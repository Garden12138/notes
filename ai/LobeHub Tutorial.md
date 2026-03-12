## LobeHub 教程

### 部署安装

* ```docker-compose```方式：

  ```bash
  # 创建一个用于存储文件的文件夹
  mkdir lobe-chat-db && cd lobe-chat-db

  # 启动一键脚本
  bash <(curl -fsSL https://lobe.li/setup.sh) -l zh_CN

  # 启动 LobeHub
  docker-compose up -d
  ```

  启动过程中，会初始化设置```LobeHub```、```Casdor```以及```MinIO```的管理员账号和密码。

  访问```http://localhost:3210/```，使用```user```账号登录，即可进入```LobeHub```的页面。

  访问```http://localhost:8000/```，使用```admin```账号登录，即可进入```Casdor```的页面。

  访问```http://localhost:9001/```，使用```admin```账号登录，即可进入```MinIO```的页面。


### 简单实用

* 设置模型```API KEY```，配置模型```API```密钥，开始使用：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-05-25.png)

* 创建知识库，构建和管理知识库,便于快速检索信息：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-07-49.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-08-43.png)

* 与```AI```聊天，点击“随便聊聊”,选择模型并输⼊对话内容：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-13-06.png)

* ⽣图⽣成，选择模型,输⼊内容并⽣成图像：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-14-20.png)

* 使⽤内置助⼿，点击“发现”搜索内置助手⼿,添加并开始对话：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-15-37.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-16-21.png)

* ⾃定义助⼿，创建⾃定义助⼿,选择模型,设置⻆⾊设定并输⼊对话：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-03-12_15-18-21.png)

### 参考文献

* [LobeHub 官方文档](https://github.com/lobehub/lobehub)