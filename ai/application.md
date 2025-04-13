> 介绍点
* 是什么
* 怎么用
* 优点
* 缺点
* 推荐指数
* 使用模型

> 一键自动生成PPT
  * deepseek + kimi（https://kimi.moonshot.cn/）+ gamma（https://gamma.app/）
  * deepseek输入所需ppt内容提示语，如：请给我输出一份未来国产AI发展展望的大纲和细节，我要用来做PPT，注意要以markdown的格式输出
  * kimi输入deepseek生成的大纲，先自动丰富内容，再生成ppt
  * 如果kimi模板效果很差，可使用gamma输入kimi自动丰富内容，再生成ppt。当gamma也支持直接输入ppt内容提示语生成。
  * 参考https://zhuanlan.zhihu.com/p/25014190693

> 一键自动生成短视频
  * deepseek + 可灵（https://klingai.kuaishou.com/） + 剪映
  * deepseek输入视频制作提示语，如：
    ```
    小米su7 ultra是一辆2025年新出的车，颜色是黄色的，你可以联网搜索下小米su7 ultra的造型，根据你现在对小米SU7 Ultra的理解，我想一个“小米su7 ultra新车广告”的10秒短视频，最多只能分4个时间段，请输出包含以下内容的分镜表格：
    1. 时间轴（精确到秒）  
    2. 画面描述（包含场景、汽车展示）  
    3. 对应AI绘画提示词（可灵AI图片创意描述）  
    4. 背景音乐风格建议
    ```
  * 根据deepseek生成的分镜表格，使用可灵文生图功能生成多张图片。
  * 使用生成的多张图片在可灵图生视频功能生成视频。
  * 导入剪映：一键成片、AI字幕、智能配音。
  * 参考https://deepseek.csdn.net/67ab1a2d79aaf67875cb91d8.html

