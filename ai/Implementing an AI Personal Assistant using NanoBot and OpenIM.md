## 使用NanoBot和OpenIM实现AI个人助手

### 目标

* 在 ```OpenIM（open-im-server）```里实现一个“类似飞书/企微的机器人”，并把它作为 ```NanoBot``` 的一个 ```chat channel```，使用户在 ```OpenIM``` 客户端里和 ```NanoBot``` 对话、调用工具（比如 ```cron``` 定时提醒）。

### 实现步骤

* 使用 ```docker```部署 ```NanoBot``` 服务：

  ```bash
  # Download source code
  git clone https://github.com/HKUDS/nanobot.git

  # Build the image
  docker build -t nanobot .

  # Initialize config (first time only)
  docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

  # Edit config on host to add API keys(如：providers.minimax.apiKey, providers.minimax.apiBase) and model(agents.default.model)
  vim ~/.nanobot/config.json

  # Run gateway
  docker run -d --name nanobot \
    --restart unless-stopped \
    -v ~/.nanobot:/root/.nanobot \
    -v /etc/localtime:/etc/localtime:ro \
    -v /etc/timezone:/etc/timezone:ro \
    -e TZ=Asia/Shanghai \
    -p 18790:18790 \
    -p 19000:19000 \
    nanobot gateway

  # Or run a single command
  docker exec -it nanobot /bin/bash
  nanobot agent -m "Hello!"
  nanobot status
  ```

* 使用```docker-compose```部署 ```OpenIM``` 服务：

  ```bash
  # Download source code
  git clone https://github.com/openimsdk/openim-docker

  # Set up MinIO address
  vim openim-docker/.env
  MINIO_EXTERNAL_ADDRESS="http://external_ip:10005"

  # Uncomment the openim-admin-front service in docker-compose if it is commented out.
  # vim openim-docker/docker-compose.yaml

  # Start services
  docker compose up -d

  # Quick verification
  # If you see the OpenIM login page, it means OpenIM is running successfully.
  curl http://your_server_ip:11001 
  curl http://your_server_ip:11002
  ```

* 使用默认管理员账号（```chatAdmin/chatAdmin```）登录 ```OpenIM``` 后台管理（```http://your_server_ip:11002```），创建机器人账号，记录机器人用户 ```ID```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-02_12-06-54.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-02_12-05-38.png)

* 开启 ```WebHooks``` 回调：

  * 将容器里的 ```webhooks.yml``` 拷贝到宿主机：

    ```bash
    mkdir -p ./openim-config

    CID=$(docker compose ps -q openim-server)
    docker cp "$CID:/openim-server/config/webhooks.yml" ./openim-config/webhooks.yml
    ```

  * 编辑 ```webhooks.yml``` 文件，设置回调地址，启用单聊并添加机器人用户 ```ID```：

    ```yaml
    url: "http://nanobot_ip:9000"

    afterSendSingleMsg:
      enable: true
      timeout: 5
      failedContinue: true
      attentionIds: ["<BOT_USER_ID>"]
    ``` 

  * 修改 ```docker-compose.yaml``` 文件，挂载 ```webhooks.yml``` 文件到 ```openim-server``` 容器：

    ```yaml
    services:
      openim-server:
        volumes:
          - ./openim-config/webhooks.yml:/openim-server/config/webhooks.yml:ro
    ```

* 添加 ```NanoBot``` 机器人为管理员：

  * 将容器里的 ```share.yml``` 拷贝到宿主机：

    ```bash
    mkdir -p ./openim-config

    CID=$(docker compose ps -q openim-server)
    docker cp "$CID:/openim-server/config/share.yml" ./openim-config/share.yml
    ```

  * 编辑 ```share.yml``` 文件，设置回调地址，添加机器人用户 ```ID``` 为管理员：

    ```yaml
    imAdminUserID:
      - imAdmin
      - "<BOT_USER_ID>"
    ``` 

  * 修改 ```docker-compose.yaml``` 文件，挂载 ```share.yml``` 文件到 ```openim-server``` 容器：

    ```yaml
    services:
      openim-server:
        volumes:
          - ./openim-config/share.yml:/openim-server/config/share.yml:ro
    ```

  * 重启 ```openim-server``` 容器：

    ```bash
    docker compose up -d --force-recreate openim-server
    ```

