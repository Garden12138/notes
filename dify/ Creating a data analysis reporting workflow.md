## 创建数据分析报告工作流

### 背景

* 业务系统的报表模块需要实时生成数据图表以及分析报告，快速准确地反映业务数据。

### 思路

* 创建“报表”数据库表的知识库。
* 通过查找知识库生成SQL语句。
* 执行SQL语句，获取数据。
* 将获取数据输入数据分析节点，生成数据分析报告。
* 将获取数据输入ECharts图表生成节点，生成可视化图表。

### 步骤

* 安装模型供应商，案例使用的```Embedding```模型是```Ollama```服务运行的```bge-large```模型，```LLM```为百炼的```DeepSeek V3```模型，所以此处安装且配置```Ollama```以及```通义千问```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow1.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow2.png)

* 安装工具```database```以及```Echarts```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow3.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow4.png)

* 创建“报表”数据库表的知识库：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow5.png)

* 创建“查找表结构”知识检索节点，添加知识库：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow6.png)

* 创建“生成```SQL```”```LLM```节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow7.png)

* 创建“```SQL```清洗”代码执行节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow8.png)

* 创建“```SQL```执行”```Database SQL Execute```工具节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow9.png)

  ```DB URI```选项填写规范：```mysql+pymysql://${username}:${password}@${ip}:${port}/${database}```

* 创建“数据分析”```LLM```节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow10.png)

* 创建“提取图表数据”参数提取器节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow11.png)

  用于提取图表类型以及图表数据。

* 创建“根据图表类型分类”条件分支节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow12.png)

* 创建“线性图表”```ECharts```图表生成节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow13.png)

* 创建“线性图表赋值”变量赋值节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow14.png)

* 编辑回复节点：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/%20Creating%20a%20data%20analysis%20reporting%20workflow15.png)

* 运行工作流，效果如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/Creating%20a%20data%20analysis%20reporting%20workflow16.png)

* [完整```yaml```文件](./dbchat-report.yml)

### 参考文献

* [5000字教程：用AI实时查询数据库，自动生成可视化图表 | Dify工作流](https://blog.csdn.net/m0_59164520/article/details/148082647)