> todo
* 经测试目前硅基流动(siliconflow)提供的deepSeek api 服务比较稳定，注册即送2000万Tokens https://account.siliconflow.cn/zh/login?redirect=https%3A%2F%2Fcloud.siliconflow.cn&invitation=foufCerk
* 火山方舟：每个模型注册即送50万tokens https://www.volcengine.com/experience/ark?utm_term=202502dsinvite&ac=DSASUQY5&rc=IJSE43PZ
* https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/README_cn.md
https://huggingface.co/spaces | Spaces - Hugging Face
https://chat.deepseek.com/a/chat/s/f605396e-322a-4c58-a2dc-d5e39f1f5bfa | DeepSeek - 探索未至之境
https://github.com/songquanpeng/one-api | songquanpeng/one-api: LLM API 管理 & 分发系统，支持 OpenAI、Azure、Anthropic Claude、Google Gemini、DeepSeek、字节豆包、ChatGLM、文心一言、讯飞星火、通义千问、360 智脑、腾讯混元等主流模型，统一 API 适配，可用于 key 管理与二次分发。单可执行文件，提供 Docker 镜像，一键部署，开箱即用。LLM API management & key redistribution system, unifying multiple providers under a single API. Single binary, Docker-ready, with an English UI.
http://localhost:3000/channel | One API
https://bailian.console.aliyun.com/?productCode=p_efm#/model-telemetry | 阿里云百炼
https://platform.openai.com/settings/organization/api-keys | API keys - OpenAI API
https://platform.deepseek.com/usage | DeepSeek 开放平台
https://kimi.moonshot.cn/chat/cv6po6bfj2j29buifdsg | ```markdown # 未来国产AI发展展望 --- - Kimi.ai
https://gamma.app/create | Gamma
https://klingai.kuaishou.com/image-to-video/multi-id/273510352143112 | 可灵 AI - 新一代 AI 创意生产力平台
https://chatdoc.com/chatdoc/#/chat/40a83620-37e4-4338-9fc9-eceebd47a797 | ChatDOC - AI Chat with PDF Documents
https://github.com/aws-samples/swift-chat/blob/main/README_CN.md | swift-chat/README_CN.md at main · aws-samples/swift-chat
https://chat.4everland.org/ | 4EVERChat - 4EVERLAND AI Playground
https://dashboard.4everland.org/ai-rpc/key/autoGen/9db3bb7c-c976-42b5-b441-3ba7dca76e41 | autoGen - AI RPC - 4EVERLAND
https://github.com/wangrongding/wechat-bot/blob/main/README.md | wechat-bot/README.md at main · wangrongding/wechat-bot
https://github.com/quantalogic/quantalogic/blob/main/README_CN.md | quantalogic/README_CN.md at main · quantalogic/quantalogic
https://github.com/CherryHQ/cherry-studio?tab=readme-ov-file | CherryHQ/cherry-studio: 🍒 Cherry Studio is a desktop client that supports for multiple LLM providers. Support deepseek-r1
https://www.raycast.com/store | Raycast - Store
https://bobtranslate.com/ | Bob
https://stranslate.zggsong.com/docs/ | STranslate | 使用说明
https://github.com/petercat-ai/petercat/blob/main/README.md | petercat/README.md at main · petercat-ai/petercat
https://github.com/zhayujie/chatgpt-on-wechat | zhayujie/chatgpt-on-wechat: 基于大模型搭建的聊天机器人，同时支持 微信公众号、企业微信应用、飞书、钉钉 等接入，可选择GPT3.5/GPT-4o/GPT-o1/ DeepSeek/Claude/文心一言/讯飞星火/通义千问/ Gemini/GLM-4/Claude/Kimi/LinkAI，能处理文本、语音和图片，访问操作系统和互联网，支持基于自有知识库进行定制企业智能客服。
https://github.com/agentuniverse-ai/agentUniverse?tab=readme-ov-file | agentuniverse-ai/agentUniverse: agentUniverse is a LLM multi-agent framework that allows developers to easily build multi-agent applications.
https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/docs/dbgpt/README_cn.md | awesome-deepseek-integration/docs/dbgpt/README_cn.md at main · deepseek-ai/awesome-deepseek-integration
https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/docs/ragflow/README_cn.md | awesome-deepseek-integration/docs/ragflow/README_cn.md at main · deepseek-ai/awesome-deepseek-integration
https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/docs/autoflow/README_cn.md | awesome-deepseek-integration/docs/autoflow/README_cn.md at main · deepseek-ai/awesome-deepseek-integration
https://github.com/zilliztech/deep-searcher | zilliztech/deep-searcher: Open Source Deep Research Alternative to Reason and Search on Private Data. Written in Python.
https://github.com/OpenSPG/KAG/blob/master/README_cn.md | KAG/README_cn.md at master · OpenSPG/KAG
https://github.com/mind-network/mind-sdk-deepseek-rust | mind-network/mind-sdk-deepseek-rust: Mind Network Rust SDK DeepSeek
https://github.com/sendaifun/solana-agent-kit | sendaifun/solana-agent-kit: connect any ai agents to solana protocols
https://github.com/DataEval/dingo/blob/main/README_zh-CN.md | dingo/README_zh-CN.md at main · DataEval/dingo
https://github.com/RockChinQ/LangBot | RockChinQ/LangBot: 😎丰富生态、🧩支持扩展、🦄多模态 - 大模型原生即时通信机器人平台 | 适配 QQ / 微信（企业微信、个人微信）/ 飞书 / 钉钉 / Discord / Telegram 等消息平台 | 支持 ChatGPT、DeepSeek、Dify、Claude、Gemini、xAI Grok、Ollama、LM Studio、阿里云百炼、火山方舟、SiliconFlow、Qwen、Moonshot、ChatGLM、SillyTraven 等 LLM 的机器人 / Agent | LLM-based instant messaging bots platform, supports Discord, Telegram, WeChat, Lark, DingTalk, QQ
https://github.com/Soulter/AstrBot/ | Soulter/AstrBot: ✨ 易上手的多平台 LLM 聊天机器人及开发框架 ✨ 平台支持 QQ、QQ频道、Telegram、微信、企微、飞书 | OpenAI、DeepSeek、Gemini、硅基流动、月之暗面、Ollama、OneAPI、Dify 等。附带 WebUI。
https://www.bukenghezi.com/ | 不坑盒子
https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/docs/cline/README.md | awesome-deepseek-integration/docs/cline/README.md at main · deepseek-ai/awesome-deepseek-integration
https://neovim.io/ | Home - Neovim
https://www.cursor.com/ja | Cursor - The AI Code Editor
https://codeium.com/windsurf | Windsurf Editor by Codeium
https://github.com/djcopley/ShellOracle/ | djcopley/ShellOracle: A terminal utility for intelligent shell command generation
https://github.com/AIDC-AI/ComfyUI-Copilot | AIDC-AI/ComfyUI-Copilot: An AI-powered custom node for ComfyUI designed to enhance workflow automation and provide intelligent assistance
https://github.com/deepseek-ai/awesome-deepseek-integration/blob/main/README_cn.md | awesome-deepseek-integration/README_cn.md at main · deepseek-ai/awesome-deepseek-integration

