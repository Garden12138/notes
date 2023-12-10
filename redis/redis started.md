## Redis 入门

> Redis 初识

* 简介

  * ```Redis（Remote Dictionary Server）```是由开源的使用```ANSI C```语言编写、遵守```BSD```协议且支持网络、基于内存可持久化的```Key-Value```型数据库，并支持多种语言的```API```。它通常被称为数据结构服务器，因值```（Value）```可以为字符串```（String）```、哈希```（Hash）```、列表```（List）```、集合```（Set）```以及排序集合```（ZSet）```等数据结构。

  * ```Redis```与其他```Key-Value```存储的优势：
    * ```Redis```运行在内存中，性能极高，同时还支持持久化至磁盘。
    * 支持丰富的数据类型，如字符串```（String）```、哈希```（Hash）```、列表```（List）```、集合```（Set）```以及排序集合```（ZSet）```等数据类型，这些复杂的数据类型在内存中可非常方便的操作，对开发者透明，无需进行额外的抽象。
    * 原子性，```Redis```所有操作都是原子性，同时还支持对几个操作全并后的原子性执行。
    * 丰富的特性，```Redis```支持数据备份```（Master-Slave）模式```、发布/订阅和管道等特性。

* 安装
  
  * ```Windows```
    
    * [根据操作系统选择具体位数](https://github.com/tporadowski/redis/releases。)，将选定压缩包下载安装至指定文件路径下，解压后进入解压文件夹，在当前文件夹打开```cmd```窗口，输入命令启动```redis```服务：
      
      ```bash
      # redis.windows.conf启动参数省略则使用默认配置
      redis-server.exe redis.windows.conf
      ```
      
    * 继续打开另一个```cmd```窗口，输入命令打开客户端：

      ```bash
      redis-cli.exe -h 127.0.0.1 -p 6379
      ```

  * ```Linux```

    * [选择稳定版本](http://download.redis.io/releases)，输入命令下载且解压：

      ```bash
      # version为选定的版本
      wget http://download.redis.io/releases/redis-${version}.tar.gz & tar -xzvf redis-${version}.tar.gz
      ```

    * 编译源码：
      
      ```bash
      make
      ```
    
    * 启动服务：
      
      ```bash
      # redis.conf启动参数省略则使用默认配置
      cd src/
      ./redis-server redis.conf
      ```
    
    * 启动客户端：

      ```bash
      cd src/
      ./redis-cli
      ```

  * ```Ubuntu```

    * 使用```apt```下载安装：
      
      ```bash
      sudo apt update
      sudo apt install redis-server
      ```

    * 启动服务：

      ```bash
      redis-server
      ```

    * 启动客户端：

      ```bash
      redis-cli
      ```

  * ```MacOS```

    * 使用```brew```下载安装：

      ```bash
      brew install redis
      ```

    * 启动服务：

      ```bash
      redis-server
      ```

    * 启动客户端：

      ```bash
      redis-cli
      ```

  * ```Docker```（快速安装）
    
    * [```dockerhub```选择合适版本](https://hub.docker.com/_/redis/tags)
    * 拉取选定版本的镜像
      
      ```bash
      # version为选定的镜像版本
      docker pull redis:${version}
      ```
    
    * 运行容器

      ```bash
      # version为选定的镜像版本
      docker run --name redis -d -p 6379:6379 redis:${version}
      ```

    * 进入容器并链接```Redis```服务

      ```bash
      docker exec -it redis /bin/bash
      redis-cli
      ```

> Redis 命令

> Redis 高级功能

> 参考文献

* [Redis 教程](https://redis.net.cn/tutorial/3501.html)
* [Redis 菜鸟](https://www.runoob.com/redis/redis-tutorial.html)
* [Redis 官网](https://redis.io/)

