## redis 应用场景

> 布隆过滤器

* 工作原理：
  
  布隆过滤器是一个高空间利用率的概率性数据结构，由二进制向量（数组）和若干个随机映射函数（哈希函数）两部分组成。工作流程如下：

    * 添加元素。当添加```Key```（布隆过滤器）时，会使用不同的哈希函数对元素值进行哈希计算得到多个哈希值，每个哈希值计算出整数索引值，将该索引值与位数组长度做取余运算得出位数组位置，将该位置的值设置为1。通过多个哈希函数所计算出的多个位数组位置上的多个值组合起来，代表添加的元素。

    * 判断元素。首先对元素进行添加时的哈希运算获取位数组的位置，通过判断每个位置是否都为1，判断元素是否存在，若其中一个为0则不存在，若都为非0则可能不存在（可能不存在的原因是因为哈希碰撞，这是被允许的，故存在错误率概念，若希望减少碰撞，则声明布隆过滤器时需设置低错误率，同时扩大位数组容量）。

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2024-01-21_21-56-01.png)

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

* 客户端安装与使用。[以```SpringBoot```为例](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20BloomFilter.md)

> 分布式锁

* 分布式锁是控制分布式系统不同进程共同访问共享资源的一种锁的实现。不同的系统或同一系统的不同主机之间共享某个临界资源，需要互斥来防止彼此干扰以确保一致性。分布式锁应该有这些特征：

  * 互斥性：任意时刻，有且只有一个客户端能持有锁。
  * 锁超时释放：持有锁超时时可释放，防止死锁。
  * 可重入性：一个线程持有锁后可再次对其请求加锁。
  * 高性能与高可用：加锁和解锁开销需尽可能低，同时保证高可用。
  * 安全性：锁只能被持有的客户端删除，不能被其他客户端删除。

* 分布式锁实现原理使用以下基本命令：
  
  * ```SETNX key val```：仅当```key```不存在时设置```val```字符串且返回1；若```key```存在时设置失败且返回0。
  * ```EXPIRE key timeout```：为```key```设置超时时间，单位为秒，超过该时间锁则自动释放，避免死锁。
  * ```DEL key```：删除```key```。

    使用```SETNX```与```EXPIRE```命令实现加锁（由于原子性问题，这两条命令需在```LUA```脚本中使用或使用命令```SET key value [expiration EX seconds|PX milliseconds] [NX|XX]```代替）；使用```DEL```命令实现解锁。

* 分布式锁的常见实现：

  * 对于```Redis```单机部署场景，常用```LUA```脚本使用```SETNX```、```EXPIRE```、```GET```以及```DEL```命令实现。
  * 对于```Redis```集群部署场景，常用```Redisson```框架实现。

    以```SpringBoot```为例，上诉两种实现方式可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Lock.md)。对于单机部署可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/redis/redis%20started.md)；对于集群部署可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/redis/Use%20docker-compose%20deploy%20redis%20cluster%20server.md)。

> 缓存

* 在实际业务场景中，```Redis```一般与其他数据库（如```Mysql```）配合使用，用于减轻后端数据库的压力。```Redis```通常将经常查询的数据缓存起来，如热点数据，当用户访问数据时，若缓存中存在数据则直接返回，若不存在则查询数据库并将数据缓存起来，最后将数据返回：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2024-03-18_11-01-12.png)

  将```Redis```作为数据库的缓存过程中，可能会出现常见的问题：

    * 缓存穿透：指查询某个不存在的数据（缓存中不存在数据库中也不存在）时数据库返回空对象代表查询失败，当这类查询请求非常多之时容易对数据库造成很大压力甚至崩溃的现象。为了避免缓存穿透，常见的解决方案有：

      * 缓存空对象：当数据库返回空对象时缓存起来，同时设置过期时间。这种做法也会存在一些问题，缓存空对象会浪费缓存空间。

      * 缓存前置添加布隆过滤器：若上述的布隆过滤器原理可知，布隆过滤器判定不存在的数据那么就一定不存在，利用这一特性可以防止缓存穿透。使用缓存过滤器时需将热点数据进行缓存预热（系统启动时，提前将相关的数据加载到缓存中）：

        ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/202403181126796.png)

    * 缓存击穿：指查询的数据缓存不存在但数据库存在（一般由```key```过期导致），某个时刻这个```key```突然过期失效致使大量并发请求进入后端数据库导致其压力瞬间增大的现象。为了避免缓存击穿，常见的解决方案有：

      * 修改过期时间，可将热点数据设置永不过期。

      * 使用分布式锁：在进行后端数据库查询前进行加锁且在查询结果缓存后解锁。

    * 缓存雪崩：指缓存中大批量的```key```同时过期失效且数据访问庞大从而导致后端数据库压力瞬间爆炸甚至服务挂掉的现象。它与缓存击穿不同的是，缓存击穿是在并发量特别大且某个```key```突然过期失效，而缓存雪崩则是大批量```key```同时过期失效。为了避免缓存击穿，常见的解决方案有：

      * 修改过期时间，可以设置不同的```key```随机过期时间或者热点数据设置永不过期。

