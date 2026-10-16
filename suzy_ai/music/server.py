"""Dedicated opt-in loopback service; never changes Logic's audio graph."""
import argparse
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

from ..server import Handler
from .audio import MAX_CHUNK
from .live import Conflict, LiveSession


class LiveHandler(Handler):
    @property
    def session(self):
        return self.server.live_session

    def _dispatch(self, callback):
        def dispatch():
            try:
                callback()
            except Conflict as exc:
                self._json({'error': str(exc)}, 409)
        super()._dispatch(dispatch)

    def _get(self):
        parts = urlparse(self.path).path.strip('/').split('/')
        if parts == ['health']:
            self._json({'ok': True, 'experimental': True, 'audio_device_access': False})
        elif parts == ['v1', 'live']:
            self._json(self.session.status())
        elif len(parts) == 4 and parts[:2] == ['v1', 'live'] and parts[3] == 'audio.wav':
            wav = self.session.audio(parts[2])
            self._headers(200, 'audio/wav', len(wav))
            self.wfile.write(wav)
        else:
            self._json({'error': 'not found'}, 404)

    def _post(self):
        parts = urlparse(self.path).path.strip('/').split('/')
        if parts == ['v1', 'live', 'context', 'reset']:
            if self._body() != {}:
                raise ValueError('reset requires an empty object')
            self._json(self.session.reset_context())
        elif parts == ['v1', 'live', 'capture']:
            self._json(self.session.arm(self._body()), 201)
        elif len(parts) == 5 and parts[:2] == ['v1', 'live'] and parts[3] == 'chunks':
            self._discard_input = True
            if (self.headers.get_content_type() != 'application/octet-stream'
                    or self.headers.get('Transfer-Encoding')
                    or len(self.headers.get_all('Content-Length', [])) != 1):
                raise ValueError('PCM chunks require a single Content-Length')
            size = int(self.headers['Content-Length'])
            if not 0 < size <= MAX_CHUNK:
                raise ValueError('chunk exceeds byte limit')
            pcm = self.rfile.read(size)
            if len(pcm) != size:
                raise ValueError('incomplete chunk')
            self._discard_input = False
            self._json(self.session.append(parts[2], int(parts[4]), pcm))
        elif len(parts) == 4 and parts[:2] == ['v1', 'live']:
            if self._body() != {}:
                raise ValueError('actions require an empty JSON object')
            if parts[3] == 'finish':
                self._json(self.session.finish(parts[2]), 202)
            else:
                self._json(self.session.action(parts[2], parts[3]))
        else:
            self._json({'error': 'not found'}, 404)


def make_server(port=7333, session=None, core_url="http://127.0.0.1:7332/v1"):
    server = ThreadingHTTPServer(('127.0.0.1', port), LiveHandler)
    server.live_session = session if session is not None else LiveSession(core_url=core_url)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=7333)
    parser.add_argument('--core-url', default='http://127.0.0.1:7332/v1')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('choose a port between 1024 and 65535')
    server = make_server(args.port, core_url=args.core_url)
    print(f'Experimental live response service: http://127.0.0.1:{args.port}')
    print('No Logic capture adapter or playback device is connected. Ctrl-C stops the service.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
