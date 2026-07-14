# 良久素材微信推广实践快照

这是 2026-07-14 真机实践所用 OpenClaw 工作区规则与 iphone-use 场景脚本的公开脱敏版。它用于配合《使用 OpenClaw + iPhone-use + WDA 实现“良久素材”自动化微信推广》阅读，不属于 iphone-use 上游项目。

## 文件对应关系

| 公开文件 | 实践中的位置 | 作用 |
| --- | --- | --- |
| `openclaw/AGENTS.md` | 专用 OpenClaw workspace | 规定任务范围、指令优先级、授权与停止条件 |
| `openclaw/TOOLS.md` | 专用 OpenClaw workspace | 记录脚本、文案文件、快捷指令和坐标参数 |
| `openclaw/skills/liangjiu-new-products-collection-v1-0-0/SKILL.md` | workspace Skill | 规定场景一到场景二的 WDA 衔接 |
| `openclaw/skills/liangjiu-wechat-auto-promotion-v1-0-0/SKILL.md` | workspace Skill | 编排采集、详情、文案、发送和分享 |
| `iphone-use/scripts/iu_clipboard_relay.py` | iphone-use `scripts/` | 将 iPhone 快捷指令请求转发到 `/agent/inbox` |
| `iphone-use/scripts/wechat-iphone-scenario1-v13-names-only.sh` | iphone-use `scripts/` | 预检、启动与新品名称采集 |
| `iphone-use/scripts/wechat-iphone-scenario2-v13-safe-reset-list-top.sh` | iphone-use `scripts/` | 列表复位、详情提取和链接回传 |
| `iphone-use/scripts/wechat-iphone-scenario3-v6-send-button-fixed.sh` | iphone-use `scripts/` | 群名校验、文案输入和单次发送 |
| `iphone-use/scripts/wechat-iphone-scenario4-v2-share-confirm-send.sh` | iphone-use `scripts/` | 从最终文案提取链接并逐个分享 |

## 与本地实践文件的差异

公开快照保留了主要函数、CLI、状态检查、错误码和产物格式，只处理了不应发布的运行配置：

- 用户目录改为 `$IPHONE_USE_DIR` 或 `$HOME/path/to/iphone-use`；
- Apple Team ID、iPhone UDID、目标群等改为环境变量或命令参数；
- 移除场景二内嵌的六商品默认值；
- 移除场景三内嵌的历史推广文案、完整小程序链接和历史消息确认标记；
- OpenClaw 文件中的真实群名改为 `<TARGET_WECHAT_GROUP>`。

场景三和场景四默认不再带目标群；运行时必须传 `--group`、`--target-group`，或设置 `WECHAT_IPHONE_TARGET_GROUP`。场景三默认不再带文案；必须传 `--message-file`、`--message`，或设置 `WECHAT_IPHONE_DEFAULT_MESSAGE`。

主 Skill 中固定的营销收尾句原样保留，因为它确实存在于本次实践版本中。这句话可能包含详情页没有验证的库存、尺码和发货承诺，是需要修正的技术债，不应直接用于新的推广任务。

## 使用方式

先完成 iphone-use、WDA 和微信真机环境配置，再把 `iphone-use/scripts/` 中的文件放入 iphone-use 项目的 `scripts/` 目录并赋予 Shell 脚本执行权限。运行前至少设置：

```bash
export IPHONE_USE_DIR="$HOME/path/to/iphone-use"
export WECHAT_IPHONE_PROJECT_DIR="$IPHONE_USE_DIR"
export WDA_TEAM_ID="<APPLE_TEAM_ID>"
export WDA_UDID="<IPHONE_UDID>"
export WECHAT_IPHONE_TARGET_GROUP="<TARGET_WECHAT_GROUP>"
```

商品列表和最终文案通过文件传入，不依赖公开快照中的默认业务数据：

```bash
./wechat-iphone-scenario2-v13-safe-reset-list-top.sh promote-products \
  --products-file ./selected-products.txt \
  --link-read-mode shortcut

./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
  --group "$WECHAT_IPHONE_TARGET_GROUP" \
  --message-file ./scenario3-final-promotion.txt \
  --dry-run
```

正式发送和逐链接分享具有外部副作用。先核对目标群、文案和 `--dry-run` 结果，再执行正式命令；发送动作一旦可能发生，不要自动重试。
