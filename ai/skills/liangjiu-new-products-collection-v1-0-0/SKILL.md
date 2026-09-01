---
name: liangjiu-new-products-collection-v1-0-0
description: 采集良久素材新品，过滤风险品类，选择同类商品并提取已验证的标题、价格、规格与链接。
---

# 良久素材新品采集与详情提取

在用户要求采集良久素材新品、自动安全选品或读取商品详情时使用本 Skill。只操作当前任务的运行目录，不复用历史商品或文案。

## 输入与目录

从任务上下文读取：

- `task_id`
- `source_page`，必须为 `新品首发`
- `target_count`，默认 6
- `selection_mode`，为 `auto_safe_same_category` 或用户指定品类

要求环境变量 `IPHONE_USE_DIR` 指向 iphone-use 项目。建立独立运行目录：

```bash
export RUN_DIR="$IPHONE_USE_DIR/runs/$TASK_ID"
mkdir -p "$RUN_DIR"
cd "$IPHONE_USE_DIR/scripts"
```

如果 `RUN_DIR` 已含正式发送结果，停止；不得复用该目录开始新任务。

## 1. 预检

运行：

```bash
./wechat-iphone-scenario1-v13-names-only.sh status
```

仅在下列条件全部成立时继续：

- `ready=true`
- `status.ok=true`
- `status.wda=true`
- `status.wda_actionable=true`
- `status.wda_locked=false`
- `status.drivable=true`
- `status.mode="agent"`

`controller.lock` 存在时读取其中 PID。只有 PID 已退出才能人工删除锁；PID 仍存在时返回 `PHONE_CONTROLLER_BUSY`。

## 2. 采集新品名称

运行：

```bash
./wechat-iphone-scenario1-v13-names-only.sh collect-new-products \
  --limit 50 \
  --max-scrolls 20 \
  --out-dir "$RUN_DIR/new-products"
```

要求 `summary.json` 和 `products.jsonl` 存在且 JSON 可解析。`target_reached=false` 不代表脚本失败；按 `collected_count` 使用实际候选，不把规格文本补成商品。

## 3. 选择同一安全品类

未指定品类时运行：

```bash
python3 ./select_safe_products.py \
  --input "$RUN_DIR/new-products/products.jsonl" \
  --count "$TARGET_COUNT" \
  --output "$RUN_DIR/selected-products.txt" \
  --report "$RUN_DIR/selection.json"
```

用户指定品类时增加 `--category "<CATEGORY>"`。读取 `selection.json`，向用户回显 `selected_category` 和 `selected_products`。

该 helper 会过滤规格片段、酒水、保健品、医疗器械、药品、成人用品和带医疗功效暗示的标题。若返回 `SAFE_SAME_CATEGORY_NOT_ENOUGH`，停止，不跨品类凑数。

## 4. 场景衔接

采集结束后再次运行场景一 `status`。如果状态健康，且期间没有用户接管、锁屏、弹窗或其他 UI 操作，允许用 `--skip-open` 进入场景二；不要只因无法再次看到“新品首发”标签而完整重入。

发现明确的其他页面、登录页、微信聊天页或未知弹窗时停止。完整重入只能由用户本次明确要求。

## 5. 提取详情与链接

运行：

```bash
./wechat-iphone-scenario2-v13-safe-reset-list-top.sh promote-products \
  --products-file "$RUN_DIR/selected-products.txt" \
  --link-read-mode shortcut \
  --clipboard-shortcut-name "IU Clipboard Export" \
  --shortcut-timeout 25 \
  --skip-open \
  --out-dir "$RUN_DIR/details"
```

逐行检查 `details/results.jsonl`。商品可进入下游必须同时满足：

- `ok=true`
- `detail.name` 与 `target_title` 完全一致
- `detail.price_text` 非空
- `product_link` 是完整 `#小程序://` 链接
- `link_copy.copy_action_verified=true`
- `link_copy.status="iphone_shortcut_inbox_received"`

`detail.specs` 为空时记录 `spec_missing`，不得补写规格；标题、价格和链接均已验证时允许保留该商品。

## 6. 有限补位

首批不足 `target_count` 时最多补位一轮。读取 `selection.json` 的 `selected_category`，将缺口数记为 `MISSING_COUNT`，运行：

```bash
python3 ./select_safe_products.py \
  --input "$RUN_DIR/new-products/products.jsonl" \
  --category "$SELECTED_CATEGORY" \
  --count "$MISSING_COUNT" \
  --exclude-results "$RUN_DIR/details/results.jsonl" \
  --output "$RUN_DIR/repair-products.txt" \
  --report "$RUN_DIR/repair-selection.json"

./wechat-iphone-scenario2-v13-safe-reset-list-top.sh promote-products \
  --products-file "$RUN_DIR/repair-products.txt" \
  --link-read-mode shortcut \
  --clipboard-shortcut-name "IU Clipboard Export" \
  --shortcut-timeout 25 \
  --out-dir "$RUN_DIR/details-repair"
```

补位前重新确认当前页面与 WDA 状态。第二轮仍不足时停止，不再循环恢复。

## 输出

向主 Skill 返回：

- `selected_category`
- 初选和补位商品名
- `details/results.jsonl`
- 可选的 `details-repair/results.jsonl`
- 已验证商品数
- 失败商品及错误码
- 缺失规格数

不得在本 Skill 中发送群消息或分享链接。
