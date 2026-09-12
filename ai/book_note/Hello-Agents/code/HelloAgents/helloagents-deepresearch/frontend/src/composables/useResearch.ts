import { computed, ref } from "vue";

import type {
  ResearchEvent,
  ResearchRequest,
  SearchAPI,
  TodoItem,
} from "../types/research";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

function errorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

async function consumeSSE(
  response: Response,
  onEvent: (event: ResearchEvent) => void,
): Promise<void> {
  if (!response.body) {
    throw new Error("浏览器没有提供可读取的流式响应体");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");

    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) {
        onEvent(JSON.parse(data) as ResearchEvent);
      }
      boundary = buffer.indexOf("\n\n");
    }

    if (done) break;
  }
}

export function useResearch() {
  const running = ref(false);
  const error = ref("");
  const events = ref<ResearchEvent[]>([]);
  const tasks = ref<TodoItem[]>([]);
  const reportMarkdown = ref("");
  let controller: AbortController | null = null;

  const progress = computed(() => {
    const value = [...events.value]
      .reverse()
      .find((event) => typeof event.progress === "number")?.progress;
    return value ?? 0;
  });

  function applyEvent(event: ResearchEvent): void {
    events.value.push(event);
    if (event.type === "tasks" && event.tasks) {
      tasks.value = event.tasks;
    } else if (event.type === "task" && event.task) {
      const index = tasks.value.findIndex((task) => task.id === event.task?.id);
      if (index >= 0) {
        tasks.value[index] = event.task;
      } else {
        tasks.value.push(event.task);
      }
    } else if (event.type === "report" && event.report_markdown) {
      reportMarkdown.value = event.report_markdown;
    } else if (event.type === "error") {
      error.value = event.message || "研究流程执行失败";
    }
  }

  async function startResearch(topic: string, searchApi?: SearchAPI): Promise<void> {
    controller?.abort();
    const currentController = new AbortController();
    controller = currentController;
    running.value = true;
    error.value = "";
    events.value = [];
    tasks.value = [];
    reportMarkdown.value = "";

    const payload: ResearchRequest = { topic: topic.trim() };
    if (searchApi) payload.search_api = searchApi;

    try {
      const response = await fetch(`${API_BASE_URL}/research/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: currentController.signal,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(errorMessage(body, `研究请求失败（HTTP ${response.status}）`));
      }
      await consumeSSE(response, applyEvent);
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      error.value = reason instanceof Error ? reason.message : "研究请求失败";
    } finally {
      if (controller === currentController) {
        controller = null;
        running.value = false;
      }
    }
  }

  function cancelResearch(): void {
    controller?.abort();
    controller = null;
    running.value = false;
  }

  return {
    cancelResearch,
    error,
    events,
    progress,
    reportMarkdown,
    running,
    startResearch,
    tasks,
  };
}