AI写作工具
✅豆包（火山写作），豆包可智能生成工作报告、方案策划及商业文案，通过深度思考功能优化专业写作，支持多轮搜索与框架生成，提升职场效率。
活动策划内容生成 -> https://www.doubao.com/chat/2322909353459714
广告创意文案 -> https://www.doubao.com/chat/2910562500974850
优点：免费，智能，专业，可作为职场写作的起草或框架。
缺点：客户端广告多。
推荐指数：★★★★

✅Kimi，可自动生成PPT框架，支持办公室文档等写作功能。
办公室写作助手 -> https://kimi.moonshot.cn/chat/cvjsfkeqvl78v7dj7r0g
ds(请给我输出一份Desigual服装品牌介绍的大纲和细节，我要用来做PPT，注意要以markdown的格式输出) -> PPT助手 -> https://kimi.moonshot.cn/chat/cvt4jc76rtpb6c2kkmbg
优点：写作速度快，内容自动丰富，效果佳。
缺点：PPT模板固定、颜值一般。
推荐指数：★★★★

AI图像工具
✅通义万相，可快速生成设计素材和营销视觉内容，提升职场创作效率。
文字生成图片 -> https://tongyi.aliyun.com/wanxiang/creation
文字生成视频 -> https://tongyi.aliyun.com/wanxiang/videoCreation
图片生成视频 -> https://tongyi.aliyun.com/wanxiang/videoCreation
优点：生成速度快，内容丰富真实，可快速制作视觉素材。
缺点：功能比较单一。
推荐指数：★★★★★

✅可灵AI，支持通过DeepSeek优化提示词，生成多种营销视觉素材，提升创作效率。
文字生成图片 -> https://app.klingai.com/cn/text-to-image/new
文字生成视频 -> https://app.klingai.com/cn/text-to-video/new
图片生成视频 -> https://app.klingai.com/cn/image-to-video/frame-mode/new
文字生成音频 -> https://app.klingai.com/cn/text-to-audio/new
图片合成 -> https://app.klingai.com/cn/try-on/model/new
配音音频 -> https://app.klingai.com/cn/video-to-lip/new
优点：功能丰富，支持参考图，已集成deepseek，可快速生成提示词，方便制作视觉素材；产品使用体验好，可快速上手。
缺点：视频生成速度慢。
推荐指数：★★★★★

✅万相营造，支持AI生成商业设计图和营销素材，智能优化视觉内容，提升商品营销效率。
https://detail.tmall.com/item.htm?abbucket=13&detail_redpacket_pop=true&id=581209981328&ltk2=1744522639646iclhigc76387v0wrn9iia&ns=1&pisk=g5IrEYtFAHfbkkAJritE7U2wRNKJdHP_4MOBK9XHFQAkN9vHYsfQeQ63w6Sei9Q7eeN-LYIV_Di7wzBnYHt315Z_fT3JvHV15w-LIbp6pbqBtUYD2pT8G-GbfTBJ9d_vrrrsT8jbDv0Ht6xDod9HxLmkrx22LdRHxQYniqvMiHxHr0q0md9otXxHK-oDepJHt40onnvHdXxHx6X03pdDKHxnaNdHZmJ9rJ_a2J60NR8JsTAqxcD9UUqhU2iIAiJyz66kgK9f0L8y_E3_0XjNITj9LMei8B5dr_9ATlP2jNCVYFxUYmK5QZfyuaPE0EQcBMYVk5uOB9XO-ESEZ81Giw5HHZFE8C7hFNIXlv0DrNC5SESbamdGotWBuZeKPB_9K6LOA5nJZ9XOXNta4fpPoO-V4ZlpnZLFvaln8Uvv3Cw43LaB9Uaf8Xs-J2LckKR_F8gKJUf93Cw4323podp218w5.&priceTId=2147800817445226064077568e1859&query=%E9%A9%AC%E7%88%B9%E5%88%A9&skuId=5937518291412&spm=a21n57.1.hoverItem.2&utparam=%7B%22aplus_abtest%22%3A%220aa0fc3456ba32844fa6f6875ca6cee9%22%7D&xxc=taobaoSearch
商品图 -> https://www.wanxiang.art/image/goods?id=5178385
解说视频 -> https://www.wanxiang.art/video/meditorMix/history?
优点：功能丰富，能够快速生成商品营销设计图和营销广告视频，支持淘宝、天猫链接智能生成。
缺点：无
推荐指数：★★★★★

