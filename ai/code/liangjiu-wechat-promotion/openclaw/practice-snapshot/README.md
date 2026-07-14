# 2026-07-14 实践原貌（公开脱敏版）

本目录保留真机实践结束时的 `AGENTS.md`、`TOOLS.md` 和两个 Skills，只替换本机路径、Agent 名、群名和链接。它用于回答“当时实际怎么跑”，不建议直接部署。

审计后确认的缺口：

- 新品采集 Skill 实际是一份“移除过严标签校验”的 Proposal，不是完整执行手册；
- 主 Skill 没有写清 `products.jsonl -> selected-products.txt -> results.jsonl -> final-promotion.txt` 的转换；
- 主 Skill 含未验证的库存、尺码与发货承诺；
- 场景三、四当时只校验 UI 群名，没有读取场景一使用的群允许名单；
- 场景三 dry-run 后再次执行会面临输入框残留风险。

同级目录上一层的文件是补齐上述缺口后的部署版。四个场景脚本放在 `../../iphone-use/scripts/`；其中场景三、四已增加允许名单校验，场景三写入文案前会清空输入框。
