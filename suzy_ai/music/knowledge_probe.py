"""Inspect source-backed 90s musical reference cards without a model, network or audio."""
import argparse
import json

from .era_knowledge import knowledge_brief


def main():
    parser=argparse.ArgumentParser(description="Offline music knowledge retrieval audit")
    parser.add_argument("--query", required=True,
                        help="e.g. Illmatic boom bap leave space for my R&B vocals")
    parser.add_argument("--limit",type=int,default=3)
    args=parser.parse_args()
    print(json.dumps({
        "query":args.query,
        "status":"research_only_not_model_training",
        "selected":knowledge_brief(args.query,limit=args.limit),
    },indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