icongen https://www.icongen.io/

hitems https://zaohaowu.com/

✅tripo ai，可将图像快速转为3D模型，适用于游戏、影视设计，AI驱动高效生成
3d模型制作 -> https://www.tripo3d.ai/app/my
优点：生成效果精美，支持多种风格，可快速制作3D模型。
缺点：价格高。
推荐指数：★★★★★

webshop https://www.weshop.com/
羚珑 https://ling.jd.com/

AI视频工具
通义万相
可灵AI
即创 https://aic.oceanengine.com/
Humva https://humva.ai/avatar/home 
noisee ai https://noisee.com.cn/#/

opusclip（https://www.opus.pro/），可自动将长视频剪辑为短视频，支持字幕添加、布局优化及多平台发布，提升传播效率。

descript（https://www.descript.com/）AI驱动的视频/音频编辑工具，支持文本转录、语音克隆及多人协作，提升制作效率。

蝉镜 https://www.chanjing.cc/

AI办公工具
apippt https://www.aippt.cn/

✅Gamma，快速生成专业PPT/文档，支持智能排版与编辑。
PPT内容导入生成 ->https://gamma.app/docs/Desigual-08pr9e3p762yvfs?mode=doc
优点：生成方式灵活，支持多种主题模版，颜值高，可灵活编辑调整。
缺点：价格贵。
推荐指数：★★★★★

kimi https://kimi.moonshot.cn/
wps https://ai.wps.cn/

✅wps灵犀，可快速生成PPT和各类文档，支持智能排版与wps编辑。
AI写作 -> https://lingxi.wps.cn/creative
AIPPT -> https://lingxi.wps.cn/ppt
AI文书 -> https://lingxi.wps.cn/official
AI搜索 -> https://lingxi.wps.cn/search
AI阅读 -> https://lingxi.wps.cn/read
优点：目前内测免费，功能丰富，支持写作、PPT、文书、搜索、阅读等多种场景，生成速度快且内容质量高，可进入wps编辑，文档分析准确。
缺点：数据分析时无法生成直观图表。
推荐指数：★★★★★

通义智文（https://tongyi.aliyun.com/）

processon（https://www.processon.com/）

xmindai https://xmind.ai/
通义听悟 https://tingwu.aliyun.com/
飞书多维表格 https://www.feishu.cn/
Raycast AI https://www.raycast.com/
Hoarder https://hoarder.app/
qimi https://qimi.com/
glif https://glif.app/
通义晓蜜 https://tongyi.aliyun.com/xiaomi
钉钉个人版 https://workspace.dingtalk.com/ 

✅钉钉闪记，可实时语音转文字
https://alidocs.dingtalk.com/i/p/Y7kmbokZp3pgGLq2/docs/lDZEN6or0dp8Z4dl316qVaPYQK91xzy3 
优点：钉钉会议无缝衔接，语音转文字实时，可快速记录会议内容。
缺点：无
推荐指数：★★★★★

AI设计工具
Recraft AI https://www.recraft.ai/
墨刀 https://modao.cc/feature/ai.html

AI对话工具
✅DeepSeek，是一个高效的模型，适用于对话和内容生成等通用应用。
深度思考对话 -> https://chat.deepseek.com/
优点：对话内容生成质量高，生成的内容涵盖广泛。
缺点：官网对话使用容易奔溃，无法持续使用。
推荐指数：★★★★★

chatgpt https://www.chatgpt.com/
通义千问 https://tongyi.aliyun.com/qianwen/

✅Qwen Chat，基于开源的Open Web UI，能同时支持开源和闭源的Qwen模型
文本、图像、视频、音频多种对话：https://chat.qwen.ai/
优点：支持当前最新、效果最佳的Qwen模型，支持多模态对话。
缺点：无
推荐指数：★★★★★

