<script setup lang="ts">
import { computed } from "vue";

import type { ResearchEvent, TodoItem } from "../types/research";

const props = defineProps<{
  open: boolean;
  topic: string;
  running: boolean;
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

const completedTasks = computed(
  () => props.tasks.filter((task) => task.status === "completed").length,
);
</script>

<template>
  <div v-if="open" class="research-overlay" role="dialog" aria-modal="true">
    <section class="research-modal">
      <header class="research-header">
        <div>
          <p class="eyebrow">DEEP RESEARCH</p>
          <h2>{{ topic }}</h2>
        </div>
        <button class="icon-button" type="button" aria-label="关闭" @click="emit('close')">
          ×
        </button>
      </header>

      <div class="progress-track" aria-label="研究进度">
        <span :style="{ width: `${progress}%` }"></span>
      </div>

      <div class="research-layout">
        <aside>
          <div class="aside-heading">
            <h3>研究任务</h3>
            <span>{{ completedTasks }}/{{ tasks.length }}</span>
          </div>
          <p v-if="!tasks.length" class="muted">等待规划结果</p>
          <ol v-else class="task-list">
            <li v-for="task in tasks" :key="task.id" :data-status="task.status">
              <strong>{{ task.title }}</strong>
              <small>{{ task.status }}</small>
            </li>
          </ol>

          <h3>过程日志</h3>
          <ul class="event-list">
            <li v-for="(event, index) in events" :key="`${event.type}-${index}`">
              {{ event.message || event.type }}
            </li>
          </ul>
        </aside>

        <article class="report-panel">
          <p v-if="error" class="error-message">{{ error }}</p>
          <pre v-else-if="reportMarkdown">{{ reportMarkdown }}</pre>
          <div v-else class="waiting-state">
            <span class="pulse"></span>
            <p>{{ running ? "正在组织研究过程……" : "等待研究报告" }}</p>
          </div>
        </article>
      </div>

      <footer>
        <span>{{ running ? "研究进行中" : error ? "研究未完成" : "研究流程结束" }}</span>
        <button v-if="running" class="secondary-button" type="button" @click="emit('cancel')">
          取消研究
        </button>
      </footer>
    </section>
  </div>
</template>

