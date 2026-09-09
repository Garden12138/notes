FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY server.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PORT=8081

EXPOSE 8081

CMD ["python", "server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8081"]
