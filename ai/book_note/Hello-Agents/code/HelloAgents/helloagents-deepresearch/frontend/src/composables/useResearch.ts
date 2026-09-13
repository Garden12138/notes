import { computed, ref } from "vue";

import { consumeResearchSSE } from "../lib/sse";
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
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (!item || typeof item !== "object" || !("msg" in item)) return "";
          const message = (item as { msg?: unknown }).msg;
          return typeof message === "string" ? message : "";
        })
        .filter(Boolean);
      if (messages.length) return messages.join("；");
    }
  }
  return fallback;
}

function requestFailureMessage(reason: unknown): string {
  if (
    reason instanceof TypeError &&
    /fetch|network|load/i.test(reason.message)
  ) {
    return "无法连接研究服务，请确认后端已经启动";
  }
  return reason instanceof Error ? reason.message : "研究请求失败";
}

export function useResearch() {
  const running = ref(false);
  const cancelled = ref(false);
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
    const normalizedTopic = topic.trim();
    if (normalizedTopic.length < 2) {
      error.value = "研究主题至少需要两个字符";
      return;
    }

    controller?.abort();
    const currentController = new AbortController();
    controller = currentController;
    running.value = true;
    cancelled.value = false;
    error.value = "";
    events.value = [];
    tasks.value = [];
    reportMarkdown.value = "";

    const payload: ResearchRequest = { topic: normalizedTopic };
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
      let terminalEventReceived = false;
      await consumeResearchSSE(response, (event) => {
        if (controller !== currentController) return;
        applyEvent(event);
        if (event.type === "done" || event.type === "error") {
          terminalEventReceived = true;
        }
      });
      if (!terminalEventReceived) {
        throw new Error("研究连接在完成事件前结束");
      }
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      error.value = requestFailureMessage(reason);
    } finally {
      if (controller === currentController) {
        controller = null;
        running.value = false;
      }
    }
  }

  function cancelResearch(): void {
    if (!controller) return;
    cancelled.value = true;
    controller?.abort();
    controller = null;
    running.value = false;
  }

  return {
    cancelResearch,
    cancelled,
    error,
    events,
    progress,
    reportMarkdown,
    running,
    startResearch,
    tasks,
  };
}
