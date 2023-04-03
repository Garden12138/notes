## GoCD

```docker pull gocd/gocd-server:v22.2.0```

```bash
## server.dockerfile
FROM gocd/gocd-server:v22.2.0
MAINTAINER Garden7979
USER root
RUN apk update && apk add openjdk8
```

```docker build -t garden7979/gocd-server-jdk8 -f server.dockerfile .```

```bash
docker run \
  --name gocd-server \
  --privileged \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  -p 8153:8153 \
  -v /data/godata:/godata \
  garden7979/gocd-server-jdk8
```



```docker pull gocd/gocd-agent-alpine-3.12:v22.1.0```

```bash
## agent.dockerfile
FROM gocd/gocd-agent-alpine-3.12:v22.1.0
MAINTAINER Garden7979
USER root
RUN apk update && apk add expect && apk add maven && apk add openjdk8 && apk add docker && apk add openrc
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

```bash
## entrypoint.sh
#!/bin/bash
chown go /var/run/docker.sock
bash /docker-entrypoint.sh
```

```docker build -t garden7979/gocd-agent-jdk8 -f agent.dockerfile .```

```bash
docker run \
  --name gocd-agent \
  --privileged \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  -e GO_SERVER_URL=http://$(docker inspect --format='{{(index (index .NetworkSettings.IPAddress))}}' gocd-server):8153/go \
  -v '/var/run/docker.sock:/var/run/docker.sock' \
  garden7979/gocd-agent-jdk8
```

```bash
## go-agent 注意事项
## 1.若集成Maven，需要拷贝maven setting.xml文件至容器内（/root/.m2/）
docker cp settings.xml gocd-agent:/root/.m2
```



https://github.com/gocd-contrib/script-executor-task/releases/download/1.0.1/script-executor-1.0.1.jar
