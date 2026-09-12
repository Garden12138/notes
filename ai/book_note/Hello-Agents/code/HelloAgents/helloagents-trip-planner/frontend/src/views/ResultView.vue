<script setup lang="ts">
import { message } from "ant-design-vue";
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from "vue";
import { useRouter } from "vue-router";

import { loadTripPlan } from "../services/trip-storage";
import type { MealType, TripPlan } from "../types/trip";

interface AMapInstance {
  add(overlays: unknown): void;
  destroy(): void;
  setFitView(overlays?: unknown): void;
}

const router = useRouter();
const tripPlan = ref<TripPlan | null>(null);
const mapContainer = ref<HTMLElement | null>(null);
const exportContent = ref<HTMLElement | null>(null);
const mapStatus = ref("");
const activeDays = ref<string[]>(["0"]);
const failedImages = ref<Record<string, boolean>>({});
const exporting = ref(false);
let map: AMapInstance | null = null;

const allAttractions = computed(() =>
  (tripPlan.value?.days ?? []).flatMap((day) =>
    day.attractions.map((attraction, index) => ({
      attraction,
      markerLabel: `${day.day_index + 1}.${index + 1}`,
    })),
  ),
);

const tripDays = computed(() => tripPlan.value?.days.length ?? 0);
const attractionCount = computed(() => allAttractions.value.length);

function imageKey(dayIndex: number, attractionIndex: number): string {
  return `${dayIndex}-${attractionIndex}`;
}

function markImageFailed(key: string): void {
  failedImages.value = { ...failedImages.value, [key]: true };
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    maximumFractionDigits: 0,
  }).format(value);
}

function mealLabel(type: MealType): string {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "小吃",
  }[type];
}

function weatherIcon(weather: string): string {
  if (weather.includes("雨")) return "🌧";
  if (weather.includes("雪")) return "🌨";
  if (weather.includes("阴")) return "☁";
  if (weather.includes("云")) return "⛅";
  return "☀";
}

async function initializeMap(): Promise<void> {
  await nextTick();
  if (!tripPlan.value || !mapContainer.value) {
    return;
  }

  const points = allAttractions.value.filter(
    ({ attraction }) =>
      Number.isFinite(attraction.location.longitude) &&
      Number.isFinite(attraction.location.latitude),
  );
  if (!points.length) {
    mapStatus.value = "行程中没有可用于地图展示的坐标";
    return;
  }

  const webKey = import.meta.env.VITE_AMAP_WEB_KEY?.trim();
  if (!webKey) {
    mapStatus.value = "未配置 VITE_AMAP_WEB_KEY，行程内容仍可正常查看";
    return;
  }

  mapStatus.value = "地图加载中……";
  try {
    const { default: AMapLoader } = await import(
      "@amap/amap-jsapi-loader"
    );
    const AMap = await AMapLoader.load({
      key: webKey,
      version: "2.0",
    });
    map?.destroy();
    map = new AMap.Map(mapContainer.value, {
      zoom: 12,
      center: [
        points[0].attraction.location.longitude,
        points[0].attraction.location.latitude,
      ],
      viewMode: "2D",
    }) as AMapInstance;

    const markers = points.map(
      ({ attraction, markerLabel }) =>
        new AMap.Marker({
          position: [
            attraction.location.longitude,
            attraction.location.latitude,
          ],
          title: attraction.name,
          label: {
            content: markerLabel,
            direction: "top",
          },
        }),
    );
    map.add(markers);
    map.setFitView(markers);
    mapStatus.value = "";
  } catch (reason) {
    mapStatus.value =
      reason instanceof Error ? reason.message : "高德地图加载失败";
  }
}

