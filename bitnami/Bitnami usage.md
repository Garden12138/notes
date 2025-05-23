## Bitnami使用

### 简介

* Bitnami容器库，提供热门应用、支持容器化并可随时启动。

#### 优点

* 自动更新，紧跟上游源码变化，通过自动化系统快速发布新版本。

* 定期更新：镜像随最新系统包定期发布。

* 一致性，容器、虚拟机和云镜像使用相同的组件和配置，方便切换。

* 轻量化基础，基于```minideb```（极简```Debian```镜像）或```scratch```（空镜像），安全且体积小。

### 使用

* 直接拉取预构建镜像：

  ```bash
  # 拉取最新版本，[镜像仓库](https://hub.docker.com/u/bitnami)：
  docker pull bitnami/[应用名]  # 例如：bitnami/nginx

  # 拉取指定版本
  docker pull bitnami/[应用名]:[标签]  # 例如：bitnami/postgresql:15
  ```

* 从源码构建镜像，[源码仓库](https://github.com/bitnami/containers.git)：

  ```bash
  git clone https://github.com/bitnami/containers.git
  cd bitnami/[应用名]/[版本]/[操作系统]  # 例如：bitnami/redis/6.2/debian-11
  docker build -t bitnami/[应用名] .
  ```

* 使用```Docker Compose```运行：

  ```bash
  # 下载 Compose 文件并启动应用
  curl -sSL https://raw.githubusercontent.com/bitnami/containers/main/bitnami/[应用名]/docker-compose.yml > docker-compose.yml
  docker-compose up -d
  ```


### 参考文献

* [bitnami/containers](https://github.com/bitnami/containers)