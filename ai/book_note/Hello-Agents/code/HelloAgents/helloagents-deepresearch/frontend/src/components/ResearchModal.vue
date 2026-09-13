<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  ref,
  watch,
} from "vue";

import { renderMarkdown } from "../lib/markdown";
import type { ResearchEvent, TodoItem, TodoStatus } from "../types/research";

const props = defineProps<{
  open: boolean;
  topic: string;
  running: boolean;
  cancelled: boolean;
  error: string;
  progress: number;
  events: ResearchEvent[];
  tasks: TodoItem[];
  reportMarkdown: string;
}>();

const emit = defineEmits<{
  close: [];
  cancel: [];
}>();

const dialog = ref<HTMLElement | null>(null);
const closeButton = ref<HTMLButtonElement | null>(null);
const selectedTaskId = ref<number | null>(null);
let previousFocus: HTMLElement | null = null;
let previousBodyOverflow = "";
let pageStateLocked = false;

const completedTasks = computed(
  () => props.tasks.filter((task) => task.status === "completed").length,
);
const safeProgress = computed(() =>
  Math.min(100, Math.max(0, Number.isFinite(props.progress) ? props.progress : 0)),
);
const latestEvent = computed(() => props.events[props.events.length - 1]);
const phaseText = computed(() => {
  if (props.error) return "研究失败";
  if (props.cancelled) return "研究已取消";
  const labels = {
    planning: "规划阶段",
    execution: "执行阶段",
    reporting: "报告阶段",
    completed: "研究完成",
    failed: "研究失败",
  } as const;
  const phase = latestEvent.value?.phase;
  return phase ? labels[phase] : "准备阶段";
});
const statusText = computed(() => {
  if (props.error) return "研究未完成";
  if (props.cancelled) return "研究已取消";
  if (props.running) {
    return latestEvent.value?.message || "正在准备研究任务";
  }
  return props.reportMarkdown ? "研究流程结束" : "等待研究报告";
});
const renderedReport = computed(() => renderMarkdown(props.reportMarkdown));
const selectedTask = computed(() => {
  const selected = props.tasks.find((task) => task.id === selectedTaskId.value);
  return selected || props.tasks[0] || null;
});

watch(
  () => props.tasks.map((task) => `${task.id}:${task.status}`).join("|"),
  () => {
    const activeTask = props.tasks.find((task) => task.status === "in_progress");
    if (activeTask) {
      selectedTaskId.value = activeTask.id;
    } else if (!props.tasks.some((task) => task.id === selectedTaskId.value)) {
      selectedTaskId.value = props.tasks[0]?.id ?? null;
    }
  },
  { immediate: true },
);

watch(
  () => props.open,
  async (open) => {
    if (open) {
      pageStateLocked = true;
      previousFocus =
        document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      previousBodyOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      document.addEventListener("keydown", handleKeydown);
      await nextTick();
      closeButton.value?.focus();
      return;
    }
    restorePageState();
  },
  { immediate: true },
);

onBeforeUnmount(restorePageState);

