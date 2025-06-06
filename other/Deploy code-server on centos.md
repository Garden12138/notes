## 在centos部署code-server

### 安装部署

* [查看选择合适发布版本](https://github.com/coder/code-server/releases)

* 下载对应版本的code-server压缩包：

  ```bash
  wget https://github.com/coder/code-server/releases/download/3.4.1/code-server-3.4.1-linux-x86_64.tar.gz
  ```

* 解压压缩包并重新命名：
  
  ```bash
  tar -zxvf code-server-3.4.1-linux-x86_64.tar.gz
  ```

  ```bash
  mv code-server-3.4.1-linux-x86_64 code-server
  ```

* 运行启动服务：

  ```bash
  cd code-server

  export PASSWORD="cs@2025" && ./code-server --port 9999 --host 0.0.0.0
  ```

* 访问服务：

  ```bash
  http://<服务器ip>:9999
  ```

  输入密码登录，即可进入code-server界面：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/code-server-login.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/code-server-welcome.png)

### 参考文献

* [centos服务器安装code-server](https://cloud.tencent.com/developer/article/1655175)