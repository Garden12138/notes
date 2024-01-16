## redis 应用场景

> 布隆过滤器

* 服务端安装与使用。在```Redis4.0```后，布隆过滤器才作为插件正式使用，需单独安装：

  * 布隆过滤器插件（```redisbloom.so```）的生成：

    ```bash
    # 方式一：下载源码并编译（待验证）
    # 下载地址：
    https://github.com/RedisBloom/RedisBloom
    # 解压文件并进入目录
    unzip RedisBloom-master.zip
    cd RedisBloom-master
    # 执行编译命令，生成插件文件
    make
    # 方式二：运行redislabs/rebloom测试容器，拷贝插件
    docker run --name redisbloom-test -d redislabs/rebloom:latest 
    docker cp redisbloom-test:/usr/lib/redis/modules/redisbloom.so . && docker stop redisbloom-test && docker rm redisbloom-test
    ```

  * ```docker```安装：

    ```bash
    # 拉取集成布隆过滤器插件的镜像
    docker pull redislabs/rebloom:latest

    # 运行集成布隆过滤器插件的容器，挂载文件redis.conf为配置文件，挂载目录rdb为数据持久化目录，挂载目录exp为扩展模块目录
    docker run \
            --name redisbloom \
            -d \
            -v /data/redis/redis.conf:/etc/redis/redis.conf \
            -v /data/redis/rdb:/data \
            -v /data/redis/exp:/exp \
            -p 6379:6379 \
            redislabs/rebloom:latest \
            redis-server /etc/redis/redis.conf --appendonly yes

    # 进入容器，测试布隆过滤器是否可正常使用
    docker exec -it redis-redisbloom /bin/bash
    root@aaa0e92b4b1f:/data# redis-cli
    127.0.0.1:6379> bf.add name redis1
    (integer) 1
    ```

    上述```docker```安装方式适用于运行新的```redis```服务容器的场景。针对运行中的```redis```服务容器：

    ```bash
    # 拷贝插件文件至扩展模块挂载目录
    cp redisbloom.so /data/redis/exp/
    # 编辑配置文件，新增加载布隆过滤器插件配置
    vi /data/redis/redis.conf
    loadmodule /exp/redisbloom.so
    # 重启容器
    docker restart redis
    ```

  * ```linux```安装：

    ```bash
    # 拷贝至指定目录
    cp redisbloom.so /usr/local/redis/bin/redisbloom.so
    # 编辑配置文件，新增加载布隆过滤器插件配置
    vi /${path}/redis.conf
    loadmodule /usr/local/redis/bin/redisbloom.so
    # 重启服务
    sudo /etc/init.d/redis-server restart
    ```

  * 常用命令使用：

    | 序号 | 命令 | 说明 |
    | :--- | :--- | :--- | 
    | 1 | BF.ADD {key} {element} | 添加一个元素至布隆过滤器 |
    | 2 | BF.EXISTS {key} {element} | 判断元素是否存在布隆过滤器 |
    | 3 | BF.MADD {key} {elements} | 添加多个元素至布隆过滤器 |
    | 4 | BF.MEXISTS {key} {elements} | 判断多个元素是否存在布隆过滤器 |
    | 5 | BF.RESERVE {key} {error_rate} {capacity} [EXPANSION {expansion}] [NONSCALING] | 手动创建错误率为{error_rate}、容量为{capacity}的布隆过滤器。选项EXPANSION可设置当数据达到满容量后自动扩容的倍数（默认为2）；选项NONSCALING可设置当数据达到满容量后不自动扩容 |

      