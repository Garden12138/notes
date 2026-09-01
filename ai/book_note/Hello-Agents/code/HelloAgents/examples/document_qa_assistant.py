"""Launch the chapter 8.4 Gradio document Q&A assistant."""

from __future__ import annotations

import argparse
from functools import partial

from hello_agents import PDFLearningAssistant, create_gradio_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="智能文档问答助手")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=7860, type=int)
    parser.add_argument("--data-dir", default="./document_qa_data")
    parser.add_argument("--share", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    factory = partial(PDFLearningAssistant, data_dir=args.data_dir)
    app = create_gradio_app(factory)
    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
    )


if __name__ == "__main__":
    main()
