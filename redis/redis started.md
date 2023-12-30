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
    | 11 | dbfilename dump.rdb | 指定本地数据库文件名，默认为dump.rdb |
    | 12 | dir ./ | 指定本地数据库存放目录 |
    | 13 | slaveof masterip masterport | 当主机为 slave 服务时，指定所属 master 服务的 IP 端口。在 Redis 启动时，自动从 master 数据同步 |
    | 14 | masterauth master-password | 当主机为 slave 服务且 master 已设置密码保护时，指定连接 master 服务的密码 |
    | 15 | requirepass foobared | 指定 Redis 连接密码，若指定则客户端在连接 Redis服务时需通过 AUTH password 命令提供密码，默认关闭 |
    | 16 | maxclients 128 | 指定 Redis 同一时间最大客户连接数，默认为无限制。最大客户连接数为 Redis 进程可打开的最大文件描述符数，若指定为0则无限制，当客户连接数超过限制，Redis 会关闭新连接并向客户端返回 max number of clients reached 错误信息 |
    | 17 | maxmemory bytes | 指定 Redis 最大内存。Redis 启动时将数据加载在内存中，达到限制后会先尝试删除已过期或即将到期的 Key，若在此处理后仍达到最大内存限制，将无法写入操作，当仍可进行读操作。Redis 新的 vm 机制，会将 Key 保存在内存中，Value 保存在 swap 区 |
    | 18 | appendonly no | 指定是否在每次更新操作后进行日志记录，默认为 no。 若不开启可能会导致在断电后一段时间内的数据丢失，因为默认情况下 Redis 是异步将数据写入磁盘|
    | 19 | appendfilename appendonly.aof | 指定更新日志文件名，默认为 appendonly.aof |
    | 20 | appendfsync everysec | 指定更新日志策略，共有3个可选值：<br> no：表示等待操作系统进行数据缓存同步到磁盘（快） <br> always：表示每次更新操作后手动调用 fsync() 将数据写入磁盘（慢，安全）<br> everysec：表示每秒同步一次（折中，默认值） |
    | 21 | vm-enabled no | 指定是否启用虚拟内存机制，默认为 no |
    | 22 | vm-swap-file /tmp/redis.swap | 指定虚拟内存文件路径，默认为 /tmp/redis.swap |
    | 23 | vm-max-memory 0 | 指定最大虚拟内存，默认为0。当指定为0时，Redis 上所有的 value 都保存在磁盘中 |
    | 24 | vm-page-size 32 | 指定虚拟内存文件页面大小，默认为32。Redis swap 文件分成多个 page，一个对象可保存在多个 page 上。该设置需根据存储数据的大小来指定，建议若存储小对象则指定32或64 bytes，若存储大对象则可设置更大。 |
    | 25 | vm-pages 134217728 | 指定虚拟内存文件页数。由于页表（表示页面空闲或使用的 bitmap）放在内存中，故磁盘上每8个 pages 将 消耗1 byte 的内存 |
    | 26 | vm-max-threads 4 | 指定访问虚拟内存文件的最大线程数，默认值为4.建议不超过机器的核心数，若设置为0则表示对文件的操作是串行的，可能会造成较长时间的延迟 |
    | 27 | glueoutputbuf yes | 指定在向客户端响应时是否将较小的包合并一个包发送，默认为 yes |
    | 28 | hash-max-zipmap-entries 64 <br> hash-max-zipmap-value 512 | 指定在超过一定数量或最大元素超过某一临界值时，采用特殊的哈希算法 |
    | 29 | activerehashing yes | 指定是否启动重置哈希，默认为 yes |
    | 30 | include /path/to/local.conf | 指定包含其他的配置文件。同一个主机上多个 Redis 实例可使用同一份公共配置文件，各个实例又可拥有自身特定的配置文件 |

  * [各版本官方配置文件](https://redis.io/docs/management/config/)

> Redis 命令

* ```Key```，用于管理 ```redis```的键，基本语法如下：
  
  ```bash
  COMMAND KEY_NAME
  ```

  没有直接创建```Key```的命令，一般都伴随着```Value```的创建生成，常见的有创建字符串类型的```Value```：

  ```bash
  SET KEY_NAME KEY_VALUE
  # SET name redis
  # OK
  ```

  基本的常用命令：
    
    * ```DEL```，用于删除已存在的```Key```，不存在的```Key```忽略：
      
      ```bash
      DEL KEY_NAME
      # DEL name
      ```
    
    * ```DUMP```，用于序列化指定```Key```，并返回序列化值：

      ```bash
      DUMP KEY_NAME
      # DUMP name
      ```

    * ``EXISTS``，用于检查指定```Key```是否存在：

      ```bash
      EXISTS KEY_NAME
      # EXISTS name
      ```

    * ```EXPIRE```，设置```Key```过期时间，单位为秒：

      ```bash
      EXPIRE KEY_NAME SEC
      # EXPIRE name 6000
      ```

    * ```EXPIREAT```，设置```Key```过期时间，单位为```UNIX```时间戳秒：

      ```bash
      EXPIREAT KEY_NAME TIMESTAMP_SEC
      # EXPIREAT name 1702655999
      ```

    * ```PEXPIRE```，设置```Key```过期时间，单位为毫秒：

      ```bash
      PEXPIRE KEY_NAME MILLSEC
      # PEXPIRE name 6000000
      ```

    * ```PEXPIREAT```，设置```Key```过期时间，单位为```UNIX```时间戳毫秒：

      ```bash
      PEXPIREAT KEY_NAME TIMESTAMP_MILLSEC
      # PEXPIREAT name 1702655999000
      ```

    * ```KEYS```，查找符合指定模式的```Key```

      ```bash
      KEYS PATTERN
      # KEYS nam*
      ```

    * ```MOVE```，将当前数据库的```Key```移动至指定的数据库```db```：

      ```bash
      MOVE KEY_NAME DESTINATION_DATABASE
      # MOVE name 1
      ```

    * ```PERSIST```，移除指定```Key```的过期时间并持久化，使得```Key```永不过期：

      ```bash
      PERSIST KEY_NAME
      # PERSIST name 
      ```

    * ```PTTL```，返回指定```Key```的剩余过期时间，单位为毫秒：

      ```bash
      PTTL KEY_NAME
      # PTTL name
      ```

    * ```TTL```，返回指定```Key```的剩余过期时间，单位为秒：

      ```bash
      TTL KEY_NAME
      # TTL name
      ```

    * ```RANDOMKEY```，随机返回一个存在的```Key```：

      ```bash
      RANDOMKEY
      # RANDOMKEY
      ```

    * ```RENAME```，修改```Key```的名称，若```newKey```已存在，将使用```newKey```，原本```newKey```则丢失：

      ```bash
      RENAME KEY_NAME NEW_KEY_NAME
      # RENAME name name1
      ```

    * ```RENAMENX```，修改```Key```的名称，仅当```newKey```不存在时，将```Key```修改为```newKey```：
      

      ```bash
      RENAMENX KEY_NAME NEW_KEY_NAME
      # RENAMENX name name1
      ```

    * ```TYPE```，返回```Key```所存储的值的类型：

      ```bash
      TYPE KEY_NAME
      # TYPE name
      ```

* ```String```，用于存储```redis```的字符串类型的值，基本语法如下：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```SET```，指定```Key```的值：
      
      ```bash
      SET KEY_NAME VALUE
      # SET name redis
      ```

    * ```GET```，获取```Key```字符串类型的值：

      ```bash
      GET KEY_NAME
      # GET name
      ```

    * ```GETRANGE```，获取```Key```指定起始偏移量的子字符串的值：

      ```bash
      GETRANGE KEY_NAME START_OFFSET END_OFFSET
      # GETRANGE name 0 2
      ```

    * ```GETSET```，获取```Key```的字符串旧值并设置新值：

      ```bash
      GETSET KEY_NAME VALUE
      # GETSET name redis1
      ```

    * ```GETBIT```，获取```Key```的字符串值的二进制值的指定偏移量上的位（```bit```）：

      ```bash
      GETBIT KEY_NAME OFFSET
      # GETBIT name 2
      ```

    * ```MGET```，获取多个指定```Key```的多个字符串值：

      ```bash
      MGET KEY_NAME_1 KEY_NAME_2 .. KEY_NAME_N
      # MGET name name2
      ```

    * ```SETBIT```，指定或移除```Key```的字符串值的二进制值的指定偏移量上的位（```bit```）：

      ```bash
      SETBIT KEY_NAME OFFSET
      # SETBIT name 2 1
      ```

    * ```SETEX```，指定```Key```的值并设置过期时间，单位为秒：

      ```bash
      SETEX KEY_NAME TIMEOUT VALUE
      # SETEX name 60 redis
      ```

    * ```SETNX```，当```Key```不存在时指定```Key```的值：

      ```bash
      SETNX KEY_NAME VALUE
      ```

    * ```SETRANGE```，从指定偏移量开始，使用参数值将```Key```的值覆盖：

      ```bash
      SETRANGE KEY_NAME OFFSET VALUE
      # SETRANGE name 0 R
      ```

    * ```STRLEN```，获取```Key```存储的字符串值长度：

      ```bash
      STRLEN KEY_NAME
      # STRLEN name
      ```

    * ```MSET```，指定多个```Key-Value```：

      ```bash
      MSET KEY_NAME_1 VALUE_1 KEY_NAME_2 VALUE_2
      # MSET name redis name1 redis2
      ```

    * ```MSETNX```，当```Key```不存在时，指定多个```Key-Value```：

      ```bash
      MSETNX KEY_NAME_1 VALUE_1 KEY_NAME_2 VALUE_2
      # MSETNX name redis name1 redis2
      ```

    * ```PSETEX```，指定```Key```的值并设置过期时间，单位为毫秒：

      ```bash
      PSETEX KEY_NAME TIMEOUT VALUE
      # PSETEX name 60000 redis
      ```

    * ```INCR```，将```Key```中的数字值增一，若```Key```不存在，则先初始化数字值为0，再执行```INCR```操作；若值包含错误类型或不为数字值类型，将返回一个错误。数字值限制在64位有符号数字表示之内：

      ```bash
      INCR KEY_NAME
      # INCR name
      ```

    * ```INCRBY```，将```Key```中的数字值增指定数值：

      ```bash
      INCRBY KEY_NAME INCR_AMOUNT
      # INCR name 50
      ```

    * ```INCRBYFLOAT```，将```Key```中的数字值增指定浮点型数值：

      ```bash
      INCRBYFLOAT KEY_NAME INCR_AMOUNT
      # INCRBYFLOAT name 50.02
      ```

    * ```DECR```，将```Key```中的数字值减一：

      ```bash
      DECR KEY_NAME
      # DECR name
      ```

    * ```DECRBY```，将```Key```中的数字值减指定数值：

      ```bash
      DECRBY KEY_NAME DECREMENT_AMOUNT
      # DECRBY name 10
      ```

    * ```APPEND```，若```Key```存在且为字符串，将值追加至尾部；若```Key```不存在则直接设值：

      ```bash
      APPEND KEY_NAME NEW_VALUE
      # APPEND name hello
      ```

* ```Hash```，，用于存储```redis```的键值对类型的值（```String```类型的```field```和```value```的映射表），基本语法如下：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```HDEL```，删除哈希表```Key```一个或多个字段：

      ```bash
      HDEL KEY_NAME FIELD1.. FIELDN
      # HDEL person_1 name age
      ```

    * ```HEXISTS```，查看哈希表```Key```中是否存在指定字段：

      ```bash
      HEXISTS KEY_NAME FIELD_NAME
      # HEXISTS person_1 name
      ```

    * ```HGET```，获取哈希表```Key```中指定字段的值：

      ```bash
      HGET KEY_NAME FIELD_NAME 
      # HGET person_1 name
      ```

    * ```HGETALL```，获取哈希表```Key```中所有字段的值：

      ```bash
      HGETALL KEY_NAME
      # HGETALL person_1
      ```

    * ```HINCRBY```，为哈希表```Key```指定字段的整形值加上整形增量：

      ```bash
      HINCRBY KEY_NAME FIELD_NAME INCR_BY_NUMBER
      # HINCRBY person_1 age 1
      ```

    * ```HINCRBYFLOAT```，为哈希表```Key```指定字段的浮点型值加上浮点型增量：

      ```bash
      HINCRBYFLOAT KEY_NAME FIELD_NAME INCR_BY_NUMBER
      # HINCRBYFLOAT person_1 weight 3.2
      ```

    * ```HKEYS```，获取哈希表```Key```中所有字段：

      ```bash
      HKEYS KEY_NAME
      # HKEYS person_1
      ```

    * ```HLEN```，获取哈希表```Key```中所有字段的数量：

      ```bash
      HLEN KEY_NAME
      # HLEN person_1
      ```

    * ```HMGET```，获取哈希表```Key```中多个指定字段的多个值：

      ```bash
      HMGET KEY_NAME FIELD1...FIELDN
      # HMGET person_1 name age
      ```

    * ```HMSET```，在哈希表```key```同时设置多个键值对（```field-value```）：
      
      ```bash
      HMSET KEY_NAME FIELD1 VALUE1 ...FIELDN VALUEN
      # HMSET person_1 name redis age 18
      ```

    * ```HSET```，将哈希表```key```中的字段```field```的值设置为```value```：
    
      ```bash
      HSET KEY_NAME FIELD VALUE
      # HSET person_1 name redis
      ```

    * ```HSETNX```，哈希表```key```中，当字段```field```不存在时，将字段```field```的值设置为```value```：

      ```bash
      HSETNX KEY_NAME FIELD VALUE
      # HSETNX person_1 name redis
      ```

    * ```HVALS```，获取哈希表```Key```中所有字段值：

      ```bash
      HVALS KEY_NAME
      # HVALS person_1
      ```

    * ```HSCAN```，迭代[渐进式迭代]哈希表```Key```的键值对：

      ```bash
      HSCAN KEY_NAME CURSOR [MATCH PATTERN] [COUNT NUMBER]
      # HSCAN person_1 0 MATCH "re"
      ```

      参数```COUNT```生效的场景为：键数大于512或值的长度大于64（本质上将```ziplist```类型降级为```dict```类型），具体可参考[这里](https://blog.csdn.net/zjcsuct/article/details/108138876)或[官方说明](https://redis.io/commands/hscan/)。

* ```List```，用于存储简单的字符串列表，按照插入顺序排序，元素可从头部（左边）或尾部（右边）添加，基本语法如下：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```BLPOP```，弹出多个```Key```的列表第一个元素，若列表中不存在元素则会阻塞队列等待超时（单位为秒）或发现可弹出元素为止：

      ```bash
      BLPOP KEY_NAME1 ... KEY_NAMEN TIMEOUT
      # BLPOP name 10
      ```

    * ```BRPOP```，弹出多个```Key```的列表最后一个元素，若列表中不存在元素则会阻塞队列等待超时（单位为秒）或发现可弹出元素为止：

      ```bash
      BRPOP KEY_NAME1 ... KEY_NAMEN TIMEOUT
      # BRPOP name 10
      ```

    * ```BRPOPLPUSH```，弹出一个列表的尾部元素添加至另一个列表的头部，若列表中不存在元素则会阻塞队列等待超时（单位为秒）或发现可弹出元素为止：
    
      ```bash
      BRPOPLPUSH KEY_NAME KEY_NAME1 TIMEOUT 
      # BRPOPLPUSH name name1 10
      ```

    * ```LINDEX```，通过索引获取列表中的元素。可使用负数表示，如-1表示倒数第一个元素，-2表示倒数第二个元素，以此类推：

      ```bash
      LINDEX KEY_NAME INDEX_POSITION
      # LINDEX name 0
      ```

    * ```LINSERT```，在指定元素前或后插入新元素。若```Key```不存在则视为空列表，不做操作；若```Key```存在且指定元素不存在，不做操作；若·```Key```存在且类型不为列表返回错误：

      ```bash
      LINSERT KEY_NAME BEFORE[AFTER] EXISTING_VALUE NEW_VALUE
      # LINSERT name BEFORE redis redis 
      ```

    * ```LLEN```，返回列表的长度。若```Key```不存在则解释为空返回0；若```Key```存在且类型不为列表则返回错误：

      ```bash
      LLEN KEY_NAME
      # LLEN name
      ```

    * ```LPOP```，弹出列表第一个元素：

      ```bash
      LPOP KEY_NAME
      # LPOP name
      ```

    * ```LPUSH```，将一个或多个值插入列表头部。若```Key```不存在则先创建再进行插入；若```Key```存在且类型不为列表则返回错误：

      ```bash
      LPUSH KEY_NAME VALUE1.. VALUEN
      # LPUSH name redis1 redis2
      ```

    * ```LPUSHX```，当前仅当```Key```存在时，将一个或多个值插入列表头部：

      ```bash
      LPUSHX KEY_NAME VALUE1.. VALUEN
      # LPUSHX name redis3
      ```

    * ```LRANGE```，获取列表指定区间的元素：

      ```bash
      LRANGE KEY_NAME START END
      # LRANGE name 0 -1
      ```

    * ```LREM```，移除列表中的与指定值相等的指定数量的元素：

      ```bash
      LREM KEY_NAME COUNT VALUE
      # LREM name 0 redis
      ```

      参数```COUNT```可以为负数（< 0），代表从列表尾部开始向头部搜索，移除与```VALUE```相等的元素，数量为```COUNT```的绝对值；可以为正数（> 0），代表从列表头部开始向尾部搜索，移除与```VALUE```相等的元素，数量为```COUNT```；也可以为零（= 0），移除所有与```VALUE```相等的元素。

    * ```LSET```，通过指定索引设置值：

      ```bash
      LSET KEY_NAME INDEX VALUE
      # LSET name 0 redis
      ```

    * ```LTRIM```，对列表中指定区间进行裁剪，保留区间内元素，移除区间外元素：

      ```bash
      LTRIM KEY_NAME START STOP
      # LTRIM name 1 -1
      ```

    * ```RPOP```，弹出列表最后一个元素：

      ```bash
      RPOP KEY_NAME
      # RPOP name
      ```

    * ```RPOPLPUSH```，弹出一个列表的尾部元素添加至另一个列表的头部：
    
      ```bash
      RPOPLPUSH KEY_NAME KEY_NAME1
      # RPOPLPUSH name name1
      ```

    * ```RPUSH```，将一个或多个值插入列表尾部。若```Key```不存在则先创建再进行插入；若```Key```存在且类型不为列表则返回错误：

      ```bash
      RPUSH KEY_NAME VALUE1.. VALUEN
      # RPUSH name redis1 redis2
      ```

    * ```RPUSHX```，当前仅当```Key```存在时，将一个或多个值插入列表尾部：

      ```bash
      RPUSHX KEY_NAME VALUE1.. VALUEN
      # RPUSHX name redis3
      ```

* ```Set```，用于存储字符串类型的无序集合，基础语法如下：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```SADD```，向集合添加一个或多个成员。若```Key```不存在则先创建```Key```后添加成员；若```Key```存在且类型不为无序集合则返回错误：

      ```bash
      SADD KEY_NAME VALUE1..VALUEN
      # SADD name redis redis1
      ```

    * ```SCARD```，获取集合的成员数量：
      
      ```bash
      SCARD KEY_NAME 
      # SCARD name
      ```

    * ```SDIFF```，获取指定集合间的差集：

      ```bash
      SDIFF KEY_NAME KEY_NAME1..KEY_NAMEN
      # SDIFF name1 name2
      ```

    * ```SDIFFSTORE```，将指定集合间的差集的结果存储在目标集合：

      ```bash
      SDIFFSTORE DESTINATION_KEY_NAME KEY_NAME1..KEY_NAMEN
      # SDIFFSTORE name name1 name2
      ```

    * ```SINTER```，获取指定集合间的交集：

      ```bash
      SINTER KEY_NAME KEY_NAME1..KEY_NAMEN
      # SINTER name1 name2
      ```

    * ```SINTERSTORE```，将指定集合间的交集的结果存储在目标集合：

      ```bash
      SINTERSTORE DESTINATION_KEY_NAME KEY_NAME1..KEY_NAMEN
      # SINTERSTORE name name1 name2
      ```

    * ```SISMEMBER```，判断指定成员是否属于集合成员：

      ```bash
      SISMEMBER KEY_NAME VALUE
      # SISMEMBER name redis
      ```

    * ```SMEMBERS```，获取集合的所有成员：

      ```bash
      SMEMBERS KEY_NAME
      # SMEMBERS name
      ```

    * ```SMOVE```，将指定成员从一个集合移动至另一个集合：

      ```bash
      SMOVE KEY_NAME1 KEY_NAME2 MEMBER
      # SMOVE name1 name2 redis1
      ```

    * ```SPOP```，弹出一个随机成员：

      ```bash
      SPOP KEY
      # SPOP name
      ```

    * ```SRANDMEMBER```，获取一个或多个随机成员：
    
      ```bash
      SRANDMEMBER KEY_NAME [COUNT]
      # SRANDMEMBER name 2
      ```

      ```COUNT```参数可以为正数，若小于集合基数则返回```COUNT```个成员，若大于等于集合基数则返回所有成员，返回的成员都各不相同；也可以为负数，返回```COUNT```绝对值的成员，返回的成员可能重复。

    * ```SREM```，移除集合一个或多个成员：

      ```bash
      SREM KEY_NAME MEMBER1..MEMBERN
      # SREM name redis redis1
      ```

    * ```SUNION```，获取指定集合间的并集：

      ```bash
      SUNION KEY_NAME KEY_NAME1..KEY_NAMEN
      # SUNION name1 name2
      ```

    * ```SUNIONSTORE```，将指定集合间的并集的结果存储在目标集合：

      ```bash
      SUNIONSTORE DESTINATION_KEY_NAME KEY_NAME1..KEY_NAMEN
      # SUNIONSTORE name name1 name2
      ```

    * ```SSCAN```，迭代集合的成员：

      ```bash
      SSCAN KEY_NAME CURSOR [MATCH PATTERN] [COUNT NUMBER]
      ```

      参数用法与```HSCAN```相似。

* ```Zset```，用于存储字符串类型的有序集合，每个成员都关联一个```double```类型的分数（数值可以是整数值或双精度浮点数），集合根据这个分数排序，基础语法如下：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```ZADD```，将一个或多个元素添加值有序集合，若元素已存在则更新其分数值：

      ```bash
      ZADD KEY_NAME SCORE1 VALUE1.. SCOREN VALUEN
      # ZADD name 1 redis1 2 redis2
      ```

    * ```ZCARD```，获取有序集合的成员数：

      ```bash
      ZCARD KEY_NAME
      # ZCARD name
      ```

    * ```ZCOUNT```，获取指定分数区间的有序集合的成员数：

      ```bash
      ZCOUNT KEY_NAME SCORE_START SCORE_END
      # ZCOUNT name 0 1
      ```

    * ```ZINCRBY```，有序集合中对指定成员的分数加上增量：

      ```bash
      INCRBY KEY_NAME INCR MEMBER
      # INCRBY name 1 redis
      ```

    * ```ZINTERSTORE```，将多个有序集合的交集结果存储在新的有序集合中：

      ```bash
      ZINTERSTORE DEST_KEY_NAME KEYSNUMBER KEY_NAME1 ..KEY_NAMEN [WEIGHTS weight [weight ...]] [AGGREGATE SUM|MIN|MAX]
      # ZINTERSTORE name3 2 name1 name2
      ```

    * ```ZLEXCOUNT```，获取指定字典区间1的有序集合的成员数：

      ```bash
      ZLEXCOUNT KEY_NAME MIN MAX
      # ZADD name 0 a 0 b 0 c 0 d 0 e
      # ZLEXCOUNT name [b [f
      ```

    * ```ZRANGE```，获取有序集合(按分数递增排序)中指定索引区间的成员：

      ```bash
      ZRANGE KEY_NAME INDEX_START INDEX_END [WITHSCORES]
      # ZRANGE name 0 -1
      ```

    * ```ZRANGEBYLEX```，获取有序集合(按分数递增排序)中指定字典区间的成员：

      ```bash
      ZRANGEBYLEX KEY_NAME MIN MAX [LIMIT off count]
      # ZADD name 0 a 0 b 0 c 0 d 0 e
      # ZRANGEBYLEX name [b [f
      ```

    * ```ZRANGEBYSCORE```，获取有序集合(按分数递增排序)中指定分数区间的成员：

      ```bash
      ZRANGEBYSCORE KEY_NAME MIN MAX [WITHSCORES] [LIMIT offset count]
      # ZADD name 1 a 2 b 3 c 4 d 5 e
      # ZRANGEBYSCORE name -inf +inf
      ```

    * ```ZRANK```，返回有序集合（按分数递增排序）中指定成员的索引：

      ```bash
      ZRANK KEY_NAME MEMBER
      # ZRANK name redis1
      ```

    * ```ZREM```，移除有序集合中的一个或多个成员：

      ```bash
      ZREM KEY_NAME MEMBER1 ..MEMBERN
      # ZREM name redis1 redis2
      ```

    * ```ZREMRANGEBYLEX```，移除有序集合中指定字典区间的所有成员：

      ```bash
      ZREMRANGEBYLEX KEY_NAME MIN MAX
      # ZADD name 0 aaaa 0 b 0 c 0 d 0 e 0 foo 0 zap 0 zip 0 ALPHA 0 alpha
      # ZREMRANGEBYLEX name [alpha [omega
      ```

    * ```ZREMRANGEBYRANK```，移除有序集合中指定索引区间的所有成员：

      ```bash
      ZREMRANGEBYRANK KEY_NAME START END
      # ZREMRANGEBYRANK name 0 -1
      ```

    * ```ZREMRANGEBYSCORE```，移除有序集合中指定分数区间的所有成员：

      ```bash
      ZREMRANGEBYSCORE KEY_NAME MIN MAX
      # ZREMRANGEBYSCORE name 0 1000
      ```

    * ```ZREVRANGE```，获取有序集合(按分数递减排序)中指定索引区间的成员：

      ```bash
      ZREVRANGE KEY_NAME INDEX_START INDEX_END [WITHSCORES]
      # ZREVRANGE name 0 -1
      ```

    * ```ZREVRANGEBYSCORE```，获取有序集合(按分数递减排序)中指定分数区间的成员：

      ```bash
      ZREVRANGEBYSCORE KEY_NAME MAX MIN [WITHSCORES] [LIMIT OFFSET COUNT]
      # ZADD name 1 a 2 b 3 c 4 d 5 e
      # ZREVRANGEBYSCORE name +inf -inf
      ```

    * ```ZREVRANK```，返回有序集合（按分数递减排序）中指定成员的索引：

      ```bash
      ZREVRANK KEY_NAME MEMBER
      # ZREVRANK name redis2
      ```

    * ```ZSCORE```，获取有序集合中指定成员的分数值：

      ```bash
      ZSCORE KEY_NAME MEMBER
      ```

    * ```ZUNIONSTORE```，将多个有序集合的并集结果存储在新的有序集合中：

      ```bash
      ZUNIONSTORE DEST_KEY_NAME KEYSNUMBER KEY_NAME1 ..KEY_NAMEN [WEIGHTS weight [weight ...]] [AGGREGATE SUM|MIN|MAX]
      # ZUNIONSTORE name3 2 name1 name2
      ```

    * ```ZSCAN```，迭代有序集合中的成员及其分数：

      ```bash
      ZSCAN KEY_NAME cursor [MATCH pattern] [COUNT count]
      ```

      参数用法与```HSCAN```相似。

* ```HyperLogLog```，用于基数统计。在输入元素的数量或体积非常庞大时，计算基数所需的空间总是固定且很小的：

  ```bash
  COMMAND KEY_NAME
  ```

  基本的常见命令：

    * ```PFADD```，添加指定元素：

      ```bash
      PFADD KEY_NAME ELEMENT1 ...ELEMENTN
      # PFADD name1 redis redis1 redis2 redis
      ```

    * ```PFCOUNT```，获取指定```HyperLogLog```的基数估算值：

      ```bash
      PFCOUNT KEY_NAME1 ...KEY_NAMEN
      # PFCOUNT name1 name2
      ```

    * ```PFMERGE```，将多个```HyperLogLog```合并成新的```HyperLogLog```：

      ```bash
      PFMERGE DEST_KEY_NAME SOURCE_KEY_NAME1 ...SOURCE_KEY_NAMEN
      # PFMERGE name3 name2 name1
      ```

      合并后的```HyperLogLog```的基数估算值是通过对所有给定```HyperLogLog```进行并集计算得出的。

* ```PUB/SUB```，发布订阅是一种消息通信模式，发送者（```PUB```）发送消息，订阅者（```SUB```）接收消息。客户端可订阅任意数量的频道（```CHANNEL```）：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2023-12-28_17-27-12.png)

  当新消息通过```PUBLISH```命令向频道发送，订阅的客户端则会收到消息：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2023-12-28_17-41-36.png)

  基础语法如下：

  ```bash
  COMMAND CHANNEL_NAME
  ```

  基本的常见命令：

    * ```PSUBSCRIBE```，订阅指定模式的一个或多个频道：
         
      ```bash
      PSUBSCRIBE CHANNEL_PATTERN1 ...CHANNEL_PATTERNN
      # PSUBSCRIBE ch*
      ```

      每个模式以*作为匹配符，比如 ```it*```匹配所有以```it```开头的频道(```it.news、it.blog、it.tweets```等等)

    * ```PUBSUB```，查看发布与订阅的系统状态：

      ```bash
      PUBSUB <SUBCMD> [ARG [ARG ...]]
      # PUBSUB CHANNELS
      ```

    * ```PUBLISH```，将消息发送至指定的频道：

      ```bash
      PUBLISH CHANNEL MESSAGE
      # PUBLISH ch1 "hello,ch1!"
      ```

    * ```PUNSUBSCRIBE```，退订指定模式的一个或多个频道：

      ```bash
      PUNSUBSCRIBE CHANNEL_PATTERN1 ...CHANNEL_PATTERNN
      # PUNSUBSCRIBE ch*
      ```

    * ```SUBSCRIBE```，订阅指定的一个或多个频道：

      ```bash
      SUBSCRIBE CHANNEL1 ...CHANNELN
      # SUBSCRIBE ch1 ch2
      ```

    * ```UNSUBSCRIBE```，退订指定的一个或多个频道：

      ```bash
      UNSUBSCRIBE CHANNEL1 ...CHANNELN
      # UNSUBSCRIBE ch1 ch2
      ```

