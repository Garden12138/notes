# 场景三、四实践原貌

这里保留 2026-07-13 实际跑通发送与分享时的公开脱敏脚本：

- `scripts/wechat-iphone-scenario3-v6-send-button-fixed.sh`
- `scripts/wechat-iphone-scenario4-v2-share-confirm-send.sh`

它们已经移除真实群名、历史文案与完整链接，但未加入本次审计后的群允许名单校验；场景三也未在写入文案前清空输入框。因此只用于复盘，不用于新部署。

场景一、场景二和 Clipboard Relay 在审计中没有这两项差异，部署版继续保留其真实控制流程。新环境统一使用 `../scripts/` 中的版本。

