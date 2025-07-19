## 在Linux上使用Ollama

### 查看Linux架构

```bash
cat /proc/version
# Linux version 5.10.134-18.al8.x86_64 (mockbuild@h87c01383.na61) (gcc (GCC) 10.2.1 20200825 (Alibaba 10.2.1-3.8 2.32), GNU ld version 2.35-12.3.al8) #1 SMP Fri Dec 13 16:56:53 CST 2024
```

可以看出当前系统的架构是```amd64```架构。

### 下载指定版本Ollama

大部分情况下，服务器都是不具备外网连接的，所以需要先[下载```Ollama```](https://github.com/ollama/ollama/releases)到本地，然后上传到服务器上，这里我们选择```ollama-linux-amd64.tgz```。

### 安装Ollama

* 解压：

  ```bash
  tar -xzf ollama-linux-amd64.tgz
  ```

* 移动到系统```PATH```目录下：

  ```bash
  sudo mv bin/ollama /usr/local/bin/ollama
  ```

* 赋予执行权限（如需要）：

  ```bash
  sudo chmod +x /usr/local/bin/ollama
  ```

* 验证安装：

  ```bash
  ollama version
  ```

### 使用systemctl管理Ollama

* 创建服务文件：

  ```bash
  sudo vim /etc/systemd/system/ollama.service
  ```

  内容如下：

  ```bash
  [Unit]
  Description=Ollama Service
  After=network.target

  [Service]
  Environment="HOME=/root"
  Environment="USER=root"
  ExecStart=/usr/local/bin/ollama serve
  Environment="OLLAMA_HOST=0.0.0.0:11434"
  Environment="OLLAMA_MODELS=/mnt/models/ollama"
  Restart=always
  RestartSec=3

  [Install]
  WantedBy=multi-user.target
  ```

  指定环境变量```OLLAMA_HOST```，使用外部服务可访问；指定环境变量```OLLAMA_MODELS```，指定模型目录。

* 启动服务：

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable ollama
  sudo systemctl start ollama
  ```

* 验证服务状态：

  ```bash
  sudo systemctl status ollama
  ```

* 访问服务：

  ```bash
  curl http://<ip>:11434/api/embeddings -d '{
      "model": "bge-large",
      "prompt": "你好，世界"
  }'
  ```



