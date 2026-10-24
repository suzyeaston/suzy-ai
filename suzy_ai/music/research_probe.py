"""Inspect user-researched, cited music cards locally without calling Qwen."""
import argparse
import json

from .research_cards import research_brief


def main():
    parser = argparse.ArgumentParser(description="Auditable offline deep-research card retrieval")
    parser.add_argument("--query", required=True, help="e.g. Cash Crop Vancouver space for vocals")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()
    selected = research_brief(args.query, limit=args.limit)
    print(json.dumps({
        "query": args.query,
        "retrieval": "source_attributed_public_research",
        "weights_updated": False,
        "model_called": False,
        "cards": selected,
        "important": "Proposed musical actions are original experiments, not album transcriptions.",
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
