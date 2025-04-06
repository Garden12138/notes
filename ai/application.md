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
豆包（火山写作）-> 活动策划内容生成 -> https://www.doubao.com/chat/2322909353459714
kimi -> 办公室写作助手 -> https://kimi.moonshot.cn/chat/cvjsfkeqvl78v7dj7r0g

AI图像工具
通义万相 -> 文字生成图片、图片生成视频 -> https://tongyi.aliyun.com/wanxiang/creation、https://tongyi.aliyun.com/wanxiang/videoCreation
可灵AI -> 文字生成图片、图片生成视频、文字生成音频、图片合成、配音音频 -> https://app.klingai.com/cn/text-to-image/new、https://app.klingai.com/cn/image-to-video/frame-mode/new、https://app.klingai.com/cn/text-to-audio/new、https://app.klingai.com/cn/try-on/model/new、https://app.klingai.com/cn/video-to-lip/new
万相营造 https://agi.taobao.com/
icongen https://www.icongen.io/
hitems https://zaohaowu.com/
tripo ai https://www.tripo3d.ai/
webshop https://www.weshop.com/
羚珑 https://ling.jd.com/

AI视频工具
通义万相
可灵AI
即创 https://aic.oceanengine.com/
Humva https://humva.ai/avatar/home
noisee ai https://noisee.com.cn/#/
必剪 https://member.bilibili.com/
opusclip https://www.opus.pro/
descript https://www.descript.com/
蝉镜 https://www.chanjing.cc/

AI办公工具
apippt https://www.aippt.cn/
gamma https://gamma.app/
kimi https://kimi.moonshot.cn/
wps https://ai.wps.cn/
wps灵犀 https://lingxi.wps.cn/
通义智文 https://tongyi.aliyun.com/
processon https://www.processon.com/
xmindai https://xmind.ai/
通义听悟 https://tingwu.aliyun.com/
飞书多维表格 https://www.feishu.cn/
Raycast AI https://www.raycast.com/
Hoarder https://hoarder.app/
qimi https://qimi.com/
glif https://glif.app/
通义晓蜜 https://tongy
钉钉个人版 https://workspace.dingtalk.com/

AI设计工具
Recraft AI https://www.recraft.ai/
墨刀 https://modao.cc/feature/ai.html

AI对话工具
deepseek https://www.deepseek.com/
chatgpt https://www.chatgpt.com/
通义千问 https://tongyi.aliyun.com/qianwen/
qwenchat https://chat.qwen.ai/
豆包 https://www.doubao.com/
kimi https://kimi.moonshot.cn/
通义星尘 https://tongyi.aliyun.com/xingchen/
grok https://x.ai/grok
claude https://claude.ai/
gemini https://gemini.google.com/
huggingchat https://huggingface.co/chat/
koko ai https://www.seeles.ai/

AI编程工具
trae https://www.trae.com.cn/
cursor https://www.cursor.com/
windsurf https://codeium.com/windsurf
github copilot https://github.com/features/copilot
通义灵码 https://lingma.aliyun.com/lingma
junie https://www.jetbrains.com/junie/
jetbrains ai https://www.jetbrains.com/ai/
codium ai https://www.qodo.ai/
tabby https://www.tabbyml.com/
fitten code https://code.fittentech.com/
deco https://ling-deco.jd.com/
httpie ai https://httpie.io/ai
hocoos https://hocoos.com/
heycli https://www.heycli.com/

AI搜索引擎
心流 https://iflow.cn/
devv https://devv.ai/
phind https://www.phind.com/
xanswer https://www.xanswer.com

AI音频工具
通义听唔 https://tingwu.aliyun.com/
suno https://suno.com/
minimax audio https://www.minimax.io/

AI开发平台/框架
dify https://dify.ai/
coze https://www.coze.cn/
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
ollama https://ollama.com/
cherry studio https://cherry-ai.com/
chatbot https://chatboxai.app/
jan https://jan.ai/
anythingllm https://anythingllm.com/

AI法律助手
通义法睿 https://tongyi.aliyun.com/farui/home

AI提示指令（学习参考）
langgpt https://github.com/langgptai/LangGPT
ai short https://www.aishort.top/
snack prompt https://snackprompt.com/
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
Mask Generation ->  ->Xenova/sam-vit-base
Image Feature Extraction -> -> MahmoodLab/UNI2-h
Keypoint Detection -> -> magic-leap-community/superpoint
自然语言处理：
Text Classification ->  -> BAAI/bge-reranker-v2-m3 
Token Classification -> -> iiiorg/piiranha-v1-detect-personal-information
Table Question Answering -> -> microsoft/tapex-large-finetuned-wtq
Question Answering -> -> distilbert/distilbert-base-cased-distilled-squad
Zero-Shot Classification -> -> knowledgator/comprehend_it-base
Translation -> -> ModelSpace/GemmaX2-28-9B-v0.1
Summarization ->  -> facebook/bart-large-cnn
Feature Extraction -> -> BAAI/bge-large-zh-v1.5
Text Generation -> -> Qwen/QwQ-32B deepseek-ai/DeepSeek-R1 deepseek-ai/DeepSeek-V3-0324
Text2Text Generation -> -> teapotai/teapotllm
Fill Mask -> -> answerdotai/ModernBERT-base
Sentence Similarity -> -> sentence-transformers/all-MiniLM-L6-v2
Text Ranking -> -> sentence-transformers/all-MiniLM-L6-v2
音频：
Text-to-Speech -> 文本转语音（文本 -> 语音） -> hexgrad/Kokoro-82M
Text-to-Audio -> 文本转音频（文本 -> 音频） -> stabilityai/stable-audio-open-1.0
Audio-to-Audio -> 音频转音频（音频 -> 音频） -> HKUSTAudio/xcodec2
Automatic Speech Recognition -> -> openai/whisper-large-v3
Audio Classification -> -> speechbrain/lang-id-voxlingua107-ecapa
Voice Activity Detection -> -> pyannote/segmentation-3.0
表格：
Tabular Classification -> -> Prior-Labs/TabPFN-v2-clf
Tabular Regression -> -> Prior-Labs/TabPFN-v2-reg
Time Series Forecasting -> -> amazon/chronos-t5-small
强化学习：
Reinforcemen Learning -> -> ValueFX9507/Tifa-DeepsexV2-7b-MGRPO-GGUF-Q8
Robotics -> -> Robotics
其他：
Graph Machine Learning -> -> ibm-research/materials.pos-egnn

uv sync --all-packages -i https://mirrors.aliyun.com/pypi/simple/ --frozen \
--extra "base" \
--extra "proxy_openai" \
--extra "hf" \
--extra "llama_cpp" \
--extra "rag" \
--extra "storage_chromadb" \
--extra "dbgpts" \
--extra "quant_bnb"