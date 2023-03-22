#### 镜像构建原理

> 背景

* 使用中间件时，通常从```Docker```镜像仓库拉取镜像，利用镜像创建并运行容器。```Docker```官方镜像是通过一定方式构建出来的，理解构建原理以及过程，也可构建出自定义应用镜像。```Dockerfile```是用来描述```Docker```镜像构建过程的文本文件，该文件包含多条构建指令以及相关描述。理解构建原理以及```Dockerifle```的相关语法，编写高效的```Dockerfile```，以便于缩短整体构建时间以及减少最终镜像的大小。

> Docker架构模式回顾

* ```Docker```使用的是```client/server```架构模式。构建镜像时，用户在```Docker Client```端输入构建命令，通过```Docker Engine```以```REST API```的形式向```Server Docker Daemon```发起构建请求，```Server Docker Daemon```根据构建请求的内容开始镜像的构建工作，并向```Docker Client```持续返回构建过程的信息，在```Docker Client```可以看到当前的构建状态。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-21_12-02-51.png)

> 镜像分层模型

* ```Docker```镜像是用于运行容器的只读模板，通过```Dockerfile```文件中定义的若干条指令构建而成，构建结束后，会有原有镜像层上生成一个新的镜像层。
  
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-21_16-52-07.png)

* 使用新镜像（```tomcat```）运行一个容器，会在新镜像层上创建一个可写的容器层，在容器中写的文件数据会保存在这个容器层中。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-21_16-57-02.png)

> 基础镜像与父级镜像

* 用于构建基础镜像的```Dockerfile```不指定父级镜像，使用如下的形式定义基础镜像：
  
  ```bash
  FROM scratch
  ```

  ```scratch```是一个空镜像，表示从零开始构建镜像，常被用来构建最小化镜像，如```busybox```，```debian```，```alpine```等镜像，这些镜像省去了许多```Linux```命令，因此镜像体积很小。一般情况下不需要自己构建基础镜像。

* 构建自定义应用镜像时，可通过```FROM```指定使用的父级镜像，比如官方的```tomcat```镜像没有```yum```、```vim```等常用```Linux```命令，可以将```tomcat```镜像作为父镜像，然后构建自定义应用镜像的```Dockerfile```里声明安装```yum```、```vim```命令的指令从而构建自定义应用镜像，使用该镜像运行的容器中可直接使用这些安装的```Linux```命令。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-21_22-45-18.png)

> 构建上下文

* ```Docker Client```向```Server Docker Daemon```发送的构建请求包含两部分，第一部分是描述镜像构建的```Dockerfile```文件，第二部分是```Build Context```构建上下文。构建上下文是多个文件的集合，这些文件可以为指定路径下的文件，也可以为远程资源中指定路径下的文件，在镜像构建过程中，```Server Docker Daemon```可以访问这些文件并执行相应的操作。构建上下文可分为：

  * 路径上下文。构建命令（```docker build```）中指定具体路径，该路径下的所有文件即为路径上下文，这些文件会被打包并发送到```Server Docker Daemon```，然后被解压。

    ```bash
    docker build -t ${imageName} -f ${dockerfile-path}/${dockerfile} ${file-path} 
    ``` 
    
    构建请求的第一部分为```Dockerfile```，可不指定具体路径的```Dockerfile```文件，默认是在当前目录下，文件名称是默认名称```Dockerfile```；构建请求的第二部分为路径上下文，```${file-path}```代表指定目录下的所有文件，这些文件在经过```.dockerignore```文件的规则匹配，将匹配的文件都发送至```Server Docker Daemon```：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-22_15-16-59.png)

  * ```URL```上下文。构建命令（```docker build```）支持指定远程仓库地址：

    ```bash
    docker build -t ${imageName} ${repository}#${branch}:${subDir}
    ```  

    ```${repository}```代表远程仓库地址，```${branch}```表示仓库分支，```${subDir}```指定仓库根目录下的子目录，该目录为```URL上下文```，其中包含```Dockerfile```文件。构建流程如下：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-22_16-26-04.png)
   
  * 省略上下文。若```Dockerfile```中的指令不需要对任何文件进行操作，可省略构建上下文，此时不会向```Server Docker Daemon```发送额外的文件，从而提供构建速度。如```Dockerfile```：

    ```bash
    FROM busybox
    RUN echo "hello world"
    EOF
    ```

    构建命令：

    ```
    docker build -t ${imageName} -<<EOF
    ``` 

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