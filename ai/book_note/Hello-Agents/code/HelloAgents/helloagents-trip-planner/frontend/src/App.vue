<template>
  <a-config-provider
    :theme="{
      token: {
        colorPrimary: '#176b57',
        borderRadius: 12,
        colorText: '#18332d',
      },
    }"
  >
    <a-layout class="app-layout">
      <a-layout-header class="app-header">
        <RouterLink to="/" class="brand">
          <span aria-hidden="true">✈</span>
          <span>HelloAgents 智能旅行助手</span>
        </RouterLink>
      </a-layout-header>
      <a-layout-content class="app-content">
        <RouterView />
      </a-layout-content>
      <a-layout-footer class="app-footer">
        HelloAgents · 从需求到可视化行程
      </a-layout-footer>
    </a-layout>
  </a-config-provider>
</template>

<style>
:root {
  color: #18332d;
  background: #f4f7f3;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

.app-layout {
  min-height: 100vh;
  background: #f4f7f3;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  height: 64px;
  padding: 0 clamp(20px, 5vw, 72px);
  background: rgb(20 61 52 / 94%);
  backdrop-filter: blur(14px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-size: 1rem;
  font-weight: 750;
  letter-spacing: 0.01em;
  text-decoration: none;
}

.brand:hover {
  color: #d8f3e9;
}

.app-content {
  min-height: calc(100vh - 128px);
}

.app-footer {
  color: #60736e;
  text-align: center;
  background: #edf2ef;
}

button,
input,
select,
textarea {
  font: inherit;
}
</style>
