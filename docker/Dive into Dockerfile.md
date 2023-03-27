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
    ```

    构建命令：

    ```bash
    docker build -t ${imageName} - < ${dockerfile-path}/${dockerfile}
    ``` 

> 构建缓存

* 迭代过程中```Dockerfile```经常修改，镜像需要频繁重新构建，在这个情况下构建缓存可以提高构建速度。
* 镜像构建过程中，```Dockerfile```中的指令会从上往下顺序执行，每一个构建步骤的结果会被缓存起来：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-23_17-35-58.png)

  若再次构建，会直接使用构建缓存中的结果（```Using Cache```）；若修改源代码```main.c```，从```COPY main.c Makefile /src/```这条指令开始，后续的指令的构建缓存将会失效，需要重新构建：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-23_17-41-21.png)

  若不使用缓存，可在执行构建命令（```docker build```）时传入```--no-cache```。

> 镜像构建过程

* ```Dokcer Client```执行构建命令（```docker build```）
* ```Docker Engine```确定构建上下文，若构建上下文中存在```.dockerignore```文件，解析该文件并将符合匹配规则的文件资源从构建上下文中排除，最后将确定的构建上下文与```Dokcerfile```文件通过```Rest API```请求方式发送给```Docker Daemon Server```。
* ```Docker Daemon Server```逐条校验```Dokcerfile```中的指令是否合法，若不合法则立即结束构建。指令校验成功后将逐条执行指令，每条指令都会在原有镜像层上创建一层临时的```conatiner```层，用于指令执行指定的命令，每条指令执行结束后将删除临时```container```，最后生成镜像层。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-03-25_17-04-37.png)


#### .dockerignore介绍

> 介绍

* ```.dockerignore```是一个文本文件，存放在构建上下文的根目录下，在```Docker Client```发送构建请求之前，优先检查这个文件是否存在，若存在则解析这个文件，排除构建上下文中符合匹配规则的文件或文件夹。

> 语法规则

* 以```#```开头的行是备注，不会被解析为匹配规则
* 支持```?```通配符，匹配单个字符
* 支持```*```通配符，匹配多个字符，只能匹配单级目录
* 支持```**```通配符，可匹配多级目录
* 支持```!```匹配符，声明某些文件资源不需要被排除
* 可以用```.dockerignore```排除```Dockerfile```和```.dockerignore```文件。```Docker Client```仍会将这两个文件发送到```Docker Daemon Server```。

> 示例

* 假设构建上下文的根目录为```/```，```.dockerignore```文件如下：
  ```bash
  # 第一行是注释
  */demo* # 表示排除构建上下文中第一级目录下以demo开头的文件夹或文件，如/test/demofile.txt，/another/demo-dir/
  */*/demo* # 表示排除构建上下文中第二级目录下以demo开头的文件夹或文件
  demo? # 表示排除构建上下文中以demo开头且后只有一个任意字符的文件或文件夹，如demo1，demob
  **/demo* # 表示排除构建上下文中任意目录下以demo开头的文件或文件夹
  *.md # 表示排除构建上下文中所有Markdown中间
  !README*.md #表示不排除以README开头的Markdown文件
  README-secret.md #表示排除README-secret.md文件
  ```

#### Dockerfile介绍

> 介绍

* ```Dockerfile```是一个用于描述```Docker```镜像构建过程的文本文件，这个文件包含多条构建指令以及相关描述。```Dockerfile```的构建指令遵循以下语法：

  ```bash
  # Comment
  INSTRUCTION arguments
  ``` 
  
  以```#```开头的行绝大部分为注释，还有小部分为解析器指令。构建指令由两部分组成，第一部分为指令名称，第二部分为指令参数，指令名称不区分大小，但按照书写惯例推荐使用大写形式，以便于与指令参数区分。

> 解析器指令

> 常用指令

> 其他指令

#### 参考文档

> [一篇文章带你吃透 Dockerfile](https://juejin.cn/post/7179042892395053113)

> [官方文档](https://docs.docker.com/reference/)