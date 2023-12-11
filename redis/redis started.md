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
  
* 配置

  * 配置文件（```redis.conf```）位于```Redis```安装目录下，可通过```CONFIG```命令查看配置项：
    
    ```bash
    CONFIG GET CONFIG_SETTING_NAME 
    # CONFIG GET loglevel
    # CONFIG GET *
    ```

    编辑配置项：

    ```bash
    CONFIG SET CONFIG_SETTING_NAME NEW_CONFIG_VALUE
    # CONFIG SET loglevel "notice"
    ```

  * 基本参数说明：

    | 序号 | 配置项 | 说明 |
    | :--- | :--- | :--- | 
    | 1 | daemonize no | Redis 默认不以守护进程的方式运行，可通过该配置项修改，使用 yes 启用守护进程（Windows 不支持守护线程的配置为 no ） |
    | 2 | pidfile /var/run/redis.pid | 当 daemonize yes 时，Redis 默认会将 pid 写入 /var/run/redis.pid，可通过 pidfile 指定路径 |
    | 3 | port 6379 | 指定 Redis 服务监听的端口 |
    | 4 | bind 127.0.0.1 | 指定绑定的主机地址 |
    | 5 | timeout 300 | 指定客户端等待时间，若超过该时间则关闭连接，若指定为0则表示关闭该功能 |
    | 6 | loglevel notice | 指定日志级别，共支持四个级别：debug、verbose、notice、warning，默认为 notice |
    | 7 | logfile stdout | 指定日志文件，默认为标准输出，若为标准输出且 daemonize yes ，日志将输出至 /dev/null |
    | 8 | databases 16 | 指定数据库的数量，默认为0 |
    | 9 | save seconds changes | 指定多长时间内有多少次更新操作，就将数据同步至数据文件中，可多条件配合，默认配置文件中提供三个条件：<br> save 900 1 <br> save 300 10 <br> save 60 10000 |
    | 10 | rdbcompression yes | 指定存储至本地数据库时是否压缩数据，默认为 yes，Redis 采用 LZF 压缩，若为节省 CPU 时间，可关闭该选项，但会导致数据库文件庞大 |
    | 11 | dbfilename dump.rdb |  |  |
    | 12 | dir ./ |  |  |
    | 13 | slaveof <masterip> <masterport> |  |  |
    | 14 | masterauth <master-password> |  |  |
    | 15 | requirepass foobared |  |  |
    | 16 | maxclients 128 |  |  |
    | 17 | maxmemory <bytes> |  |  |
    | 18 | appendonly no |  |  |
    | 19 | appendfilename appendonly.aof |  |  |
    | 20 | appendfsync everysec |  |  |
    | 21 | vm-enabled no |  |  |
    | 22 | vm-swap-file /tmp/redis.swap |  |  |
    | 23 | vm-max-memory 0 |  |  |
    | 24 | vm-page-size 32 |  |  |
    | 25 | vm-pages 134217728 |  |  |
    | 26 | vm-max-threads 4 |  |  |
    | 27 | glueoutputbuf yes |  |  |
    | 28 | hash-max-zipmap-entries 64 <br> hash-max-zipmap-value 512 |  |  |
    | 29 | activerehashing yes |  |  |
    | 30 | include /path/to/local.conf |  |  |

  * [各版本官方配置文件](https://redis.io/docs/management/config/)

> Redis 命令

> Redis 高级功能

> 参考文献

* [Redis 教程](https://redis.net.cn/tutorial/3501.html)
* [Redis 菜鸟](https://www.runoob.com/redis/redis-tutorial.html)
* [Redis 官网](https://redis.io/)

