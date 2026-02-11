## 创建5G AIM模板审批工作流

### 背景

* 业务系统需要支持```5G AIM```模板的自动初审，实现对模板上的图文合法性、相关性进行审核，并且能够对模板上的促销活动时间进行过期检查。

### 思路

* 流程1
  * 提取图片中的时间
  * 处理提取的时间，进行格式转化，若为农历则进行农历转新历
  * 判断处理后的时间是否在促销活动时间内
* 流程2
  * 分析图文合法性、相关性
* 合并流程1、流程2分析结果输出审批结果 

### 步骤

* 创建“获取今年年份”代码执行节点，获取当前年份：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_1.png)

* 创建“图片日期提取”```LLM```节点，提取图片中的日期：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_2.png)

* 创建“处理图中提取的日期”代码执行节点，格式化日期，判断是否为农历，进行农历转新历：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_3.png)

* 创建“判断提取日期是否过期”代码执行节点，判断处理后的日期是否在促销活动时间内：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_4.png)

* 创建“审核图片和文案”```LLM```节点，对图文进行合法性、相关性分析：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_5.png)

* 创建变量聚合器节点、模板转换节点、```LLM```节点，将分析结果转换为```JSON```格式：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_6.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_7.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_8.png)

* 创建“审核结果聚合”变量聚合器节点、“审核聚合结果判断”代码执行节点，合并流程1、流程2分析结果输出审批结果：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_9.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_template_approval_10.png)

* [完整```yaml```文件](./5gaim-template-approval.yml)

### 效果

* 对“黄、赌、毒”进行审核：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/template_approve_hdd1.png)

* 对“3.8 妇女节”营销活动进行审核：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/template_approve_381.png)

* 正常模板审核：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/template_approve_raw.png)

### 升级提升

* 业务系统升级，对于模板审核进行优化拆分，重新整合，划分为文案AI审核、图像AI审核、链接AI审核、视频AI审核、图文版式模板相关性审核、模板相关性审核。

* 文案AI审核，对模板中的文案进行规范校验：

  - 违禁词/敏感词检测（政治、色情、暴力、违禁广告用语）
  - 虚假/夸大宣传识别（“最”系列、绝对化用语、无法证实的承诺）
  - 行业特定合规检查（医疗、金融、教育等特殊行业用语规范）
  - 基础文案质量评估（可读性、语法、拼写错误）

  参考[完整```yaml```文件](./yaml/content-ai-approval.yml)

  输入：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_10-33-21.png)

  输出：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_10-34-37.png)

* 图像AI审核，对模板中的图片进行规范性校验：

  - 视觉违规内容识别（敏感场景、不当人物、不良标志）
  - 版权风险检测（水印、知名IP元素、疑似未授权素材）
  - 技术质量评估（清晰度、尺寸、格式、色彩模式、马赛克、白边黑边）

  参考[完整```yaml```文件](./yaml/image-ai-approval.yml)

  输入：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_10-55-16.png)
  
  输出：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_10-56-23.png)

  关键节点说明：

  - "图像合规审核"```LLM```节点使用的是```Step3-VL-1OB```模型，该模型的部署可参考[使用```vLLM```多卡推理部署```Step3-VL-10B```](../ai/Deploying%20Step3-VL-10B%20using%20vLLM%20multi-GPU%20inference.md)，模型设置思考模式：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-18-28.png)
  
  
    并且该节点需要开启视觉，设置为前一节点"图像下载"节点的输出：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-01-02.png)

  
    另外，也可使用千问的```qwen3-vl-plus```或者混元的```hunyuan-vision-1.5-instruct```模型。对于新模型，服务提供商没有更新，需要在插件管理更新服务提供商插件：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-27-16.png)

    如果更新完插件后仍然没有新模型，可以尝试使用```OpenAI-API-compatible```的服务提供商的方式集成进来，一般大厂的服务提供商都支持```OpenAI```兼容的格式，如：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-31-00.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-31-39.png)

* 链接AI审核，对模板中的链接进行规范性校验：

  - HTTPS规范
  - 恶意网址
  - 钓鱼网站

  参考[完整```yaml```文件](./yaml/link-ai-approval.yml)

  输入：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-51-54.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-55-14.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-56-27.png)

  输出：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-52-33.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-53-14.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_11-57-01.png)

  关键节点说明：

  - "```URL```规范校验"```HTTP```节点，主要是实现```URL```规范校验的```Fastapi```服务，由于```sandbox```环节存在```dns```解析等问题，所以依赖于```Web```服务，[代码参考](./code/app_url.py)

  - "钓鱼网站校验"```HTTP```节点，主要是实现```URL```钓鱼性质校验的```Fastapi```服务，[代码参考](./code/app_phishing.py)

* 视频AI审核，对模板中的视频画面内容、字幕内容以及音频进行规范性校验：

  - 视觉违规内容识别（敏感场景、不当人物、不良标志）
  - 版权风险检测（水印、知名IP元素、疑似未授权素材）
  - 技术质量评估（清晰度、尺寸、格式、色彩模式、马赛克、白边黑边）

  参考[完整```yaml```文件](./yaml/video-ai-approval.yml)

  输入：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_15-43-58.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_15-45-33.png)

  输出：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_15-42-07.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Snipaste_2026-02-11_15-46-16.png)

  关键节点说明：

  - "获取音频内容描述"```HTTP```节点，通过视频链接获取其中的音频内容，[代码参考](./code/audio2text.py)，需[本地运行 Funasr-Nano-2512 模型](../ai/Running%20the%20Funasr-Nano-2512%20model%20locally.md)

  - "获取画面以及字幕内容描述"```HTTP```节点，通过视频链接获取其中的画面以及字幕内容，[代码参考](./code/qwen3_omni_flash_api.py)，使用的是千问模型```API```。

* 图文版式模板相关性审核，对模板中的图文版式进行相关性校验：

  - 区域1的图片内容、区域1的图片链接内容、区域2的标题文案、区域3的正文文案、区域4的按钮文案以及区域4的按钮链接内容相关性校验

  参考[完整```yaml```文件](./yaml/template-layout-approval.yml)

  关键节点说明：

  - "生成区域```x```链接对应页面截图"```HTTP```节点，通过链接打开页面，截图下载，[代码参考](./code/app_link_screenshot_oss.py)