function safeFileName(city: string): string {
  return (city.trim() || "旅行").replace(/[\\/:*?"<>|]/g, "_");
}

async function capturePlan(): Promise<HTMLCanvasElement> {
  if (!exportContent.value) {
    throw new Error("没有可导出的行程内容");
  }
  const { default: html2canvas } = await import("html2canvas");
  return html2canvas(exportContent.value, {
    backgroundColor: "#f4f7f3",
    scale: Math.min(2, window.devicePixelRatio || 1),
    useCORS: true,
    logging: false,
  });
}

async function exportAsImage(): Promise<void> {
  if (!tripPlan.value || exporting.value) return;
  exporting.value = true;
  try {
    const canvas = await capturePlan();
    const link = document.createElement("a");
    link.download = `${safeFileName(tripPlan.value.city)}旅行计划.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
    message.success("旅行计划图片已生成");
  } catch (reason) {
    message.error(reason instanceof Error ? reason.message : "图片导出失败");
  } finally {
    exporting.value = false;
  }
}

async function exportAsPDF(): Promise<void> {
  if (!tripPlan.value || exporting.value) return;
  exporting.value = true;
  try {
    const canvas = await capturePlan();
    const { jsPDF } = await import("jspdf");
    const imageData = canvas.toDataURL("image/png");
    const pdf = new jsPDF("p", "mm", "a4");
    const margin = 8;
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const imageWidth = pageWidth - margin * 2;
    const imageHeight = (canvas.height * imageWidth) / canvas.width;
    const printableHeight = pageHeight - margin * 2;
    let renderedHeight = 0;

    pdf.addImage(
      imageData,
      "PNG",
      margin,
      margin,
      imageWidth,
      imageHeight,
      undefined,
      "FAST",
    );
    renderedHeight += printableHeight;
    while (renderedHeight < imageHeight) {
      pdf.addPage();
      pdf.addImage(
        imageData,
        "PNG",
        margin,
        margin - renderedHeight,
        imageWidth,
        imageHeight,
        undefined,
        "FAST",
      );
      renderedHeight += printableHeight;
    }
    pdf.save(`${safeFileName(tripPlan.value.city)}旅行计划.pdf`);
    message.success("旅行计划 PDF 已生成");
  } catch (reason) {
    message.error(reason instanceof Error ? reason.message : "PDF 导出失败");
  } finally {
    exporting.value = false;
  }
}

function goHome(): void {
  void router.push({ name: "home" });
}

onMounted(async () => {
  tripPlan.value = loadTripPlan();
  if (tripPlan.value) {
    await initializeMap();
  }
});

onBeforeUnmount(() => {
  map?.destroy();
  map = null;
});
</script>

<template>
  <main class="result-page">
    <header class="result-toolbar">
      <div>
        <p class="eyebrow">YOUR TRIP PLAN</p>
        <h1>{{ tripPlan ? `${tripPlan.city}旅行计划` : "旅行计划" }}</h1>
      </div>
      <a-space wrap>
        <a-button @click="goHome">返回首页</a-button>
        <a-dropdown v-if="tripPlan">
          <a-button type="primary" :loading="exporting">导出行程</a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="image" @click="exportAsImage">
                导出为图片
              </a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">
                导出为 PDF
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-space>
    </header>

    <a-empty
      v-if="!tripPlan"
      class="empty-state"
      description="没有可展示的旅行计划，请先从首页生成"
    >
      <a-button type="primary" @click="goHome">创建旅行计划</a-button>
    </a-empty>

    <div v-else ref="exportContent" class="plan-content">
      <section class="overview-grid">
        <a-card class="overview-card" :bordered="false">
          <p class="card-kicker">行程概览</p>
          <h2>{{ tripPlan.city }}</h2>
          <p class="date-range">
            {{ tripPlan.start_date }} — {{ tripPlan.end_date }}
          </p>
          <p class="suggestion">{{ tripPlan.overall_suggestions }}</p>
          <div class="summary-stats">
            <div><strong>{{ tripDays }}</strong><span>天</span></div>
            <div><strong>{{ attractionCount }}</strong><span>个景点</span></div>
            <div>
              <strong>{{ tripPlan.weather_info.length }}</strong><span>天天气</span>
            </div>
          </div>
        </a-card>

        <a-card
          v-if="tripPlan.budget"
          class="budget-card"
          :bordered="false"
        >
          <p class="card-kicker">预算明细</p>
          <div class="budget-list">
            <div>
              <span>景点门票</span>
              <strong>{{ formatCurrency(tripPlan.budget.total_attractions) }}</strong>
            </div>
            <div>
              <span>酒店住宿</span>
              <strong>{{ formatCurrency(tripPlan.budget.total_hotels) }}</strong>
            </div>
            <div>
              <span>餐饮费用</span>
              <strong>{{ formatCurrency(tripPlan.budget.total_meals) }}</strong>
            </div>
            <div>
              <span>交通费用</span>
              <strong>{{ formatCurrency(tripPlan.budget.total_transportation) }}</strong>
            </div>
          </div>
          <div class="budget-total">
            <span>预估总费用</span>
            <strong>{{ formatCurrency(tripPlan.budget.total) }}</strong>
          </div>
        </a-card>
      </section>

      <section class="map-section">
        <header class="content-heading">
          <div>
            <p class="card-kicker">地点关系</p>
            <h2>景点地图</h2>
          </div>
          <span>{{ attractionCount }} 个坐标点</span>
        </header>
        <div ref="mapContainer" class="map-container">
          <div v-if="mapStatus" class="map-message">{{ mapStatus }}</div>
        </div>
      </section>

      <section class="days-section">
        <header class="content-heading">
          <div>
            <p class="card-kicker">逐日安排</p>
            <h2>每日行程</h2>
          </div>
        </header>

        <a-collapse v-model:activeKey="activeDays" class="day-collapse">
          <a-collapse-panel
            v-for="day in tripPlan.days"
            :key="String(day.day_index)"
          >
            <template #header>
              <div class="day-header">
                <strong>第 {{ day.day_index + 1 }} 天</strong>
                <span>{{ day.date }}</span>
                <small>{{ day.description }}</small>
              </div>
            </template>

            <div class="day-meta">
              <span>交通：{{ day.transportation }}</span>
              <span>住宿：{{ day.accommodation }}</span>
            </div>

            <h3 class="subheading">景点安排</h3>
            <div class="attraction-grid">
              <article
                v-for="(attraction, index) in day.attractions"
                :key="`${attraction.poi_id || attraction.name}-${index}`"
                class="attraction-card"
              >
                <div class="image-frame">
                  <img
                    v-if="
                      attraction.image_url &&
                      !failedImages[imageKey(day.day_index, index)]
                    "
                    :src="attraction.image_url"
                    :alt="attraction.name"
                    crossorigin="anonymous"
                    @error="markImageFailed(imageKey(day.day_index, index))"
                  />
                  <div v-else class="image-placeholder">暂无图片</div>
                  <span>{{ day.day_index + 1 }}.{{ index + 1 }}</span>
                </div>
                <div class="attraction-body">
                  <div class="attraction-title">
                    <h4>{{ attraction.name }}</h4>
                    <a-tag v-if="attraction.rating !== null" color="gold">
                      {{ attraction.rating }} 分
                    </a-tag>
                  </div>
                  <p>{{ attraction.description }}</p>
                  <dl>
                    <div><dt>地址</dt><dd>{{ attraction.address }}</dd></div>
                    <div>
                      <dt>游览</dt><dd>{{ attraction.visit_duration }} 分钟</dd>
                    </div>
                    <div>
                      <dt>门票</dt><dd>{{ formatCurrency(attraction.ticket_price) }}</dd>
                    </div>
                  </dl>
                </div>
              </article>
            </div>

            <div class="day-detail-grid">
              <article v-if="day.hotel" class="detail-card hotel-card">
                <p class="card-kicker">住宿</p>
                <h3>{{ day.hotel.name }}</h3>
                <p>{{ day.hotel.address || "地址待确认" }}</p>
                <dl>
                  <div><dt>类型</dt><dd>{{ day.hotel.type || day.accommodation }}</dd></div>
                  <div><dt>价格</dt><dd>{{ day.hotel.price_range || formatCurrency(day.hotel.estimated_cost) }}</dd></div>
                  <div><dt>评分</dt><dd>{{ day.hotel.rating || "暂无" }}</dd></div>
                </dl>
              </article>

              <article class="detail-card meal-card">
                <p class="card-kicker">餐饮</p>
                <ul>
                  <li v-for="meal in day.meals" :key="`${meal.type}-${meal.name}`">
                    <div>
                      <strong>{{ mealLabel(meal.type) }} · {{ meal.name }}</strong>
                      <small>{{ meal.description || meal.address || "信息待确认" }}</small>
                    </div>
                    <span>{{ formatCurrency(meal.estimated_cost) }}</span>
                  </li>
                </ul>
              </article>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </section>

      <section v-if="tripPlan.weather_info.length" class="weather-section">
        <header class="content-heading">
          <div>
            <p class="card-kicker">出行参考</p>
            <h2>天气信息</h2>
          </div>
        </header>
        <div class="weather-grid">
          <article v-for="weather in tripPlan.weather_info" :key="weather.date">
            <span class="weather-icon">{{ weatherIcon(weather.day_weather) }}</span>
            <div>
              <strong>{{ weather.date }}</strong>
              <p>
                白天 {{ weather.day_weather }} {{ weather.day_temp }}℃ ·
                夜间 {{ weather.night_weather }} {{ weather.night_temp }}℃
              </p>
              <small>{{ weather.wind_direction }} {{ weather.wind_power }}</small>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.result-page {
  width: min(1280px, calc(100% - 32px));
  margin: 0 auto;
  padding: 42px 0 88px;
}

.result-toolbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 28px;
}

.result-toolbar h1,
.content-heading h2,
.overview-card h2,
.day-header,
p {
  margin-top: 0;
}

.result-toolbar h1 {
  margin-bottom: 0;
  color: #143d34;
  font-size: clamp(2.1rem, 5vw, 4.2rem);
  line-height: 1;
  letter-spacing: -0.045em;
}

.eyebrow,
.card-kicker {
  margin-bottom: 7px;
  color: #c44f2d;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

.empty-state {
  margin-top: 90px;
  padding: 52px;
  border: 1px solid #dae4df;
  border-radius: 20px;
  background: #fff;
}

.plan-content {
  display: grid;
  gap: 22px;
  padding: 2px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 22px;
}

.overview-card,
.budget-card,
.map-section,
.days-section,
.weather-section {
  border: 1px solid #dae4df;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 16px 48px rgb(20 61 52 / 6%);
}

.overview-card :deep(.ant-card-body),
.budget-card :deep(.ant-card-body) {
  padding: 28px;
}

.overview-card h2 {
  margin-bottom: 4px;
  font-size: 2rem;
}

.date-range {
  color: #5e746d;
  font-variant-numeric: tabular-nums;
}

.suggestion {
  max-width: 760px;
  margin: 22px 0;
  color: #49615a;
  line-height: 1.75;
}

.summary-stats {
  display: flex;
  gap: 12px;
}

.summary-stats div {
  min-width: 90px;
  padding: 12px;
  border-radius: 12px;
  background: #eef5f2;
}

.summary-stats strong,
.summary-stats span {
  display: block;
}

.summary-stats strong {
  color: #176b57;
  font-size: 1.35rem;
}

.summary-stats span {
  color: #71827d;
  font-size: 0.8rem;
}

.budget-list {
  display: grid;
  gap: 11px;
}

.budget-list > div,
.budget-total {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.budget-list span {
  color: #657a74;
}

.budget-total {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid #dce5e1;
}

.budget-total strong {
  color: #c44f2d;
  font-size: 1.35rem;
}

.map-section,
.days-section,
.weather-section {
  overflow: hidden;
  padding: 28px;
}

.content-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.content-heading h2 {
  margin-bottom: 0;
  font-size: 1.55rem;
}

.content-heading > span {
  color: #71827d;
}

.map-container {
  position: relative;
  min-height: 390px;
  overflow: hidden;
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgb(23 107 87 / 8%), rgb(196 79 45 / 8%)),
    repeating-linear-gradient(
      45deg,
      transparent,
      transparent 18px,
      rgb(255 255 255 / 55%) 18px,
      rgb(255 255 255 / 55%) 36px
    );
}

.map-message {
  position: absolute;
  inset: 50% auto auto 50%;
  z-index: 2;
  width: min(420px, calc(100% - 32px));
  padding: 15px 18px;
  transform: translate(-50%, -50%);
  border: 1px solid #ccd9d4;
  border-radius: 12px;
  background: rgb(255 255 255 / 92%);
  color: #49615a;
  text-align: center;
}

.day-collapse {
  border: 0;
  background: transparent;
}

.day-collapse :deep(.ant-collapse-item) {
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid #dae4df;
  border-radius: 14px !important;
  background: #fbfcfb;
}

.day-collapse :deep(.ant-collapse-content) {
  border-top-color: #e2e9e6;
}

.day-header {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: baseline;
  gap: 12px;
  width: 100%;
}

.day-header strong {
  color: #176b57;
}

.day-header span,
.day-header small {
  color: #6d817b;
}

.day-header small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.day-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin: 4px 0 22px;
}

.day-meta span {
  padding: 7px 10px;
  border-radius: 8px;
  background: #edf4f1;
  color: #526963;
  font-size: 0.86rem;
}

.subheading {
  margin: 0 0 14px;
  font-size: 1rem;
}

.attraction-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.attraction-card {
  overflow: hidden;
  border: 1px solid #dce5e1;
  border-radius: 14px;
  background: #fff;
}

.image-frame {
  position: relative;
  height: 190px;
  background: #e7eeeb;
}

.image-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: #84948f;
  background: linear-gradient(135deg, #e7efec, #f3e9e5);
}

.image-frame > span {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 5px 8px;
  border-radius: 7px;
  background: #143d34;
  color: #fff;
  font-size: 0.78rem;
  font-weight: 750;
}

.attraction-body {
  padding: 18px;
}

.attraction-title {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
}

.attraction-title h4 {
  margin: 0;
  font-size: 1.1rem;
}

.attraction-body > p {
  min-height: 48px;
  margin: 10px 0 14px;
  color: #5d716b;
  line-height: 1.6;
}

dl {
  display: grid;
  gap: 7px;
  margin: 0;
}

dl > div {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 10px;
}

dt {
  color: #81918c;
}

dd {
  margin: 0;
  color: #3f5750;
}

.day-detail-grid {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 14px;
  margin-top: 14px;
}

.detail-card {
  padding: 19px;
  border-radius: 14px;
}

.hotel-card {
  background: #edf5f2;
}

.detail-card h3 {
  margin: 0 0 8px;
}

.detail-card > p:not(.card-kicker) {
  color: #60736e;
}

.meal-card {
  background: #f8f0ed;
}

.meal-card ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.meal-card li {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 9px;
  border-bottom: 1px solid rgb(196 79 45 / 13%);
}

.meal-card li:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.meal-card li div {
  display: grid;
  gap: 2px;
}

.meal-card small {
  color: #7e6d67;
}

.weather-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.weather-grid article {
  display: flex;
  gap: 13px;
  padding: 17px;
  border: 1px solid #dce5e1;
  border-radius: 13px;
  background: #fbfcfb;
}

.weather-icon {
  font-size: 1.9rem;
}

.weather-grid p {
  margin: 5px 0;
  color: #526963;
  line-height: 1.5;
}

.weather-grid small {
  color: #7b8d87;
}

@media (max-width: 900px) {
  .overview-grid,
  .day-detail-grid {
    grid-template-columns: 1fr;
  }

  .weather-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .result-toolbar {
    align-items: start;
    flex-direction: column;
  }

  .attraction-grid,
  .weather-grid {
    grid-template-columns: 1fr;
  }

  .day-header {
    grid-template-columns: 1fr;
    gap: 3px;
  }

  .day-header small {
    white-space: normal;
  }

  .map-section,
  .days-section,
  .weather-section {
    padding: 18px;
  }
}
</style>
