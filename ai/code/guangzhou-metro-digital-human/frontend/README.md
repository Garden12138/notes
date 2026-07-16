# 广州地铁 WebUI 构建与上传

广州地铁业务界面位于 OpenAvatarChat-WebUI 的 `featrue/new_ui` 分支，包含：

- `src/views/Subway/`：地铁线路绘制和路线高亮。
- `src/views/Eating/`：美食列表。
- `src/views/VideoChat/`：`scene_dialog`、地图、美食和关闭事件处理。
- `src/data/subway.json`：前端地铁线路绘制数据。

## 获取业务分支

```bash
cd "$HOME/Documents/gitlab/OpenAvatarChat-WebUI"
git fetch origin
git switch featrue/new_ui 2>/dev/null || \
  git switch --track origin/featrue/new_ui
```

不要直接在 `develop` 分支打包，`develop` 不包含广州地铁页面。

## 移除硬编码敏感配置

当前业务分支的 `vite.config.ts` 包含硬编码后端地址，地图组件也包含硬编码地图平台凭据。发布前必须改用环境变量。

在 `vite.config.ts` 中使用：

```typescript
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const serverOrigin = env.VITE_OPENAVATAR_ORIGIN

  if (!serverOrigin) {
    throw new Error('VITE_OPENAVATAR_ORIGIN is required')
  }

  return {
    base: './',
    server: {
      host: '0.0.0.0',
      https: true,
      proxy: {
        '/download': { target: serverOrigin, changeOrigin: true, secure: false },
        '/openavatarchat': { target: serverOrigin, changeOrigin: true, secure: false },
        '/webrtc/offer': { target: serverOrigin, changeOrigin: true, secure: false },
        '/ws': {
          target: serverOrigin.replace(/^https:/, 'wss:'),
          ws: true,
          rewriteWsOrigin: true,
          secure: false,
        },
      },
    },
  }
})
```

在地图组件中使用：

```typescript
;(window as any)._AMapSecurityConfig = {
  securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
}

const AMap = await AMapLoader.load({
  key: import.meta.env.VITE_AMAP_KEY,
  version: '2.0',
  plugins: [
    'AMap.ToolBar',
    'AMap.Scale',
    'AMap.Geolocation',
    'AMap.Transfer',
    'AMap.CitySearch',
  ],
})
```

复制环境变量文件：

```bash
cp <materials-root>/frontend/.env.production.example .env.production.local
vim .env.production.local
```

`.env.production.local` 不应提交到 Git。

## 安装和构建

当前项目锁定 `pnpm 10.10.0`。本地仓库原部署说明使用 Node.js 25.2.1：

```bash
nvm install 25.2.1
nvm use 25.2.1
corepack enable
corepack prepare pnpm@10.10.0 --activate

pnpm install --frozen-lockfile
pnpm run build
```

构建成功后检查：

```bash
test -f dist/index.html
find dist/assets -maxdepth 1 -type f | grep -Eq '\.(js|css)$'
```

## 上传到 OpenAvatarChat

目标目录是 OpenAvatarChat 的 RTC Client 静态资源目录：

```text
<openavatarchat-root>/src/handlers/client/rtc_client/frontend/dist
```

使用占位符执行：

```bash
rsync -av \
  dist/ \
  <ssh-user>@<server-host>:<openavatarchat-root>/src/handlers/client/rtc_client/frontend/dist/
```

上传前应在服务器上自行备份现有 `dist`。本教程不使用 `--delete`，避免误删服务器上仍需保留的文件。

上传后清除浏览器缓存或强制刷新。不要只修改服务器上的压缩 JavaScript；后续改动必须回到本地源码仓库重新构建。
