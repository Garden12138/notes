<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchArchitecture } from "../services/api";
import type {
  ArchitectureSnapshot,
  ExternalIntegration,
} from "../types/architecture";

const snapshot = ref<ArchitectureSnapshot | null>(null);
const loading = ref(true);
const error = ref("");

const integrations = computed<[string, ExternalIntegration][]>(() =>
  Object.entries(snapshot.value?.external_integrations ?? {}),
);

onMounted(async () => {
  try {
    snapshot.value = await fetchArchitecture();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "无法连接后端";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="page-shell">
    <header class="hero">
      <p class="eyebrow">HELLOAGENTS · CHAPTER 13</p>
      <h1>智能旅行助手</h1>
      <p class="lead">
        先确认前端、后端、Agent 与外部服务的边界，再逐步加入旅行规划能力。
      </p>
    </header>

    <p v-if="loading" class="notice">正在读取后端架构……</p>
    <p v-else-if="error" class="notice error">
      后端连接失败：{{ error }}
    </p>

    <template v-else-if="snapshot">
      <section>
        <div class="section-heading">
          <p>01</p>
          <h2>四层架构</h2>
        </div>
        <div class="card-grid">
          <article v-for="layer in snapshot.layers" :key="layer.name" class="card">
            <span>{{ layer.name }}</span>
            <h3>{{ layer.technology }}</h3>
            <ul>
              <li v-for="item in layer.responsibilities" :key="item">
                {{ item }}
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section>
        <div class="section-heading">
          <p>02</p>
          <h2>Agent 分工</h2>
        </div>
        <div class="agent-list">
          <article v-for="agent in snapshot.agents" :key="agent.name">
            <h3>{{ agent.display_name }}</h3>
            <p>{{ agent.responsibility }}</p>
            <small>输出：{{ agent.expected_outputs.join(" / ") }}</small>
          </article>
        </div>
      </section>

      <section class="split-panel">
        <div>
          <div class="section-heading">
            <p>03</p>
            <h2>数据流</h2>
          </div>
          <ol>
            <li v-for="step in snapshot.data_flow" :key="step">{{ step }}</li>
          </ol>
        </div>
        <aside>
          <p class="eyebrow">INTEGRATIONS</p>
          <div v-for="[name, item] in integrations" :key="name" class="status-row">
            <div>
              <strong>{{ name.toUpperCase() }}</strong>
              <small>{{ item.purpose }}</small>
            </div>
            <span :class="{ ready: item.configured }">
              {{ item.configured ? "已配置" : "未配置" }}
            </span>
          </div>
        </aside>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page-shell {
  width: min(1120px, calc(100% - 40px));
  margin: 0 auto;
  padding: 72px 0 96px;
}

.hero {
  max-width: 720px;
  margin-bottom: 64px;
}

.eyebrow,
.section-heading p {
  color: #de6844;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.14em;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 20px;
  color: #143d34;
  font-size: clamp(3rem, 8vw, 6.5rem);
  line-height: 0.94;
  letter-spacing: -0.055em;
}

.lead {
  color: #4d655f;
  font-size: 1.12rem;
  line-height: 1.75;
}

section {
  margin-top: 56px;
}

.section-heading {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 18px;
}

.section-heading h2 {
  font-size: 1.8rem;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.card,
.agent-list article,
.split-panel,
.notice {
  border: 1px solid #d8e0da;
  border-radius: 20px;
  background: #fff;
}

.card {
  min-height: 230px;
  padding: 22px;
}

.card > span {
  color: #79908a;
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
}

.card h3 {
  margin: 32px 0 18px;
}

ul,
ol {
  margin-bottom: 0;
  padding-left: 20px;
  color: #536a64;
  line-height: 1.8;
}

.agent-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.agent-list article {
  padding: 24px;
}

.agent-list p,
.agent-list small {
  color: #647872;
  line-height: 1.6;
}

.split-panel {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 48px;
  padding: 32px;
}

.split-panel aside {
  padding: 24px;
  border-radius: 16px;
  background: #173e35;
  color: #fff;
}

.status-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 0;
  border-bottom: 1px solid rgb(255 255 255 / 14%);
}

.status-row div {
  display: grid;
  gap: 5px;
}

.status-row small {
  color: #b9cac5;
}

.status-row > span {
  align-self: center;
  color: #ffb49e;
  white-space: nowrap;
}

.status-row > span.ready {
  color: #91dfb9;
}

.notice {
  padding: 20px 24px;
}

.notice.error {
  color: #9a2e1d;
  border-color: #e8b8ae;
}

@media (max-width: 820px) {
  .card-grid,
  .agent-list,
  .split-panel {
    grid-template-columns: 1fr;
  }

  .page-shell {
    padding-top: 44px;
  }
}
</style>

