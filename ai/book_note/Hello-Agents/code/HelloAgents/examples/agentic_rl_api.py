"""Serve an accepted Agentic-RL checkpoint through a small FastAPI app."""

import argparse
from typing import Any

from hello_agents.rl import generate_math_response, load_inference_model


def create_app(model_path: str, quantization: str = "none") -> Any:
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise ImportError("启动 API 需要安装 fastapi、pydantic 和 uvicorn") from exc

    model, tokenizer = load_inference_model(model_path, quantization)
    app = FastAPI(title="Agentic-RL Math API", version="1.0.0")

    class SolveRequest(BaseModel):
        question: str = Field(min_length=1)
        max_new_tokens: int = Field(default=512, ge=1, le=2048)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "model_path": model_path}

    @app.post("/solve")
    def solve(request: SolveRequest) -> dict[str, str]:
        answer = generate_math_response(
            model,
            tokenizer,
            request.question,
            request.max_new_tokens,
        )
        return {"question": request.question, "answer": answer}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve an Agentic-RL model")
    parser.add_argument("--model-path", required=True)
    parser.add_argument(
        "--quantization", choices=("none", "8bit", "4bit"), default="none"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError("启动 API 需要安装 uvicorn") from exc
    uvicorn.run(
        create_app(args.model_path, args.quantization),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
