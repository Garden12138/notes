## 创建5G AIM投放效果分析助手工作流

### 背景

* 根据售前需求，需设计一套```5G AIM```投放效果分析助手工作流，用于帮助运营商分析其```5G AIM```投放效果，投放效果数据由运营提供。助手提供“黄金时段”、“最佳版式”、“曝光最高文案”、“最优人群标签”、“效果最优模板”固定分析维度以及支持自定义分析维度的能力。

### 思路

* 将用户问题进行分类，分为```5G AIM```投放“黄金时段”、“最佳版式”、“曝光最高文案”、“最优人群标签”、“效果最优模板”相关问题，无关问题则进行提问式回复。
* 判断问题是否为固定分析维度，若是则进入```API```检索模式，若不是则进入知识库模式。
* ```API```检索模式则进行```API```调用，获取相关数据（按维度排序的数据，如黄金时段则返回曝光率最高的数据），并进行分析，知识库模式则进行知识库检索，获取相关知识，并进行分析。

### 步骤

* 创建“5G超信投放问题分类”问题分类器节点，将用户问题分类：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi1.png)

* 创建“黄金时段知识检索前置”代码执行节点、“初始化问题判断”条件分支节点，用于判断问题是否为固定分析维度：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi4.png)

* 创建“黄金时段```API```检索”代码执行节点、“黄金时段```API```检索模型分析”```LLM```节点，用于调用```API```获取相关数据并进行分析：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi5.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi6.png)

* 创建“黄金时段知识检索”知识检索节点、“黄金时段知识检索模型分析”```LLM```节点，用于获取相关知识并进行分析：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi7.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi8.png)


* [完整```yaml```文件](./5gaim-delivery-effect-analysis-assistant.yml)

### 效果

* 输入固定维度问题“黄金时段”：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi_hjsd1.png)

* 输入自定义维度问题“分析一下汽车行业的```5G```超信投放的黄金时段“：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/5gaim_deli__eff_analy_assi_hjsd2.png)