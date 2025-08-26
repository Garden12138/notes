## 在 Mac 上使用 Chrome MCP

### 介绍

* ```Chrome MCP Server```是一个基于```Chrome```插件的模型上下文协议 (```MCP```) 服务器，能够将```Chrome```浏览器功能暴露给```Cursor```等```AI```助手（```MCP```客户端），实现复杂的浏览器自动化、内容分析和语义搜索等，主要基于现有的用户习惯和配置、登录态。

### 安装

* 要求```node```环境版本为18.19.0以上，推荐使用[nvm](https://github.com/Garden12138/notes/blob/master/nodejs/Use%20nvm%20to%20manage%20nodejs.md)进行管理。

* 全局安装```mcp-chrome-bridge```：

  ```bash
  npm install -g mcp-chrome-bridge
  ```

* [下载```mcp-chrome```浏览器扩展](https://github.com/hangwin/mcp-chrome/releases)。

* 加载```mcp-chrome```浏览器扩展：

  * 打开```Chrome```并访问```chrome://extensions/```
  * 启用"开发者模式"
  * 点击"加载未打包的扩展程序"，选择下载路径下的解压文件
  * 点击插件图标打开插件，点击连接即可看到```mcp```的配置

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac1.png)
    
* ```MCP```客户端配置，如```Cursor```：

  ```bash
  {
    "mcpServers": {
      "chrome-mcp-server": {
        "type": "streamableHttp",
        "url": "http://127.0.0.1:12306/mcp"
      }
    }
  }
  ```

* 使用：

  * 获取浏览记录信息：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac2.png)

  * 分析页面内容：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac3.png)

  * 截图网页：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac4.png)

  * 网页操作：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac7.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac5.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac6.png)

  * 网页抓包：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac8.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac9.png)

  * 打开网页：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Use%20Chrome%20MCP%20on%20Mac10.png)

### 参考文献

* [Chrome MCP Server](https://github.com/hangwin/mcp-chrome/blob/master/README_zh.md)