豆包 https://www.doubao.com/
kimi https://kimi.moonshot.cn/
通义星尘 https://tongyi.aliyun.com/xingchen/

✅Grok，是xAI基于大型语言模型开发的生成式人工智能聊天机器人，它能够实时回答用户的问题，并利用X社交媒体平台的数据进行回应。
深度思考对话 -> https://grok.com/
优点：支持结合全球性的社交媒体数据进行回答，可快速回答用户各种问题。
缺点：对话内容可能存在敏感。
推荐指数：★★★★★

claude https://claude.ai/
gemini https://gemini.google.com/
huggingchat https://huggingface.co/chat/
koko ai https://www.seeles.ai/

AI编程工具
trae https://www.trae.com.cn/

✅cursor https://www.cursor.com/

windsurf https://codeium.com/windsurf

✅github copilot https://github.com/features/copilot

通义灵码 https://lingma.aliyun.com/lingma

junie https://www.jetbrains.com/junie/
jetbrains ai https://www.jetbrains.com/ai/

✅codium ai https://www.qodo.ai/

✅tabby https://www.tabbyml.com/

✅fitten code https://code.fittentech.com/

✅deco https://ling-deco.jd.com/

httpie ai https://httpie.io/ai
hocoos https://hocoos.com/

✅heycli https://www.heycli.com/

✅javaAI https://www.feisuanyz.com/home

AI搜索引擎
心流 https://iflow.cn/
devv https://devv.ai/
phind https://www.phind.com/
xanswer https://www.xanswer.com

AI音频工具
通义听唔 https://tingwu.aliyun.com/

✅Suno，支持文本输入创作多风格的音乐及歌词，提供音质优化。
create -> https://suno.com/create
优点：能够快速生成质量非常高的音乐。
缺点：无
推荐指数：★★★★★

minimax audio https://www.minimax.io/

AI开发平台/框架
✅dify，是一款开源的大语言模型（LLM）应用开发平台。它融合了后端即服务（Backend as Service）和LLMOps 的理念，使开发者可以快速搭建生产级的生成式AI 应用，它支持多种大型语言模型。
应该开发：https://cloud.dify.ai/apps
优点：可本地化部署，低代码开发，可视化构建AI应用，支持多模型集成，开源灵活，社区资源丰富。
缺点：需基础编程知识，学习门槛中高，依赖第三方模型，性能受接口限制。
推荐指数：★★★★★

coze（https://www.coze.cn/）

chatdev https://chatdev.modelbest.cn
langchain https://python.langchain.com/docs/introduction/
文心智能体平台 https://agents.baidu.com/
pytorch https://pytorch.org/
mlx https://ml-explore.github.io/mlx/build/html/index.html
numpy https://numpy.org/
dl4j https://deeplearning4j.konduit.ai/
jax https://docs.jax.dev/en/latest/
nltk https://www.nltk.org/

AI训练模型
魔塔社区 https://www.modelscope.cn/home
huggingface https://huggingface.co/

✅ollama，是一个开源的大型语言模型服务工具，可快速在本地运行大模型，通过简单的安装指令轻松启动和运行开源的大型语言模型。
https://ollama.com/
优点：本地部署LLM框架，支持多模型运行，隐私安全性高。
缺点：需较高配置，模型加载耗资源，调试复杂。
推荐指数：★★★★★

✅cherry studio，是一款功能强大的国产开源AI工具，支持本地部署、知识库管理、多模型聚合和联网搜索等特性。
https://cherry-ai.com/
优点：AI生成3D/视频内容高效，模板丰富，协作便捷。
缺点：输出依赖外部模型，高清渲染成本高，版权限制多。
推荐指数：★★★★★

✅chatbot，是一款AI客户端应用和智能助手，支持众多先进的AI模型和API。
https://chatboxai.app/
优点：快速搭建对话流，支持多平台接入，成本低。
缺点：复杂逻辑处理弱，依赖训练数据质量，定制性有限。
推荐指数：★★★★★

jan https://jan.ai/
anythingllm https://anythingllm.com/

