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