function restorePageState(): void {
  if (!pageStateLocked) return;
  document.removeEventListener("keydown", handleKeydown);
  document.body.style.overflow = previousBodyOverflow;
  previousFocus?.focus();
  previousFocus = null;
  pageStateLocked = false;
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    event.preventDefault();
    emit("close");
    return;
  }
  if (event.key !== "Tab" || !dialog.value) return;

  const focusable = Array.from(
    dialog.value.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  );
  if (!focusable.length) {
    event.preventDefault();
    dialog.value.focus();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function taskStatusLabel(status: TodoStatus): string {
  return {
    pending: "待执行",
    in_progress: "进行中",
    completed: "已完成",
    failed: "失败",
  }[status];
}

function safeExternalUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : null;
  } catch {
    return null;
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="research-overlay"
      role="presentation"
      @click.self="emit('close')"
    >
      <section
        ref="dialog"
        class="research-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="research-dialog-title"
        aria-describedby="research-dialog-status"
        tabindex="-1"
      >
        <header class="research-header">
          <div>
            <p class="eyebrow">DEEP RESEARCH</p>
            <h2 id="research-dialog-title">{{ topic }}</h2>
          </div>
          <button
            ref="closeButton"
            class="icon-button"
            type="button"
            :aria-label="running ? '关闭并取消研究' : '关闭研究面板'"
            @click="emit('close')"
          >
            ×
          </button>
        </header>

        <div class="progress-section">
          <div class="progress-copy">
            <strong>{{ phaseText }}</strong>
            <span>{{ safeProgress }}%</span>
          </div>
          <div
            class="progress-track"
            role="progressbar"
            aria-label="研究进度"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuenow="safeProgress"
          >
            <span :style="{ width: `${safeProgress}%` }"></span>
          </div>
          <p id="research-dialog-status" class="status-message" aria-live="polite">
            {{ statusText }}
          </p>
        </div>

        <div class="research-layout">
          <aside>
            <div class="aside-heading">
              <h3>研究任务</h3>
              <span>{{ completedTasks }}/{{ tasks.length }}</span>
            </div>
            <p v-if="!tasks.length" class="muted">等待规划结果</p>
            <ol v-else class="task-list">
              <li
                v-for="task in tasks"
                :key="task.id"
                :data-status="task.status"
                :data-selected="task.id === selectedTask?.id"
              >
                <button type="button" @click="selectedTaskId = task.id">
                  <strong>{{ task.title }}</strong>
                  <small>{{ taskStatusLabel(task.status) }}</small>
                </button>
              </li>
            </ol>

            <h3>过程日志</h3>
            <p v-if="!events.length" class="muted">等待服务端事件</p>
            <ol v-else class="event-list" aria-live="polite">
              <li v-for="(event, index) in events" :key="`${event.type}-${index}`">
                <span>{{ index + 1 }}</span>
                {{ event.message || event.type }}
              </li>
            </ol>
          </aside>

          <article class="report-panel">
            <p v-if="error" class="error-message" role="alert">{{ error }}</p>
            <div
              v-else-if="renderedReport"
              class="markdown-body"
              v-html="renderedReport"
            ></div>
            <section v-else-if="selectedTask" class="task-preview">
              <p class="eyebrow">CURRENT TODO</p>
              <h3>{{ selectedTask.title }}</h3>
              <p>{{ selectedTask.intent }}</p>
              <dl>
                <div>
                  <dt>搜索查询</dt>
                  <dd>{{ selectedTask.query }}</dd>
                </div>
                <div>
                  <dt>任务状态</dt>
                  <dd>{{ taskStatusLabel(selectedTask.status) }}</dd>
                </div>
              </dl>
              <div v-if="selectedTask.summary" class="task-summary">
                <h4>阶段总结</h4>
                <p>{{ selectedTask.summary }}</p>
              </div>
              <div v-if="selectedTask.sources.length" class="task-sources">
                <h4>来源</h4>
                <ol>
                  <li v-for="source in selectedTask.sources" :key="source.url">
                    <a
                      v-if="safeExternalUrl(source.url)"
                      :href="safeExternalUrl(source.url) || undefined"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {{ source.title }}
                    </a>
                    <span v-else>{{ source.title }}</span>
                    <p>{{ source.snippet }}</p>
                  </li>
                </ol>
              </div>
            </section>
            <div v-else class="waiting-state">
              <span v-if="running" class="pulse" aria-hidden="true"></span>
              <p>{{ cancelled ? "研究已取消" : "正在组织研究过程……" }}</p>
            </div>
          </article>
        </div>

        <footer>
          <span>{{ statusText }}</span>
          <button
            v-if="running"
            class="secondary-button"
            type="button"
            @click="emit('cancel')"
          >
            取消研究
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
