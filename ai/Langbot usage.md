## Langbot 使用说明

### 部署对话机器人（以Gewechat为例）

* 拉取镜像

  ```bash
  ## mac arm 从阿里云镜像仓库拉取
  docker pull registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine
  ```

* 更改镜像名

  ```bash
  docker tag registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine gewe
  ```

* 创建网络

  ```bash
  docker network create langbot-network
  ```

* 运行容器

  ```bash
  docker run -itd --network langbot-network -v /root/temp:/root/temp -p 2531:2531 -p 2532:2532 --privileged=true --name=gewe gewe /usr/sbin/init
  ```

### 部署Langbot

* 拉取源码

  ```bash
  git clone https://github.com/RockChinQ/LangBot
  ```

* 修改```docker-compose.yaml```文件

  ```yaml
  version: "3"

  services:
    langbot:
      image: rockchin/langbot:latest
      container_name: langbot
      volumes:
        - ./data:/app/data
        - ./plugins:/app/plugins
      restart: on-failure
      environment:
        - TZ=Asia/Shanghai
      ports:
        - 5300:5300  # 供 WebUI 使用
        - 2280-2290:2280-2290  # 供消息平台适配器方向连接
      # 根据具体环境配置网络
      networks:
        - langbot-network

  networks:
    langbot-network:
      external: true
  ```

* 运行容器

  ```bash
  docker-compose up -d
  ```

* 验证部署成功，访问```http://localhost:5300```

### 配置对话机器人（以Gewechat为例）

* 登录```Langbot```，点击左侧菜单栏中的设置，选择```platform.json```，切换编辑模式，找到```gewechat```适配器，填写配置信息，```app_id```与```token```不用填，个人微信扫码登录的时候会自动获取设置，地址中的域名```langbot```与```gewe```为容器名称：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/langbot1.png)

### 配置对话模型（以openapi为例）

* 选择```provider.json```，切换编辑模式，找到```openai-chat-completions```配置信息，填入地址，找到```keys.openai```配置信息，填入密钥，最后找到```model```，填入模型名称，示例如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/langbot2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/langbot3.png)

### 重启Langbot

* 重启```Langbot```容器：

  ```bash
  docker-compose down
  docker-compose up -d
  ```

  重启成功后，会看到控制台打印日志，出现微信登录二维码，扫描登录即可使用：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/langbot_wechat1.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/langbot_wechat2.png)

### 参考文献

* [https://docs.langbot.app/zh/insight/guide](https://docs.langbot.app/zh/insight/guide)
* [Gewechat GitHub](https://github.com/Devo919/Gewechat)

#### 注意事项

* Gewechat在本教程实现时未被封禁，请尝试其他实现方式。