<script setup lang="ts">
import { ref } from "vue";

import ResearchModal from "./components/ResearchModal.vue";
import { useResearch } from "./composables/useResearch";
import type { SearchAPI } from "./types/research";

const topic = ref("");
const searchApi = ref<SearchAPI>("duckduckgo");
const modalOpen = ref(false);

const {
  cancelResearch,
  error,
  events,
  progress,
  reportMarkdown,
  running,
  startResearch,
  tasks,
} = useResearch();

function submitResearch(): void {
  const normalizedTopic = topic.value.trim();
  if (normalizedTopic.length < 2 || running.value) return;
  modalOpen.value = true;
  void startResearch(normalizedTopic, searchApi.value);
}

function closeModal(): void {
  if (running.value) cancelResearch();
  modalOpen.value = false;
}
</script>

<template>
  <main class="app-shell">
    <div class="background-grid" aria-hidden="true"></div>
    <section class="intro-panel">
      <p class="eyebrow">HELLOAGENTS · CHAPTER 14</p>
      <h1>把零散搜索整理成<br />一条可追溯的研究链</h1>
      <p class="lead">
        先拆问题，再逐项检索和总结，最后合并为带来源的研究报告。
      </p>
      <div class="capability-list">
        <span>问题剖析</span>
        <span>多轮信息采集</span>
        <span>反思与总结</span>
      </div>
    </section>

    <form class="research-card" @submit.prevent="submitResearch">
      <div class="card-number">14.1</div>
      <label for="topic">研究主题</label>
      <textarea
        id="topic"
        v-model="topic"
        rows="6"
        minlength="2"
        maxlength="500"
        placeholder="例如：开源大模型推理框架的技术路线与适用场景"
        required
      ></textarea>

      <label for="search-api">搜索引擎</label>
      <select id="search-api" v-model="searchApi">
        <option value="duckduckgo">DuckDuckGo</option>
        <option value="tavily">Tavily</option>
        <option value="perplexity">Perplexity</option>
        <option value="searxng">SearXNG</option>
        <option value="advanced">Advanced（组合可用来源）</option>
      </select>

      <button class="primary-button" type="submit" :disabled="running || topic.trim().length < 2">
        {{ running ? "研究进行中" : "开始研究" }}
      </button>
      <p class="scope-note">
        已打通界面、SSE 与工具层；生产服务装配将在后续小节完成。
      </p>
    </form>

    <ResearchModal
      :open="modalOpen"
      :topic="topic.trim()"
      :running="running"
      :error="error"
      :progress="progress"
      :events="events"
      :tasks="tasks"
      :report-markdown="reportMarkdown"
      @close="closeModal"
      @cancel="cancelResearch"
    />
  </main>
</template>
