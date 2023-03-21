#### 镜像构建原理

> 背景

* 使用中间件时，通常从```Docker```镜像仓库拉取镜像，利用镜像创建并运行容器。```Docker```官方镜像是通过一定方式构建出来的，理解构建原理以及过程，也可构建出自定义应用镜像。```Dockerfile```是用来描述```Docker```镜像构建过程的文本文件，该文件包含多条构建指令以及相关描述。理解构建原理以及```Dockerifle```的相关语法，编写高效的```Dockerfile```，以便于缩短整体构建时间以及减少最终镜像的大小。

> Docker架构模式回顾

* ```Docker```使用的是```client/server```架构模式。构建镜像时，用户在```Docker Client```端输入构建命令，通过```Docker Engine```以```REST API```的形式向```Server Docker Daemon```发起构建请求，```Server Docker Daemon```根据构建请求的内容开始镜像的构建工作，并向```Docker Client```持续返回构建过程的信息，在```Docker Client```可以看到当前的构建状态。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-21_12-02-51.png)

> 镜像分层模型

> 基础镜像与父级镜像

> 构建上下文

> 构建缓存

> 镜像构建过程

#### .dockerignore介绍

> 语法规则

> 示例

#### Dockerfile介绍

> 解析器指令

> 常用指令

> 其他指令

#### 参考文档

> [一篇文章带你吃透 Dockerfile](https://juejin.cn/post/7179042892395053113)