AI法律助手
✅通义法睿，拥有法律领域理解和推理能力，能够基于自然语言与人对话、回答法律问题、推送裁判类案、辅助案情分析、生成法律文书、检索法律知识。 通过问题理解，正确引用法规和案例进行问题回答。 根据案情描述，自动总结法律诉求并撰写法律文书。 提供法律法规、类案检索，自带法律法规和裁判案例库。
法律咨询：https://tongyi.aliyun.com/farui/chat
法律检索：https://tongyi.aliyun.com/farui/search
合同检索：https://tongyi.aliyun.com/farui/review
优点：法律条文解析精准，合同审查自动化，合规风险预警。
缺点：仅限法律垂直领域，需专业术语输入，更新延迟。
推荐指数：★★★★★

AI提示指令（学习参考）
langgpt https://github.com/langgptai/LangGPT

✅ai short，一款专为提升工作和学习效率设计的AI 指令管理工具。
https://www.aishort.top/
优点：聚合主流AI快捷指令，一键调用，节省提示词设计时间。
缺点：场景适配僵化，无法深度定制，高阶功能缺失。
推荐指数：★★★★★

✅snack prompt，一个采用的Prompts诱导填空式的社区，它提供了一种简单的prompt修改方式，你只需要输入关键信息，就可以将他人的优秀用例转换成自己想生成的内容。
https://snackprompt.com/
优点：提供结构化提示模板，新手友好，支持多模型适配。
缺点：复杂任务覆盖不足，创意性输出有限，依赖模板更新。
推荐指数：★★★★★

提示工程指南 https://www.promptingguide.ai/zh

AI模型评测
openllmleaderboard https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/

AI学习网站
阿里云AI学习路线 https://developer.aliyun.com/learning/roadmap/ai

