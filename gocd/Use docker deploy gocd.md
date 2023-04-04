## 使用 docker 部署 gocd

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
  USER root  # 指定构建过程以及容器创建所使用root用户
  RUN apk update && apk add openjdk8  # 执行安装openjdk8命令
  ```

* 构建 ```gocd-server``` 镜像
  
  ```bash
  docker build -t gardeb12138/gocd-server-jdk8 -f server.dockerfile .
  ```

> 运行 ```gocd-server```容器
  
  ```bash
  docker run \
  --name gocd-server \
  --privileged \
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
  USER root  # 指定构建过程以及容器创建所使用root用户
  RUN apk update && apk add expect && apk add maven && apk add openjdk8 && apk add docker && apk add openrc # 执行安装maven，openjdk8，docker以及openrc命令
  COPY entrypoint.sh . # 复制构建上下文的entrypoint.sh文件至镜像内文件系统的当前工作目录
  RUN chmod +x entrypoint.sh # 赋予entrypoint.sh文件读写权限
  ENTRYPOINT ["/entrypoint.sh"] # 设置容器以entrypoint.sh方式启动
  ```

* 编写 ```gocd-agent``` 的启动脚本 ```entrypoint.sh```

  ```bash
  ## entrypoint.sh
  #!/bin/bash
  chown go /var/run/docker.sock # 设置go用户拥有使用docker的权限
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
  --privileged \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  -e GO_SERVER_URL=http://$(docker inspect --format='{{(index (index .NetworkSettings.IPAddress))}}' gocd-server):8153/go \
  -v '/var/run/docker.sock:/var/run/docker.sock' \
  garden12138/gocd-agent-jdk8
```

使用```-e```参数设置环境变量```GO_SERVER_URL```访问地址；使用```-v```参数设置```docker.sock```挂载数据卷。

> 注意事项

* ```gocd-agent``` 若需集成```Maven```，需要拷贝```maven setting.xml```文件至容器内（```/root/.m2/```）。
  
  ```bash
  docker cp settings.xml gocd-agent:/root/.m2
  ```
  
* [若需添加```Shell```脚本执行插件，点击下载](https://github.com/gocd-contrib/script-executor-task/releases/download/1.0.1/script-executor-1.0.1.jar)
