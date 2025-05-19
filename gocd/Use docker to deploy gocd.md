## 使用 docker 部署 gocd

> 创建自定义网络，运行的```server```与```agent```容器都使用该网络，使得```server```和```agent```容器重启时，容器```ip```固定不变，```agent```服务访问```server```服务的```ip```不变，```server```服务中```agent```服务的注册```ip```不变，保持```server```和```agent```的可用性。
  
  ```bash
  docker network create --subnet=172.18.0.0/16 gocd-network
  ```

> 构建 ```gocd-server``` 镜像

* 拉取相应版本 ```gocd-server``` 父级镜像，如```v22.2.0```
  
  ```bash
  docker pull gocd/gocd-server:v22.2.0
  ```

* 制作 ```gocd-server``` 的 ```Dockerfile```

  ```bash
  ## server.dockerfile
  FROM gocd/gocd-server:v22.2.0
  MAINTAINER garden12138
  ## 指定构建过程以及容器创建所使用root用户
  USER root
  ## 执行安装openjdk8命令
  RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \  
    apk update && \
    apk add openjdk8
  ```

* 构建 ```gocd-server``` 镜像
  
  ```bash
  docker build -t garden12138/gocd-server-jdk8 -f server.dockerfile .
  ```

> 运行 ```gocd-server```容器
  
  ```bash
  docker run \
  --name gocd-server \
  --net gocd-network \
  --ip 172.18.0.12 \
  --privileged \
  --restart always \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  -p 8153:8153 \
  -v /data/godata:/godata \
  garden12138/gocd-server-jdk8
  ```

  ```--privileged```参数设置容器内```root```拥有真正的```root```权限；```log-opt max-sise```设置日志文件大小，```log-opt max-file```。

> 构建 ```gocd-agent``` 镜像
  
* 拉取相应版本 ```gocd-agent``` 父级镜像，如```v22.1.0```
  
  ```bash
  docker pull gocd/gocd-agent-alpine-3.12:v22.1.0
  ```

* 制作 ```gocd-agent``` 的 ```Dockerfile```

  ```bash
  ## agent.dockerfile
  FROM gocd/gocd-agent-alpine-3.12:v22.1.0
  MAINTAINER garden12138
  ## 指定构建过程以及容器创建所使用root用户
  USER root
  ## 执行安装maven，openjdk8，docker以及openrc命令
  RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \ 
    apk update && \
    apk add expect && \
    apk add maven && \
    apk add openjdk8 && \
    apk add docker && \
    apk add openrc
  ## 复制构建上下文的entrypoint.sh文件至镜像内文件系统的当前工作目录
  COPY entrypoint.sh .
  ## 赋予entrypoint.sh文件读写权限
  RUN chmod +x entrypoint.sh
  ## 设置容器以entrypoint.sh方式启动
  ENTRYPOINT ["/entrypoint.sh"]
  ```

* 编写 ```gocd-agent``` 的启动脚本 ```entrypoint.sh```

  ```bash
  #!/bin/bash
  ## 设置go用户拥有使用docker的权限
  chown go /var/run/docker.sock
  bash /docker-entrypoint.sh
  ```

* 构建 ```gocd-agent``` 镜像

  ```bash
  docker build -t garden12138/gocd-agent-jdk8 -f agent.dockerfile .
  ```

> 运行 ```gocd-agent```容器

```bash
docker run \
  --name gocd-agent \
  --net gocd-network \
  --ip 172.18.0.13 \
  --privileged \
  --restart always \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  -e GO_SERVER_URL=http://$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gocd-server):8153/go \
  -v '/var/run/docker.sock:/var/run/docker.sock' \
  garden12138/gocd-agent-jdk8
```

使用```-e```参数设置环境变量```GO_SERVER_URL```访问地址；使用```-v```参数设置```docker.sock```挂载数据卷。

> 注意事项

* ```gocd-agent``` 若需集成```Maven```，需要拷贝```maven setting.xml```文件至容器内（```/root/.m2/```）。
  
  ```bash
  docker exec -it gocd-agent /bin/bash
  mkdir /root/.m2/
  docker cp settings.xml gocd-agent:/root/.m2/
  ```

* 安装```Shell```脚本执行插件
  
  * [```Shell```脚本执行插件下载地址](https://github.com/gocd-contrib/script-executor-task/releases/download/1.0.1/script-executor-1.0.1.jar)，也可使用```Linux```命令下载：

    ```bash
    wget https://github.com/gocd-contrib/script-executor-task/releases/download/1.0.1/script-executor-1.0.1.jar
    ```

  * 移动插件文件至宿主机挂载目录下的插件文件夹，如上述的```/data/godata/```的```/plugins/external/```：

    ```bash
    mv script-executor-1.0.1.jar /data/godata/plugins/external/
    ```
  
  * 重启```gocd-server```，使安装的插件生效：

    ```bash
    docker restart gocd-server 
    ```
  
> 参考文献

* [GoCD 整行记（一）：定制 gocd-server](https://www.jianshu.com/p/e4e4ed65f100)
  
* [GoCD 整行记（二）：定制 gocd-agent](https://www.jianshu.com/p/6b0961d806d2)

* [GoCD Plugin User Guide](https://www.bookstack.cn/read/gocd-20.5-en/42e37f2ec557d5bc.md#ejh70a)

* [gocd/gocd-server](https://hub.docker.com/r/gocd/gocd-server)

* [gocd/gocd-agent-docker-dind](https://hub.docker.com/r/gocd/gocd-agent-docker-dind)