## server.dockerfile
FROM gocd/gocd-server:v22.2.0
MAINTAINER garden12138
## 指定构建过程以及容器创建所使用root用户
USER root
## 执行安装openjdk8命令
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \  
  apk update && \
  apk add openjdk8