* ```Redis```缓存常见实现：

  * ```lettuce```实现
    
    * [单例模式](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Standalone.md)
    * [主从复制模式](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Master-Slave.md)
    * [哨兵模式](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Sentinel.md)
    * [集群模式](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Cluster.md)

  * [```redissson```实现](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Intergrates%20Redisson.md)
  * [框架```SpringCache```实现](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20SpringCache.md)

> 排行榜

* 排行榜有许多应用场景，如博客热搜榜以及礼物贡献实时榜等。它们有共同的特点为榜上的条目是唯一的（不重复）且按指定系数排序。```redis```的有序集合（```zset```）适合该应用场景，它是```String```类型元素的集合且不允许重复的成员，每个成员都会关联一个```double```类型的分数，有序集合可根据这个分数进行排序。排行榜可用到的几个基本命令：
  
  ```bash
  # 将一个或多个元素添加值有序集合，若元素已存在则更新其分数值
  # ZADD KEY_NAME SCORE1 VALUE1.. SCOREN VALUEN
  ZADD blog_hot 100 blog_1 1000 blog_2

  # 有序集合中对指定成员的分数加上增量
  # INCRBY KEY_NAME INCR MEMBER
  INCRBY blog_hot 1 blog_2

  # 获取有序集合中指定成员的分数值
  # ZSCORE KEY_NAME MEMBER
  ZSCORE blog_hot blog_2

  # 获取有序集合(按分数递增排序)中指定索引区间的成员
  # ZRANGE KEY_NAME INDEX_START INDEX_END [WITHSCORES]
  ZRANGE blog_hot 0 -1 WITHSCORES

  # 获取有序集合(按分数递减排序)中指定索引区间的成员
  # ZREVRANGE KEY_NAME INDEX_START INDEX_END [WITHSCORES]
  ZREVRANGE blog_hot 0 -1 WITHSCORES
  ```

  排行榜有序集合内的成员一般为成员的唯一标识，如博客```id```，这时我们可通过哈希类型存储博客详细信息，常使用```HMSET```命令：

  ```bash
  # 在哈希表key同时设置多个键值对field-value
  # HMSET KEY_NAME FIELD1 VALUE1 ...FIELDN VALUEN
  HMSET blog_hot:blog_1 title redis3 author redis3
  ```

  一般排行榜都存在时效性，如周榜、月榜等，常使用```EXPIRE```命令：

  ```bash
  # 设置Key过期时间，单位为秒
  # EXPIRE KEY_NAME SEC
  EXPIRE blog_hot 1711987199
  ```

> 分布式Session

* ```Http```协议是无状态的，客户端（浏览器）只需向服务器请求资源，服务器向客户端返回资源，其之间不记录彼此历史信息，每次请求都是独立的。实际上客户端（浏览器）与服务器之间使用```Socket```嵌套字进行通信，当服务器将请求结果返回给客户端（浏览器）后会关闭当前的```Socket```连接。但在许多```Web```应用场景中需维护用户态（用户是否登录），此时出现了保持```Http```连接状态的技术，一个是```Cookie```（浏览器实现方案），另一个是```Session```（服务器实现方案）。```Cookie + Session```是单机经典的实现方案，对于分布式集群也在其基础上做出扩展，如：

  * ```Session Stick```：将客户端（浏览器）的每次请求都转发至同一台服务器，这需负载均衡器根据每次请求的会话（```SessionId```）来进行请求转发。
  * ```Session Replication```：```Web``服务器之间增加了会话数据同步的功能，各个服务器之间通过同步保证不同```Web``服务器之间的```Session```数据的一致性。
  * ```Cookie Base```：将```Session```数据放在```Cookie```里，访问```Web```服务器时，再由```Web```服务器生成对应的```Session```数据。
  * ```Session Redis```：使用```Redis```将集群中的所有```Session```集中存储起来：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2024-04-05_23-24-44.png)

    ```SpringBoot```集成分布式```Session Redis```可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Session.md)。

  还可以使用无状态的```JWT```方案。（后续更新...）


> 参考文献

* [5 分钟搞懂布隆过滤器，亿级数据过滤算法你值得拥有！](https://juejin.cn/post/6844904007790673933)
* [记一篇REDIS布隆过滤器的使用](https://zhuanlan.zhihu.com/p/89883126)
* [Redis布隆过滤器（原理+图解）](https://c.biancheng.net/redis/bloom-filter.html)
* [Redis 布隆（Bloom Filter）过滤器原理与实战](https://www.51cto.com/article/704389.html)
* [（Redis使用系列） Springboot 在redis中使用BloomFilter布隆过滤器机制 六](https://developer.aliyun.com/article/951745)
* [SpringBoot 中使用布隆过滤器 Guava、Redission实现](https://juejin.cn/post/7136214205618716709)
* [Redis分布式锁应用（实现+原理）](https://c.biancheng.net/redis/distributed-lock.html)
* [七种方案！探讨Redis分布式锁的正确使用姿势](https://juejin.cn/post/6936956908007850014)
* [一口气讲完了 Redis 常用的数据结构及应用场景](https://xie.infoq.cn/article/c742001e651de0198d7f8a5d7)
* [分布式系统 - 分布式会话及实现方案](https://pdai.tech/md/arch/arch-z-session.html)