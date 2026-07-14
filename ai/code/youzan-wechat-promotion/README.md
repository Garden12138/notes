# 有赞商城 A 微信推广实践快照

这是 2026-07-14 单商品推广链路的公开脱敏快照。Agent 规则、三个 Skills 和 `wechat-iphone` 脚本均来自当日实际工作区；除公开所需的值替换外，执行顺序、错误处理和防重复发送规则保持不变。

完整实践文章见[使用 OpenClaw + iPhone-use + WDA 实现有赞商城 A 自动化微信推广](../../Using%20OpenClaw%20iPhone-use%20and%20WDA%20to%20automate%20Youzan%20WeChat%20promotion.md)。

## 文件

| 文件 | 作用 |
| --- | --- |
| `openclaw/AGENTS.md` | 专用 Agent 的职责、授权、状态与停止规则 |
| `openclaw/skills/youzan-product-listing-daily-goods-v1-0-0/SKILL.md` | API-first 选品、上架、卖点与 SKU 加价 |
| `openclaw/skills/youzan-product-promotion-v1-0-0/SKILL.md` | 精确筛选商品并生成、校验推广链接 |
| `openclaw/skills/youzan-wechat-auto-promotion/SKILL.md` | 串联上架、链接、文案和微信发送 |
| `iphone-use/scripts/wechat-iphone` | iPhone 状态、WDA 启停、群聊校验、草稿检查和单次发送 |
| `iphone-use/config/allowed-groups.json.example` | 群聊允许名单示例 |

## 脱敏范围

| 原始值类型 | 公开值 |
| --- | --- |
| 本机 iphone-use 目录 | `$HOME/path/to/iphone-use` |
| Apple Team ID | `<APPLE_TEAM_ID>` |
| iPhone UDID | `<IPHONE_UDID>` |
| 商品示例 | `<PRODUCT_KEYWORD>`、`<FULL_PRODUCT_NAME>` |
| 群聊配置 | 仅保留 `<TARGET_WECHAT_GROUP>` 示例 |

真实 Token、群名、商品、链接、聊天内容和运行证据没有复制到本目录。脚本仍从 `$HOME/.iphone-use/agent-token` 读取本机 Token，仓库不保存 Token 值。

## 部署位置

将 Agent 文件和 Skills 放入专用 OpenClaw workspace，将脚本与 allowlist 放入同一 `wechat-iphone` Skill：

```text
$OPENCLAW_WORKSPACE/
├── AGENTS.md
└── skills/
    ├── youzan-product-listing-daily-goods-v1-0-0/SKILL.md
    ├── youzan-product-promotion-v1-0-0/SKILL.md
    ├── youzan-wechat-auto-promotion/SKILL.md
    └── wechat-iphone/
        ├── config/allowed-groups.json
        └── scripts/wechat-iphone
```

运行前配置本机值：

```bash
export WECHAT_IPHONE_PROJECT_DIR="$HOME/path/to/iphone-use"
export WDA_TEAM_ID="<APPLE_TEAM_ID>"
export WDA_UDID="<IPHONE_UDID>"
export WECHAT_IPHONE_CONFIG="$OPENCLAW_WORKSPACE/skills/wechat-iphone/config/allowed-groups.json"
```

脚本原始发送结果使用 `group_still_open`。OpenClaw 最终报告可将它映射为 `group_verified`，并在任务层补充 `task_id` 和 `evidence_dir`。