* ```Transactions```，事务可一次性执行多个命令，事务从开始到执行会经历三个阶段（开始事物 -> 命令入队 -> 执行事务）。事务有三个特点：

  * 批量命令在```EXEC```命令前会一直入队缓存。
  * 批量命令间不具备原子性，在事务执行过程中，任意命令执行失败，之前的命令不会回滚，后续的命令会继续执行。
  * 事务执行过程中，其他客户端提交的命令请求不会插入到事务执行命令的队列中。

  基础语法如下：

  ```bash
  COMMAND
  ```

  基本的常见命令：

    * ```DISCARD```，取消事务，放弃事务块内所有命令的执行：

      ```bash
      DISCARD
      # DISCARD
      ```

    * ```EXEC```，执行事务块内所有的命令：

      ```bash
      EXEC
      # EXEC
      ```

    * ```MULTI```，标志事务块的开始：

      ```bash
      MULTI
      # MULTI
      ```

    * ```UNWATCH```，取消```WATCH```命令监视的所有```Key```：

      ```bash
      UNWATCH
      # UNWATCH
      ```

    * ```WATCH```，监视一个或多个```Key```，若这些```Key```在事务执行之前被改动，事务将被打断（```EXEC```命令执行返回```nil```表示事务没有成功）。换句话说，```WATCH```是```EXEC```的执行条件，当多个客户端同时执行```EXEC```事务时，```WACTH```充当乐观锁的角色。一旦```EXEC```被执行，所有的键将不会被监视：

      ```bash
      WATCH KEY_NAME1 ...KEY_NAMEN
      # WATCH lock lock_times
      ```

