## 使用 One-API 作为 AI 代理

### 背景

* 客户端对接各种服务商的大语言模型需要实现各种接口，使用```One API```可以简化这一过程，可以统一为通用的```OpenAI```格式的接口。

### 搭建

* 使用```docker```部署```One API```服务端：

  ```bash
  docker run -d -p 3000:3000 \
    --name one-api \
    --restart always \
    -e TZ=Asia/Shanghai \
    -e SESSION_SECRET="${SESSION_SECRET}" \
    -e SQL_DSN="${USER}:${PASSWORD}@tcp(${HOST}:${PORT})/oneapi" \
    -v ${DATA_PATH}:/data \
    ghcr.io/martialbe/one-api
  ```

  环境变量```SESSION_SECRET```设置之后将使用固定的会话密钥，系统在重新启动后已登录用户```cookie```将依旧有效；环境变量```SQL_DSN```设置数据库连接信息。

* 登录```One API```服务```http://localhost:3000```，使用默认的用户名```root```和密码```123456```登录。

### 渠道配置

* 以阿里云百炼服务商为例：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi1.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi2.png)

  选择类型为“阿里云百炼”，填入名称“百炼”，添加分组以及选择将使用的阿里云百炼的模型，编写重定向规则，```key```为客户端使用的模型名称，```value```为阿里云百炼的模型名称，最后填入密钥。

### 令牌设置

* 创建客户端```ai-commit```令牌：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi3.png)

* 点击复制，生成客户端```ai-commit```的令牌：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi4.png)

### 域名配置

* [准备域名](../other/Implement%20own%20domain%20name%20site.md)

* 添加公网子域名解析，以阿里云为例：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi5.png)

* ```nginx```配置：

  ```bash
  # one-api
  server{
    listen 80;
    listen [::]:80;
    server_name openai.gardenqaq.cn;
    
    location / {
        client_max_body_size  64m;
        proxy_http_version 1.1;
        proxy_pass http://${ip}:${port};
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header Accept-Encoding gzip;
        proxy_read_timeout 300s;  # GPT-4 需要较长的超时时间，请自行调整
     }
  }
  ```

### 客户端使用

* 以```vscode```为例，安装```ai-commit```插件，配置```ai-commit```插件：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi6.png)

* 点击```ai-commit```按钮，自动调用模型，生成```commit```信息：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/oneapi7.png)

### 参考文献

* [One API Github](https://github.com/songquanpeng/one-api/blob/main/README.md)