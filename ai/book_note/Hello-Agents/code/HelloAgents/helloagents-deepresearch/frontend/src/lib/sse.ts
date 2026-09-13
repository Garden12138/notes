import { parseResearchEvent, type ResearchEvent } from "../types/research";

function parseFrame(frame: string): ResearchEvent | null {
  const data = frame
    .split("\n")
    .filter((line) => line === "data" || line.startsWith("data:"))
    .map((line) => (line === "data" ? "" : line.slice(5).trimStart()))
    .join("\n");
  if (!data) return null;
  return parseResearchEvent(JSON.parse(data));
}

export class ResearchSSEDecoder {
  private buffer = "";
  private trailingCarriageReturn = false;

  push(chunk: string): ResearchEvent[] {
    let normalizedChunk =
      (this.trailingCarriageReturn ? "\r" : "") + chunk;
    this.trailingCarriageReturn = normalizedChunk.endsWith("\r");
    if (this.trailingCarriageReturn) {
      normalizedChunk = normalizedChunk.slice(0, -1);
    }
    this.buffer += normalizedChunk.replace(/\r\n|\r/g, "\n");
    return this.drain(false);
  }

  finish(): ResearchEvent[] {
    if (this.trailingCarriageReturn) {
      this.buffer += "\n";
      this.trailingCarriageReturn = false;
    }
    return this.drain(true);
  }

  private drain(flushRemainder: boolean): ResearchEvent[] {
    const events: ResearchEvent[] = [];
    let boundary = this.buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const event = parseFrame(this.buffer.slice(0, boundary));
      this.buffer = this.buffer.slice(boundary + 2);
      if (event) events.push(event);
      boundary = this.buffer.indexOf("\n\n");
    }

    if (flushRemainder && this.buffer.trim()) {
      const event = parseFrame(this.buffer);
      this.buffer = "";
      if (event) events.push(event);
    }
    return events;
  }
}

export async function consumeResearchSSE(
  response: Response,
  onEvent: (event: ResearchEvent) => void,
): Promise<void> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/event-stream")) {
    throw new Error("研究服务没有返回 text/event-stream 响应");
  }
  if (!response.body) {
    throw new Error("浏览器没有提供可读取的流式响应体");
  }

  const reader = response.body.getReader();
  const textDecoder = new TextDecoder();
  const sseDecoder = new ResearchSSEDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = textDecoder.decode(value, { stream: true });
      for (const event of sseDecoder.push(text)) onEvent(event);
    }
    const finalText = textDecoder.decode();
    for (const event of sseDecoder.push(finalText)) onEvent(event);
    for (const event of sseDecoder.finish()) onEvent(event);
  } finally {
    reader.releaseLock();
  }
}
