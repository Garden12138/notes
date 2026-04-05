# Douyin Skills Natural-Language Examples

下面是两份本地 Douyin skills 的自然语言使用示例，便于以后直接复制、改写、投喂给代理。

---

## 1. `douyin-search-crawler` 使用示例

适合：默认搜索排序、批量抓取内容与评论、导出 JSON / CSV。

### 示例 1：抓取默认搜索前 20 条内容

请使用 `douyin-search-crawler` skill，基于真实可见浏览器和已登录的持久化 profile，在抖音搜索关键词“异宠”。
不要依赖 DOM 卡片点击找视频链接，而是从搜索请求里提取 aweme_id：
- 第一页使用 `aweme/v1/web/general/search/stream`
- 后续分页使用 `aweme/v1/web/general/search/single`

要求：
- 目标抓取 20 条内容
- 每条内容进入详情页后尽量抓最多 5 条评论
- 每条内容容错处理，单条失败不要中断整批
- 输出标准化 JSON
- 导出 `contents.csv` 和 `comments.csv`
- `comments.csv` 需要通过 `contentId` 关联回 `contents.csv`
- 保持低频、随机等待、像人一样操作

### 示例 2：做一轮默认排序的小批量验证

请使用 `douyin-search-crawler` skill，对关键词“异宠”做一次小批量验证：
- 默认搜索排序
- 先抓 5 条内容
- 每条尝试抓 3 到 5 条评论
- 输出 JSON 和两个 CSV

如果页面出现验证码、空结果异常增多、或者详情页连续超时，请自动降速或停止。

### 示例 3：做增量采集，跳过历史 awemeId

请使用 `douyin-search-crawler` skill，对关键词“异宠”做一轮新的默认搜索采集。
要求：
- 先抓搜索候选
- 用已有历史记录中的 `awemeId` 做主去重
- 已经抓过的内容不要重复进入详情页
- 只对新的 awemeId 抓详情和评论
- 输出新增内容的 JSON、`contents.csv`、`comments.csv`

---

## 2. `douyin-most-liked-crawler` 使用示例

适合：先切到“筛选 → 最多点赞”，再抓高互动内容与评论。

### 示例 1：抓取“最多点赞”前 11 条候选

请使用 `douyin-most-liked-crawler` skill，在真实可见浏览器里打开抖音搜索关键词“异宠”，并先切换到：
- 筛选
- 排序依据
- 最多点赞

要求：
- 保持固定窗口大小和稳定 viewport
- 不要硬编码点击坐标，而是动态定位 `最多点赞` 节点并点击
- 在请求层确认筛选已成功切换：
  - `is_filter_search=1`
  - `filter_selected={"sort_type":"1","publish_time":"0"}`
  - `search_source=tab_search`
- 成功后抓取 11 条内容候选
- 输出每条内容的 `awemeId`、描述、来源接口
- 保持随机等待和低频节奏

### 示例 2：抓取“最多点赞”模式下的 3 条内容 + 评论

请使用 `douyin-most-liked-crawler` skill，对关键词“异宠”执行一轮 most-liked 小样本抓取。
要求：
- 在同一个浏览器实例里完成“切换到最多点赞”与“后续采集”
- 不要切完后再开第二个浏览器实例
- 抓取 3 条 most-liked 内容
- 每条进入详情页，最多抓 5 条评论
- 输出 JSON
- 导出 `contents.csv` 和 `comments.csv`
- `comments.csv` 通过 `contentId` 关联到 `contents.csv`

### 示例 3：做“最多点赞”模式的增量采集

请使用 `douyin-most-liked-crawler` skill，对关键词“异宠”执行一轮新的 most-liked 增量采集。
要求：
- 先切换到“筛选 → 最多点赞”
- 从搜索请求中提取 aweme_id
- 用历史 `awemeId` 做主去重
- 已经抓过的内容直接跳过
- 只对新内容抓详情和评论
- 输出新增结果的 JSON、`contents.csv`、`comments.csv`
- 全程保持可见浏览器、随机等待、低频操作

### 示例 4：先验证 most-liked 状态，再决定是否继续

请使用 `douyin-most-liked-crawler` skill，先只验证关键词“异宠”的搜索页是否成功切换到“最多点赞”。
验证标准：
- 找到并点击正确的 `最多点赞` 节点
- 抓到带以下参数的请求：
  - `is_filter_search=1`
  - `filter_selected={"sort_type":"1","publish_time":"0"}`
  - `search_source=tab_search`

如果验证成功，再继续抓取 5 条内容；如果验证失败，就停止并报告失败原因。

---

## 3. 更口语的短提示模板

### 默认搜索版
- 用 `douyin-search-crawler` 抓一下“异宠”默认搜索前 20 条，带评论，导出 JSON 和两个 CSV。
- 用 `douyin-search-crawler` 做一轮异宠增量采集，按 awemeId 去重，只抓新内容。

### 最多点赞版
- 用 `douyin-most-liked-crawler` 抓一下“异宠”在“最多点赞”排序下的前 11 条候选。
- 用 `douyin-most-liked-crawler` 跑一轮异宠的 most-liked 增量采集，按 awemeId 去重，只抓新内容和评论。
- 用 `douyin-most-liked-crawler` 先确认筛选真的切到“最多点赞”，确认后再继续抓 3 条样本。

---

## 4. 推荐写法习惯

以后在自然语言里，最好明确写出这些信息：
- 用哪个 skill
- 关键词是什么
- 默认排序还是“最多点赞”
- 抓多少条
- 是否要抓评论
- 是否要导出 CSV
- 是否要做 awemeId 去重
- 是否要求低频、随机等待、可见浏览器

这样执行会更稳定，也更不容易跑偏。
