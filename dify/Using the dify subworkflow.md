## 使用 dify 子工作流

### 背景

* 当工作流多样复杂时，我们可考虑将其拆分成多个子工作流，每个子工作流只负责一项具体的任务。将工作流发布为工具，即可在其他工作流中使用。

### 实践

* 以个人助手识别发票信息为例，我们可以将其拆分成个人助手工作流以及发票识别子工作流，个人助手工作流中调用发票识别子工作流，并将识别结果返回给用户：

  * 创建空白应用，选择工作流应用类型，输入应用名称，点击创建：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_12-07-40.png)

  * 编辑用户输入节点，新增文档类型字段“发票”以及字符串类型字段“名称”：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-15-02.png)

  * 新增 ```PDF转PNG转换器``` 节点，```PDF内容``` 设置用户输入的“发票”字段：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-18-20.png)

  * 新增识别发票信息```LLM```节点，选择模型，开启视觉效果，设置提示词，结构化获取发票信息：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-20-49.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-25-01.png)

    提示词如下：

    ```bash
    # 角色
    你是一个专业的发票信息提取助手。

    # 任务
    你的任务是从图片中，精准地提取所有关键信息，并严格按照指定的 JSON 格式输出。请忽略文本中与发票无关的干扰项（如“下载次数”）。

    # 输入变量
    发票的原始文本内容将通过图片识别的内容传入。

    # 输出要求
    1.  **严格的JSON格式**：你的回答必须是一个完整的、格式正确的 JSON 对象，不能包含任何 JSON 之外的解释、注释或文字。
    2.  **数据清洗**：
        * 对于金额和数量，只保留数字，去除货币符号（如 `¥`）。
        * 对于日期，统一输出为 `YYYY-MM-DD` 格式。
        * 对于税率，输出百分比字符串，例如 `"13%"`。
        * 如果某一项信息在发票中不存在，请使用 `null` 或者空字符串 `""` 作为值。
    3.  **处理项目列表**：发票中的“项目名称”部分可能包含多个商品或服务，甚至可能包含折扣（金额为负数）。你需要将每一个项目都作为一个独立的对象，放入 `items` 数组中。

    # JSON 输出格式

    ```json
    {
      "invoice_title": "string",
      "invoice_number": "string",
      "issue_date": "string",
      "buyer_info": {
        "name": "string",
        "tax_id": "string"
      },
      "seller_info": {
        "name": "string",
        "tax_id": "string"
      },
      "items": [
        {
          "name": "string",
          "model": "string",
          "unit": "string",
          "quantity": "number | null",
          "unit_price": "number | null",
          "amount": "number",
          "tax_rate": "string",
          "tax_amount": "number"
        }
      ],
      "total_amount_exclusive_tax": "number",
      "total_tax_amount": "number",
      "total_amount_inclusive_tax": {
        "in_words": "string",
        "in_figures": "number"
      },
      "remarks": "string",
      "issuer": "string"
    }
    ```
  
  * 新增获取发票信息代码执行节点，获取纯净```json```结构的发票信息：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-27-34.png)

    代码如下：

    ```python
    import json
    import re

    def main(output: str) -> dict:
        # 去除 markdown 代码块标记
        output = re.sub(r"^```[\w]*\s*", "", output.strip(), flags=re.IGNORECASE)
        output = re.sub(r"```$", "", output.strip())
        output = output.strip()

        data = json.loads(output)
        # 直接保留原始日期字符串
        date_str = data.get("issue_date", "").replace("/", "-").replace(".", "-").strip()

        items_str = json.dumps(data.get("items", []), ensure_ascii=False)
        record = {
            "invoice_title": data.get("invoice_title", ""),
            "invoice_code": data.get("invoice_number", ""),
            "issue_date": date_str,
            "buyer_name": data.get("buyer_info", {}).get("name", ""),
            "buyer_tax_id": data.get("buyer_info", {}).get("tax_id", ""),
            "seller_name": data.get("seller_info", {}).get("name", ""),
            "seller_tax_id": data.get("seller_info", {}).get("tax_id", ""),
            "items": items_str,
            "total_amount": data.get("total_amount_exclusive_tax", ""),
            "total_tax": data.get("total_tax_amount", ""),
            "total_with_tax": data.get("total_amount_inclusive_tax", {}).get("in_figures", ""),
            "total_with_tax_in_words": data.get("total_amount_inclusive_tax", {}).get("in_words", ""),  # 新增
            "remarks": data.get("remarks", ""),
            "issuer": data.get("issuer", "")
        }
        return {
            "result": json.dumps(record, ensure_ascii=False)

        }
    ```

  * 新增```转换Json Excel格式```代码执行节点，将发票信息转换为下一个 ```JSON转EXCEL``` 节点插件所需格式：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-32-19.png)

    代码如下：

    ```python
    import json

    def main(arg1: str) -> dict:
        # 取出 "result" -> 字符串 JSON
        record = json.loads(arg1)

        # 将 record 转成 excel 一行（根据你业务字段名填入）
        excel_row = {
            "invoice_title": record.get("invoice_title", ""),
            "invoice_code": record.get("invoice_code", ""),
            "issue_date": record.get("issue_date", ""),
            "buyer_name": record.get("buyer_name", ""),
            "buyer_tax_id": record.get("buyer_tax_id", ""),
            "seller_name": record.get("seller_name", ""),
            "seller_tax_id": record.get("seller_tax_id", ""),
            "items": record.get("items", ""),
            "total_amount": record.get("total_amount", ""),
            "total_tax": record.get("total_tax", ""),
            "total_with_tax": record.get("total_with_tax", ""),
            "total_with_tax_in_words": record.get("total_with_tax_in_words", ""),
            "remarks": record.get("remarks", ""),
            "issuer": record.get("issuer", "")
       }

        # 生成你需要的目标格式
        result = {
            "[format]": {
                "defaults": {
                    "rowHeight": 20,
                    "columnWidth": 15
                }
            },
            "Sheet1": [excel_row]   # 一行，如果以后要多行就 append 更多
        }

        return {
            "result": json.dumps(result, ensure_ascii=False)
        }
    ```

  * 新增```Json转Excel```插件节点，选择```JSON```字符串，设置文件名：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-34-29.png)

  * 新增输出节点，设置输出字段：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-36-50.png)

  * 点击发布为工具，设置工具信息：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-38-13.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-39-10.png)

  * 新增个人助手 ```Chatflow```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-40-43.png)

  * 编辑用户输入节点，新增文档类型字段“发票文件”：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-40-43.png)

  * 新增发票识别总结子工作流节点，设置发票以及名称变量：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-44-05.png)

  * 新增发票识别总结结果聚合节点，设置聚合子工作流返回结果字段：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-45-24.png)

  * 新增直接回复节点，设置回复内容：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-46-07.png)

  * 点击预览，运行测试，上传发票文件，输出文件名：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-09_17-48-36.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-02-10_10-02-41.png)

### 参考文献

* [工作流 Web App](https://docs.dify.ai/zh/use-dify/publish/webapp/workflow-webapp)