## 在 Centos 上安装 docker

> 卸载旧版本 docker
  
  ```bash
  sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine
  ```

> 安装 yum 工具包 yum-utils

  ```bash
  sudo yum install -y yum-utils
  ```

> 添加 docker 配置管理仓库

  ```bash
  sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
  ```

> 安装 docker
  
  ```
  sudo yum install docker-ce docker-ce-cli containerd.io
  ```

> /etc/docker 目录下添加包含国内镜像源的 daemon.json 文件

  ```bash
  vim /etc/docker/daemon.json

  ## daemon.json
  {
    "insecure-registries": ["192.168.9.8:80"],
    "registry-mirrors": ["https://registry.cn-hangzhou.aliyuncs.com"]
  }
  ```

> 运行服务

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl start docker
  docker -v
  ```

> 参考文献

* [docker install](https://docs.docker.com/engine/install/centos/)
