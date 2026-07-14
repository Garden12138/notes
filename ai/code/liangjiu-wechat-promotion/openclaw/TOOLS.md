# TOOLS.md — 良久素材本地工具

## 目录

- iphone-use 项目：`$IPHONE_USE_DIR`
- 执行脚本：`$IPHONE_USE_DIR/scripts`
- 任务产物：`$IPHONE_USE_DIR/runs/<task_id>`
- iphone-use 状态：`$HOME/.iphone-use/wechat-iphone`
- 群允许名单：`$WECHAT_IPHONE_CONFIG`

## 场景与 helper

| 文件 | 用途 |
| --- | --- |
| `wechat-iphone-scenario1-v13-names-only.sh` | WDA 状态、启动、新品名称采集 |
| `select_safe_products.py` | `products.jsonl` 到同类安全选品清单 |
| `wechat-iphone-scenario2-v13-safe-reset-list-top.sh` | 详情、价格、规格与链接提取 |
| `build_verified_promotion.py` | `results.jsonl` 到事实文案 |
| `wechat-iphone-scenario3-v6-send-button-fixed.sh` | 群名双校验、dry-run、单次发送 |
| `wechat-iphone-scenario4-v2-share-confirm-send.sh` | 从最终文案逐链接分享 |
| `iu_clipboard_relay.py` | iPhone 剪贴板到 `/agent/inbox` |

## 固定配置

- 快捷指令：`IU Clipboard Export`
- 链接读取模式：`shortcut`
- 群允许名单格式：`{"groups":["<TARGET_WECHAT_GROUP>"]}`
- 最终文案：`$RUN_DIR/final-promotion.txt`

真实群名、Team ID、UDID 和 Token 只放本地环境或配置文件，不写入 Skill。

## 实测坐标基线

2026-07-13 实测元素树为 `393 × 852`：

- `新品首发`：`x=0.105`、`y=0.805`
- 详情返回：`x=0.050`、`y=0.100`
- 场景二快捷指令超时：`25` 秒
- 分享确认发送兜底：`x=0.675`、`y=0.865`

这些值不是通用配置。新设备先运行场景一 `elements`，读取 `screen.width`、`screen.height` 和目标元素 `rect`，再设置：

```bash
export WECHAT_IPHONE_SCREEN_WIDTH="<WIDTH>"
export WECHAT_IPHONE_SCREEN_HEIGHT="<HEIGHT>"
export WECHAT_IPHONE_NEW_PRODUCTS_X="<NORMALIZED_X>"
export WECHAT_IPHONE_NEW_PRODUCTS_Y="<NORMALIZED_Y>"
```

归一化坐标按元素中心计算：`x=(left+width/2)/screen.width`，`y=(top+height/2)/screen.height`。坐标只作已知页面兜底，不能替代元素身份校验。