* 实现 ```OpenIM Channel```：

  * 在 ```.nanobot/config.json``` 文件里新增 ```opemim channel``` 配置：

    ```json
    {
      "channels": {
        "openim": {
          "enabled": true,
          "apiAddress": "http://openim-server_ip:10002",
          "adminUserId": "<ADMIN_USER_ID>", # 在openim-server的share.yml的imAdminUserID中配置，默认为imAdmin
          "adminSecret": "<ADMIN_SECRET>", # 在openim-server的share.yml的secret中配置，默认为openIM123
          "botUserId": "<BOT_USER_ID>",
          "botNickname": "NanoBot",
          "botPlatformId": 1,
          "listenHost": "0.0.0.0",
          "listenPort": 19000,
          "webhookPath": "/callbackAfterSendSingleMsgCommand",
          "enableReadReceipt": true
        }
      }
    }
    ```

  * 在 ```nanobot/config/schema.py``` 文件里新增 ```openim channel``` 配置定义：

    ```python
    class OpenIMConfig(BaseModel):
        """OpenIM channel configuration using webhook + REST API."""
        enabled: bool = False

        # OpenIM REST API address, e.g. http://openim-api:10002
        api_address: str = "http://127.0.0.1:10002"

        # Admin credential (used to get admin token, then mint bot user token)
        admin_user_id: str = "imAdmin"
        admin_secret: str = "openIM123"

        # Bot identity in OpenIM
        bot_user_id: str = ""
        bot_nickname: str = "NanoBot"
        bot_platform_id: int = 1  # keep consistent with your OpenIM client platformID usage

        # Webhook server listen (OpenIM server will POST here)
        listen_host: str = "0.0.0.0"
        listen_port: int = 19000
        webhook_path: str = "/callbackAfterSendSingleMsgCommand"

        # Read receipt / unread fix
        enable_read_receipt: bool = True

    class ChannelsConfig(BaseModel):
        # ...
        openim: OpenIMConfig = Field(default_factory=OpenIMConfig)
    ```

  * 在 ```nanobot/channels/manager.py``` 文件里新增 ```openim channel``` 注册：

    ```python
    def _init_channels(self) -> None:
        # ...
        # OpenIM channel
        if self.config.channels.openim.enabled:
            try:
                from nanobot.channels.openim import OpenIMChannel
                self.channels["openim"] = OpenIMChannel(self.config.channels.openim, self.bus)
                logger.info("OpenIM channel enabled")
            except ImportError as e:
                logger.warning("OpenIM channel not available: {}", e)
    ```

  * 新增 ```nanobot/channels/openim.py``` 文件，实现 ```OpenIM channel``` 逻辑：

    ```OpenIMRestClient``` 负责 ```token``` 和 ```send/read API``` 调用

    ```OpenIMChannel``` 负责启动 ```webhook server```，接收消息并转发到 ```bus```；收到 ```agent``` 输出后发送回复

    具体实现参考[这里](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/openim.py)

  * 修改（覆盖） [```nanobot/agent/loop.py```](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/loop.py)、 [```nanobot/cron/service.py``](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/service.py)、[```nanobot/agent/tools/cron.py```](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/cron.py) 以及 [```nanobot/cli/commands.py```](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/commands.py) 文件，使其可以正常回复 ```openim channel``` 的消息。

  * 修改 ```Dockerfile```，加速构建以及暴露```webhook server 19000```端口，可参考[这里](./code/Implementing%20an%20AI%20Personal%20Assistant%20using%20NanoBot%20and%20OpenIM/Dockerfile)

  * 暂停并删除 ```NanoBot``` 容器，删除 ```NanoBot```旧镜像，重新构建镜像，再启动：

    ```bash
    docker stop nanobot && docker rm nanobot && docker rmi nanobot
    docker build -t nanobot .
    docker run -d --name nanobot \
      --restart unless-stopped \
      -v ~/.nanobot:/root/.nanobot \
      -v /etc/localtime:/etc/localtime:ro \
      -v /etc/timezone:/etc/timezone:ro \
      -e TZ=Asia/Shanghai \
      -p 18790:18790 \
      -p 19000:19000 \
      nanobot gateway
    ```

* 验证功能，登录 ```OpenIM``` 客户端，添加机器人为好友，发送消息给机器人，机器人回复消息：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-02_16-13-45.png)

### 参考文献

* [NanoBot Github](https://github.com/HKUDS/nanobot)
* [OpenIM 官方稳定](https://docs.openim.io/zh-Hans/)