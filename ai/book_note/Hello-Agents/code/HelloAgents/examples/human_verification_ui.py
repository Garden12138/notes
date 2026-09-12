"""Launch the optional human verification UI for generated data."""

from __future__ import annotations

import argparse

from hello_agents import HumanVerificationStore, HumanVerificationUI


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_path", help="Generated AIME JSON or JSONL path")
    parser.add_argument("--results-path")
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    store = HumanVerificationStore(args.data_path, args.results_path)
    HumanVerificationUI(store).build().launch(share=args.share)


if __name__ == "__main__":
    main()
