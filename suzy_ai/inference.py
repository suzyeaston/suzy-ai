"""Bounded, local-only OpenAI-compatible inference. No proxies or redirects."""
from __future__ import annotations

import http.client
import ipaddress
import json
import math
import os
import socket
import threading
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit


class InferenceError(Exception):
    """Safe to expose: never contains backend bodies or prompt text."""


class InferenceUnavailable(InferenceError):
    pass


class InferenceTimeout(InferenceError):
    pass


class InferenceAdapter(Protocol):
    model: str

    def complete(self, messages: list[dict[str, str]], max_tokens: int) -> str: ...


def local_endpoint(url: str) -> tuple[str, int, str]:
    try:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        # Pin localhost to a literal address; never resolve arbitrary hostnames.
        address = "127.0.0.1" if host == "localhost" else host
        if not ipaddress.ip_address(address).is_loopback:
            raise ValueError
        if (parsed.scheme != "http" or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment
                or parsed.path.rstrip("/") != "/v1"
                or any(c.isspace() for c in url)):
            raise ValueError
        port = 80 if parsed.port is None else parsed.port
        if not 1 <= port <= 65535:
            raise ValueError
        return address, port, "/v1/chat/completions"
    except ValueError:
        raise ValueError("inference URL must be http://<loopback>:<port>/v1") from None


@dataclass(frozen=True)
class LocalInference:
    base_url: str
    model: str
    timeout: float = 60.0
    max_response_bytes: int = 262_144

    def __post_init__(self) -> None:
        local_endpoint(self.base_url)
        if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 200:
            raise ValueError("configure a local model name (1–200 characters)")
        if not math.isfinite(self.timeout) or not 0 < self.timeout <= 120:
            raise ValueError("inference timeout must be between 0 and 120 seconds")
        if not 1 <= self.max_response_bytes <= 1_048_576:
            raise ValueError("invalid response byte limit")

    def complete(self, messages: list[dict[str, str]], max_tokens: int = 512) -> str:
        if type(max_tokens) is not int or not 1 <= max_tokens <= 2048:
            raise ValueError("max_tokens must be an integer from 1 to 2048")
        host, port, path = local_endpoint(self.base_url)
        body = json.dumps({"model": self.model, "messages": messages,
                           "stream": False, "max_tokens": max_tokens}).encode("utf-8")
        if len(body) > 131_072:
            raise ValueError("inference request is too large")
        connection = http.client.HTTPConnection(host, port, timeout=self.timeout)
        expired = threading.Event()
        timer = None
        started = time.monotonic()
        try:
            connection.connect()
            transport = connection.sock

            def expire() -> None:
                expired.set()
                try:
                    transport.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            # A deadline also bounds slow trickling responses (socket timeout alone
            # only limits idle time). Connecting itself has the same timeout.
            remaining = self.timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise InferenceTimeout("local model request timed out")
            timer = threading.Timer(remaining, expire)
            timer.daemon = True
            timer.start()
            # HTTPConnection deliberately ignores HTTP_PROXY/HTTPS_PROXY settings.
            connection.request("POST", path, body, {"Content-Type": "application/json"})
            response = connection.getresponse()
            if response.status != 200:
                raise InferenceUnavailable("local model server rejected the request")
            raw = response.read(self.max_response_bytes + 1)
            if len(raw) > self.max_response_bytes:
                raise InferenceError("local model response exceeded the size limit")
            try:
                payload = json.loads(raw)
                message = payload["choices"][0]["message"]
                answer = message["content"]
                if (message.get("role") != "assistant" or message.get("tool_calls")
                        or message.get("function_call") or not isinstance(answer, str)
                        or not answer.strip()):
                    raise ValueError
            except (ValueError, KeyError, IndexError, TypeError, UnicodeError, RecursionError):
                raise InferenceError("local model returned an invalid text response") from None
            if expired.is_set():
                raise InferenceTimeout("local model request timed out")
            return answer
        except InferenceError:
            if expired.is_set():
                raise InferenceTimeout("local model request timed out") from None
            raise
        except TimeoutError:
            raise InferenceTimeout("local model request timed out") from None
        except (OSError, http.client.HTTPException):
            if expired.is_set():
                raise InferenceTimeout("local model request timed out") from None
            raise InferenceUnavailable("local model server is unavailable") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()


def from_environment() -> LocalInference:
    model = os.environ.get("SUZY_AI_MODEL", "").strip()
    if not model:
        raise InferenceUnavailable("set SUZY_AI_MODEL to enable local inference")
    try:
        return LocalInference(
            os.environ.get("SUZY_AI_INFERENCE_URL", "http://127.0.0.1:11434/v1"),
            model, float(os.environ.get("SUZY_AI_INFERENCE_TIMEOUT", "60")),
        )
    except ValueError:
        raise InferenceUnavailable("invalid local inference configuration") from None
