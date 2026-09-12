<script setup lang="ts">
import dayjs, { type Dayjs } from "dayjs";
import { message } from "ant-design-vue";
import { onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { getApiErrorMessage } from "../services/api";
import { createTripPlan } from "../services/trip";
import { saveTripPlan } from "../services/trip-storage";
import type { TripRequest } from "../types/trip";

type TripFormState = Omit<TripRequest, "start_date" | "end_date"> & {
  start_date: string | null;
  end_date: string | null;
};

const router = useRouter();
const loading = ref(false);
const loadingProgress = ref(0);
const loadingStatus = ref("");
let progressTimer: ReturnType<typeof window.setInterval> | undefined;

const formData = reactive<TripFormState>({
  city: "",
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: "公共交通",
  accommodation: "经济型酒店",
  preferences: ["历史文化"],
  free_text_input: "",
});

const preferenceOptions = [
  { label: "🏛️ 历史文化", value: "历史文化" },
  { label: "🏞️ 自然风光", value: "自然风光" },
  { label: "🍜 美食", value: "美食" },
  { label: "🎨 艺术", value: "艺术" },
  { label: "🛍️ 购物", value: "购物" },
  { label: "☕ 休闲", value: "休闲" },
];

watch(
  [() => formData.start_date, () => formData.end_date],
  ([startDate, endDate]) => {
    if (!startDate || !endDate) {
      formData.travel_days = 1;
      return;
    }
    const days = dayjs(endDate).diff(dayjs(startDate), "day") + 1;
    if (days < 1) {
      message.warning("结束日期不能早于开始日期");
      formData.end_date = null;
      return;
    }
    if (days > 30) {
      message.warning("旅行天数不能超过 30 天");
      formData.end_date = null;
      return;
    }
    formData.travel_days = days;
  },
);

function disabledStartDate(current: Dayjs): boolean {
  return current.endOf("day").isBefore(dayjs().startOf("day"));
}

function disabledEndDate(current: Dayjs): boolean {
  if (disabledStartDate(current)) {
    return true;
  }
  if (!formData.start_date) {
    return false;
  }
  const start = dayjs(formData.start_date).startOf("day");
  return current.isBefore(start) || current.isAfter(start.add(29, "day"));
}

function clearProgressTimer(): void {
  if (progressTimer !== undefined) {
    window.clearInterval(progressTimer);
    progressTimer = undefined;
  }
}

function startProgress(): void {
  loadingProgress.value = 8;
  loadingStatus.value = "正在初始化旅行规划任务……";
  progressTimer = window.setInterval(() => {
    loadingProgress.value = Math.min(90, loadingProgress.value + 7);
    const progress = loadingProgress.value;
    if (progress <= 30) {
      loadingStatus.value = "正在搜索景点……";
    } else if (progress <= 52) {
      loadingStatus.value = "正在查询天气……";
    } else if (progress <= 72) {
      loadingStatus.value = "正在整理酒店信息……";
    } else {
      loadingStatus.value = "正在生成并校验行程……";
    }
  }, 700);
}

async function handleSubmit(): Promise<void> {
  if (!formData.start_date || !formData.end_date) {
    message.error("请选择完整的旅行日期");
    return;
  }

  const request: TripRequest = {
    city: formData.city.trim(),
    start_date: formData.start_date,
    end_date: formData.end_date,
    travel_days: formData.travel_days,
    transportation: formData.transportation,
    accommodation: formData.accommodation,
    preferences: [...(formData.preferences ?? [])],
    free_text_input: formData.free_text_input?.trim() ?? "",
  };

  loading.value = true;
  startProgress();
  try {
    const response = await createTripPlan(request);
    if (!response.success || !response.data) {
      throw new Error(response.message || "后端没有返回旅行计划");
    }
    loadingProgress.value = 100;
    loadingStatus.value = "旅行计划已生成";
    saveTripPlan(response.data);
    message.success(response.message || "旅行计划生成成功");
    await router.push({ name: "result" });
  } catch (reason) {
    message.error(getApiErrorMessage(reason, "生成旅行计划失败"));
  } finally {
    clearProgressTimer();
    loading.value = false;
  }
}

onBeforeUnmount(clearProgressTimer);
</script>

<template>
  <main class="home-page">
    <section class="hero-panel">
      <p class="eyebrow">HELLOAGENTS · TRIP PLANNER</p>
      <h1>把旅行需求整理成<br />一份可执行的行程</h1>
      <p class="hero-copy">
        填写目的地、日期和偏好。后端将依次查询景点、天气和酒店，再生成统一的旅行计划。
      </p>
      <div class="workflow-hint" aria-label="规划步骤">
        <span>景点</span><i>→</i><span>天气</span><i>→</i><span>酒店</span><i>→</i><span>行程</span>
      </div>
    </section>

    <a-card class="form-card" :bordered="false">
      <a-form :model="formData" layout="vertical" @finish="handleSubmit">
        <section class="form-section">
          <header class="section-heading">
            <span>01</span>
            <div>
              <h2>目的地与日期</h2>
              <p>日期范围会自动换算为旅行天数，最长 30 天。</p>
            </div>
          </header>

          <a-row :gutter="[20, 8]">
            <a-col :xs="24" :md="10">
              <a-form-item
                label="目的地城市"
                name="city"
                :rules="[{ required: true, whitespace: true, message: '请输入目的地城市' }]"
              >
                <a-input
                  v-model:value="formData.city"
                  size="large"
                  placeholder="例如：北京"
                  :maxlength="40"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="5">
              <a-form-item
                label="开始日期"
                name="start_date"
                :rules="[{ required: true, message: '请选择开始日期' }]"
              >
                <a-date-picker
                  v-model:value="formData.start_date"
                  value-format="YYYY-MM-DD"
                  size="large"
                  class="full-width"
                  :disabled-date="disabledStartDate"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="5">
              <a-form-item
                label="结束日期"
                name="end_date"
                :rules="[{ required: true, message: '请选择结束日期' }]"
              >
                <a-date-picker
                  v-model:value="formData.end_date"
                  value-format="YYYY-MM-DD"
                  size="large"
                  class="full-width"
                  :disabled-date="disabledEndDate"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="4">
              <a-form-item label="旅行天数">
                <div class="day-counter">
                  <strong>{{ formData.travel_days }}</strong><span>天</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </section>

        <section class="form-section">
          <header class="section-heading">
            <span>02</span>
            <div>
              <h2>出行偏好</h2>
              <p>这些信息会进入四个 Agent 的协作上下文。</p>
            </div>
          </header>

          <a-row :gutter="[20, 8]">
            <a-col :xs="24" :md="12">
              <a-form-item label="交通方式" name="transportation">
                <a-select v-model:value="formData.transportation" size="large">
                  <a-select-option value="公共交通">公共交通</a-select-option>
                  <a-select-option value="自驾">自驾</a-select-option>
                  <a-select-option value="步行">步行</a-select-option>
                  <a-select-option value="混合">混合交通</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="住宿偏好" name="accommodation">
                <a-select v-model:value="formData.accommodation" size="large">
                  <a-select-option value="经济型酒店">经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">豪华酒店</a-select-option>
                  <a-select-option value="民宿">民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="旅行偏好" name="preferences">
            <a-checkbox-group
              v-model:value="formData.preferences"
              :options="preferenceOptions"
              class="preference-list"
            />
          </a-form-item>

          <a-form-item label="额外要求" name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              :rows="4"
              :maxlength="500"
              show-count
              placeholder="例如：希望多安排博物馆、需要无障碍设施、饮食过敏信息……"
            />
          </a-form-item>
        </section>

        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="loading"
          class="submit-button"
        >
          {{ loading ? "正在规划" : "开始规划" }}
        </a-button>

        <div v-if="loading" class="progress-panel" aria-live="polite">
          <a-progress
            :percent="loadingProgress"
            :show-info="true"
            status="active"
            stroke-color="#176b57"
          />
          <p>{{ loadingStatus }}</p>
          <small>进度用于反馈等待状态，不代表后端任务的实时百分比。</small>
        </div>
      </a-form>
    </a-card>
  </main>
</template>

<style scoped>
.home-page {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 64px 0 88px;
}

.hero-panel {
  position: relative;
  max-width: 850px;
  margin-bottom: 38px;
}

.hero-panel::after {
  position: absolute;
  top: -26px;
  right: -180px;
  width: 290px;
  height: 290px;
  border-radius: 50%;
  background: radial-gradient(circle, rgb(222 104 68 / 18%), transparent 68%);
  content: "";
  pointer-events: none;
}

.eyebrow {
  margin-bottom: 18px;
  color: #c44f2d;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 22px;
  color: #143d34;
  font-size: clamp(2.8rem, 7vw, 5.8rem);
  line-height: 1.02;
  letter-spacing: -0.055em;
}

.hero-copy {
  max-width: 680px;
  color: #526963;
  font-size: 1.08rem;
  line-height: 1.8;
}

.workflow-hint {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 24px;
  color: #60736e;
}

.workflow-hint span {
  padding: 7px 12px;
  border: 1px solid #cddbd5;
  border-radius: 999px;
  background: #fff;
  font-size: 0.86rem;
  font-weight: 650;
}

.workflow-hint i {
  color: #c44f2d;
  font-style: normal;
}

.form-card {
  overflow: hidden;
  border: 1px solid #dce5e1;
  border-radius: 24px;
  box-shadow: 0 24px 70px rgb(23 62 53 / 10%);
}

.form-card :deep(.ant-card-body) {
  padding: clamp(22px, 4vw, 44px);
}

.form-section {
  margin-bottom: 34px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4ebe8;
}

.section-heading {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.section-heading > span {
  color: #c44f2d;
  font-family: ui-monospace, monospace;
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 2;
}

.section-heading h2 {
  margin-bottom: 4px;
  font-size: 1.35rem;
}

.section-heading p {
  margin-bottom: 0;
  color: #71827d;
}

.full-width {
  width: 100%;
}

.day-counter {
  display: flex;
  align-items: baseline;
  justify-content: center;
  height: 40px;
  border-radius: 10px;
  background: #e7f1ed;
  color: #176b57;
}

.day-counter strong {
  margin-right: 4px;
  font-size: 1.45rem;
}

.preference-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.preference-list :deep(.ant-checkbox-wrapper) {
  margin-inline-start: 0;
  padding: 11px 13px;
  border: 1px solid #dce5e1;
  border-radius: 10px;
  background: #fbfcfb;
}

.submit-button {
  height: 54px;
  border-radius: 14px;
  font-size: 1rem;
  font-weight: 700;
}

.progress-panel {
  margin-top: 20px;
  padding: 20px;
  border-radius: 14px;
  background: #f1f6f4;
  text-align: center;
}

.progress-panel p {
  margin: 10px 0 4px;
  color: #285e50;
  font-weight: 650;
}

.progress-panel small {
  color: #7a8c87;
}

@media (max-width: 700px) {
  .home-page {
    padding-top: 42px;
  }

  .hero-panel::after {
    display: none;
  }

  .preference-list {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
