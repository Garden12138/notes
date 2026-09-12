export type SearchAPI = "duckduckgo" | "tavily" | "perplexity" | "searxng";
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
