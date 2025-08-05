## 使用docker-compose部署dify

### 前提条件

* [docker](https://gitee.com/FSDGarden/learn-note/blob/master/docker/Install%20dokcer%20on%20centos.md)
* [docker-compose](https://gitee.com/FSDGarden/learn-note/blob/master/docker/Install%20docker-compose%20on%20centos.md)

### 步骤

* 克隆仓库：

  ```bash
  git clone https://github.com/langgenius/dify.git
  ```

* 修改配置文件：

  ```bash
  cd dify/docker
  cp .env.example .env
  ```

* 启动服务：

  ```bash
  docker-compose up -d
  ```

* 访问服务：

  ```bash
  http://localhost

* 对于本地部署，我们有可能会修改前端```UI```或者修改源码，启动服务后，需要重新构建镜像并重新启动服务，这个时候我们需要找到```docker-compose.yml```文件，修改```build```命令，重新构建镜像：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/dify_1.png)

  然后重新启动服务：

  ```bash
  docker-compose down
  docker-compose up -d
  ```

### 参考文献

* [langgenius/dify](https://github.com/langgenius/dify)