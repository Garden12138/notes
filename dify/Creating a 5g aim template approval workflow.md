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