模型任务分类
多模态：
Audio-Text-to-Text -> 音频+文本 to 文本 -> Qwen/Qwen2-Audio-7B-Instruct
Image-Text-to-Text -> 图像+文本 to 文本 -> Qwen/Qwen2.5-VL-32B-Instruct
Video-Text-to-Text -> 视频+文本 to 文本 -> llava-hf/LLaVA-NeXT-Video-7B-hf
Visual Question Answering -> 视觉问答（图像/视频 + 文本 to 文本）-> DAMO-NLP-SG/VideoLLaMA3-7B 
Document Question Answering -> 文档问答（文档（本质上也是文本）+文本 to 文本）-> naver-clova-ix/donut-base-finetuned-docvqa
Visual Document Retrieval -> 视觉文档检索（图像 + 文档（本） -> 文档（本）） -> vidore/colpali-v1.2
Any-to-Any -> 任意模态（文本/图像/视频/音频）+任意模态（文本/图像/视频/音频） -> Qwen/Qwen2.5-Omni-7B
视觉：
Depth Estimation -> 深度估计 -> depth-anything/Depth-Anything-V2-Small-hf
Image Classification -> 图像分类（图像 -> 文本（类别）） -> nvidia/MambaVision-L3-512-21K
Zero-Shot Image Classification -> 零样本图像分类（图像 -> 文本（未知类别））-> google/siglip2-so400m-patch14-384
Object Detection -> 实体检测（图像 -> 文本（类别 + 位置）） -> lewiswatson/yolov8x-tuned-hand-gestures
Zero-Shot Object Detection -> 零样本实体检测（图像 -> 文本（未知类别 + 位置）） -> jameslahm/yoloe-v8l-seg
Image Segmentation -> 图像分割（图像 -> 图像（分割）） -> briaai/RMBG-2.0
Text-to-Image -> 文本转图像（文本 -> 图像） -> Shakker-Labs/AWPortraitCN2
Image-to-Text -> 图像转文本（图像 -> 文本） -> Salesforce/blip-image-captioning-base
Image-to-Image -> 图像转图像（图像 -> 图像）->fotographerai/zenctrl_tools
Image-to-Video -> 图像转视频（图像 -> 视频） -> Wan-AI/Wan2.1-I2V-14B-720P
Text-to-Video -> 文本转视频（文本 -> 视频） -> Wan-AI/Wan2.1-T2V-14B
Text-to-3D -> 文本转三维（文本 -> 三维） -> JeffreyXiang/TRELLIS-text-xlarge
Image-to-3D -> 图像转三维（图像 -> 三维） -> JeffreyXiang/TRELLIS-image-large
Unconditional Image Generation -> 无条件图像生成（文本 -> 图像（随机）） -> qualcomm/Stable-Diffusion-v2.1
Video Classification -> 视频分类（视频 -> 文本（类别）） -> MCG-NJU/videomae-base-finetuned-kinetics
Mask Generation -> 掩模生成（图像 -> 掩模（二值淹模，其中掩模值为1代表目标区域，0代表背景区域）） ->  ->Xenova/sam-vit-base
Image Feature Extraction -> 图像特征提取（代表图片内容的特征） -> MahmoodLab/UNI2-h
Keypoint Detection -> 关键点检测（检测图片中物体的显著特征并赋予语义） -> magic-leap-community/superpoint
自然语言处理：
Text Classification -> 文本分类（句子、段落以及文档等文本数据自动分配到一个或多个预定类别中） -> BAAI/bge-reranker-v2-m3 
Zero-Shot Classification -> 零样本分类（句子、段落以及文档等文本数据配推断未知类别） -> knowledgator/comprehend_it-base
Token Classification -> 令牌分类（文本中字符、单词以及子句自动分配到一个或多个预定类别中） -> iiiorg/piiranha-v1-detect-personal-information
Table Question Answering -> 表格问答（表格 + 文本（问题）-> 文本（答案）） -> microsoft/tapex-large-finetuned-wtq
Question Answering -> 问答（文本 + 数据源（文本、表格、知识库以及互联网文档）） -> distilbert/distilbert-base-cased-distilled-squad
Translation -> 翻译（文本（语言） -> 文本（另一语言）） -> ModelSpace/GemmaX2-28-9B-v0.1
Summarization -> 摘要总结（文本 -> 文本（摘要）） -> facebook/bart-large-cnn
Feature Extraction -> 特征提取（文本 -> 向量特征） -> BAAI/bge-large-zh-v1.5
Text Generation -> 文本生成（对话） -> Qwen/QwQ-32B deepseek-ai/DeepSeek-R1 deepseek-ai/DeepSeek-V3-0324
Text2Text Generation -> 文本到文本生成（翻译、文本摘要、问答生成、文本修复） -> teapotai/teapotllm
Fill Mask -> 填充掩码（文本（掩码）-> 文本（填充）） -> answerdotai/ModernBERT-base
Sentence Similarity -> 句子相似度 -> sentence-transformers/all-MiniLM-L6-v2
Text Ranking -> 文本排序（一组文本根据相关性排序） -> sentence-transformers/all-MiniLM-L6-v2
音频：
Text-to-Speech -> 文本转语音（文本 -> 语音） -> hexgrad/Kokoro-82M
Text-to-Audio -> 文本转音频（文本 -> 音频） -> stabilityai/stable-audio-open-1.0
Audio-to-Audio -> 音频转音频（音频 -> 音频） -> HKUSTAudio/xcodec2
Automatic Speech Recognition -> 自动语音识别（语言 -> 文本） -> openai/whisper-large-v3
Audio Classification -> 音频分类 -> speechbrain/lang-id-voxlingua107-ecapa
Voice Activity Detection -> 语音活动检测（检测人声，区分静音/噪音） -> pyannote/segmentation-3.0
表格：
Tabular Classification -> 表格分类 -> Prior-Labs/TabPFN-v2-clf
Tabular Regression -> 表格回归（基于表格预测连续值） -> Prior-Labs/TabPFN-v2-reg
Time Series Forecasting -> 时间序列预测（基于历史数据预测未来值） -> amazon/chronos-t5-small
强化学习：
Reinforcemen Learning -> 强化学习（学习最优测策略） -> ValueFX9507/Tifa-DeepsexV2-7b-MGRPO-GGUF-Q8
Robotics -> 机器人学 -> Robotics
其他：
Graph Machine Learning -> 图机器学习（处理图数据） ->  -> ibm-research/materials.pos-egnn

uv sync --all-packages -i https://mirrors.aliyun.com/pypi/simple/ --frozen \
--extra "base" \
--extra "proxy_openai" \
--extra "hf" \
--extra "llama_cpp" \
--extra "rag" \
--extra "storage_chromadb" \
--extra "dbgpts" \
--extra "quant_bnb"

https://github.com/Devo919/Gewechat/issues/217
docker run -d --network langbot-network -v ./data/temp:/root/temp -p 2531:2531 -p 2532:2532 --privileged=true --restart=always --name=gewe gewe

docker compose up -d
https://github.com/hanfangyuan4396/dify-on-wechat/issues/196 每次配置完最后删除容器重新运行，不然容易获取登录验证码失败，所以建议刚开始部署直接更改/data/config.yaml文件，然后启动。