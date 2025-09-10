## 在 Mac 上使用 FastAPI MCP

### 介绍

* 用于自动将```FastAPI```端点作为```Model Context Protocol (MCP) ```工具暴露出来。

### 安装

* 安装包：

  ```bash
  pip install fastapi-mcp
  ```

* 使用```FastAPI MCP```封装```FastAPI```端点，且```mount```到```FastAPI```应用上：

  ```python
  from apps import app  # The FastAPI app
  from fastapi_mcp import FastApiMCP

  # Add MCP server to the FastAPI app
  mcp = FastApiMCP(app)

  # Mount the MCP server to the FastAPI app
  mcp.mount_http(mount_path="/fastapi-mcp")
  ```

* ```mcp```客户端如```cursor```使用```SSE```配置：

  ```bash
  "FastAPI-MCP-Server": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8000/fastapi-mcp"
    }
  ```

### 使用

* 启动```FastAPI```应用：

  ```bash
  python server.py
  ```  

* 连接```mcp```客户端，并订阅```FastAPI```端点，使用“获取所有产品信息”进行对话：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/fastapi_mcp1.png)


### 本文示例可参考[这里](https://github.com/Garden12138/ai-example/tree/main/FastAPI-MCP)，更多使用示例请参考[fastapi_mcp/examples](https://github.com/tadata-org/fastapi_mcp/tree/main/examples)。

### 参考文献

* [FastAPI MCP工具](https://www.modelscope.cn/mcp/servers/@tadata-org/fastapi_mcp)
* [fastapi_mcp Github](https://github.com/tadata-org/fastapi_mcp)
* [FastAPI-MCP : 自动将 FastAPI 端点转换为 MCP 工具](https://zhuanlan.zhihu.com/p/1895441737528366536)