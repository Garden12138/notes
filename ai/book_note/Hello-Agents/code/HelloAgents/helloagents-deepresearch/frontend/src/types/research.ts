export type SearchAPI =
  | "duckduckgo"
  | "tavily"
  | "perplexity"
  | "searxng"
  | "advanced";
export type TodoStatus = "pending" | "in_progress" | "completed" | "failed";
export type ResearchPhase =
  | "planning"
  | "execution"
  | "reporting"
  | "completed"
  | "failed";

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface TodoItem {
  id: number;
  title: string;
  intent: string;
  query: string;
  status: TodoStatus;
  summary?: string | null;
  sources: SearchResult[];
  note_id?: string | null;
}

export type ResearchEventType =
  | "status"
  | "tasks"
  | "task"
  | "tool_call"
  | "report"
  | "done"
  | "error";

export interface ResearchEvent {
  type: ResearchEventType;
  phase?: ResearchPhase;
  message?: string;
  progress?: number;
  tasks?: TodoItem[];
  task?: TodoItem;
  report_markdown?: string;
  detail?: Record<string, unknown>;
}

export interface ResearchRequest {
  topic: string;
  search_api?: SearchAPI;
}

const RESEARCH_EVENT_TYPES = new Set<ResearchEventType>([
  "status",
  "tasks",
  "task",
  "tool_call",
  "report",
  "done",
  "error",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function parseResearchEvent(value: unknown): ResearchEvent {
  if (!isRecord(value) || typeof value.type !== "string") {
    throw new Error("SSE 事件缺少 type 字段");
  }
  if (!RESEARCH_EVENT_TYPES.has(value.type as ResearchEventType)) {
    throw new Error(`未知的 SSE 事件类型：${value.type}`);
  }
  if (
    value.progress !== undefined &&
    (typeof value.progress !== "number" ||
      !Number.isFinite(value.progress) ||
      value.progress < 0 ||
      value.progress > 100)
  ) {
    throw new Error("SSE 事件的 progress 必须在 0–100 之间");
  }
  if (value.type === "tasks" && !Array.isArray(value.tasks)) {
    throw new Error("tasks 事件缺少任务列表");
  }
  if (value.type === "task" && !isRecord(value.task)) {
    throw new Error("task 事件缺少任务数据");
  }
  if (value.type === "report" && typeof value.report_markdown !== "string") {
    throw new Error("report 事件缺少 Markdown 报告");
  }
  return value as unknown as ResearchEvent;
}