* ```SCRIPT```，```Redis```可使用```LUA```解释器（2.6版本支持内嵌的```LUA```环境）来执行脚本，  基础语法如下：

  ```bash
  COMMAND
  ```

  基本的常见命令：

    * ```EVAL```，执行```LUA```脚本：

      ```bash
      EVAL SCRIPT KEY_NUMBER KEY_NAME1 ...KEY_NAMEN ARG1 ...ARGN
      # EVAL "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}" 2 key1 key2 first second
      ```

      ```KEY_NAME1 ...KEY_NAMEN```表示脚本中所会使用的```Redis Key```，```LUA```中通过全局变量数组```KEYS```以基址的形式访问如```KEYS[1]、KEYS[2]...```

      ```ARG1 ...ARGN```表示脚本中会使用的附加参数，```LUA```中通过全局变量数组```ARGV```以基址的形式访问如```ARGV[1]、ARGV[2]...```

    * ```EVALSHA```，执行缓存在脚本缓存中指定```SHA1```校验码的```LUA```脚本：

      ```bash
      EVALSHA SHA1 KEY_NUMBER KEY_NAME1 ...KEY_NAMEN ARG1 ...ARGN
      # EVALSHA 232fd51614574cf0867b83d384a5e898cfd24e5a 2 key1 key2 first second
      ```
      
      参数```KEY_NAME1 ...KEY_NAMEN```与```ARG1 ...ARGN```同```EVAL```。

    * ```SCRIPT EXISTS```，根据```SHA1```校验码查看```LUA```脚本是否缓存：

      ```bash
      SCRIPT EXISTS SHA1 ...SHAN
      # SCRIPT EXISTS 232fd51614574cf0867b83d384a5e898cfd24e5a
      ```

    * ```SCRIPT FLUSH```，移除缓存中所有```LUA```脚本：

      ```bash
      SCRIPT FLUSH
      # SCRIPT FLUSH
      ```

    * ```SCRIPT KILL```，杀死当前正在运行的```LUA```脚本（当且仅当这个脚本未进行任何写操作时生效），脚本被杀死后执行这个脚本的客户端会从```EVAL```或```EVALSHA```命令的阻塞中退出并返回一个错误。

    * ```SCRIPT LOAD```，将```LUA```脚本缓存在脚本缓存中并返回```SHA1```校验码，缓存成功后并不立即执行：

      ```bash
      SCRIPT LOAD LUA_SCRIPT
      # SCRIPT LOAD script
      ```

* ```Connection```，用于连接```redis```服务：

  ```bash
  COMMAND
  ```

  基本的常见命令：

    * ```AUTH```，检测指定密码是否与配置文件所配置的相同：

      ```bash
      AUTH PASSWORD
      # AUTH mypassword
      ```

    * ```ECHO```，打印指定字符串：

      ```bash
      ECHO STR
      # ECHO redis
      ```

    * ```PING```，检测服务是否正常运行，是则返回```PONG```，否则返回连接超时：

      ```bash
      PING
      # PING
      ```

    * ```QUIT```，关闭当前客户端与```redis```服务的连接“

      ```bash
      QUIT
      # QUIT
      ```

    * ```SELECT```，切换至指定索引的数据库，默认为0:

      ```bash
      SELECT INDEX
      # SELECT 1
      ```

> Redis 高级功能

> 参考文献

* [Redis 教程](https://redis.net.cn/tutorial/3501.html)
* [Redis 菜鸟](https://www.runoob.com/redis/redis-tutorial.html)
* [Redis 官网](https://redis.io/)

