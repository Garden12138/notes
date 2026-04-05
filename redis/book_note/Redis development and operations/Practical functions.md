## 小功能大用处

### 慢查询分析

* 定义

  * ```Redis```命令的生命周期通常分为发送命令、命令排队、命令执行、返回结果四个部分，慢查询只统计“命令执行”这个生命周期的时间，若出现慢查询则记录命令日志。因此，若没有慢查询记录，并不代表客户端没有超时问题，还有可能是网络传输或命令排队超时。由于```Redis```采用单线程架构，慢查询会导致其他命令级联阻塞。


* 慢查询两个关键配置参数

  * ```slowlog-log-slower-than```：设置慢查询的执行时间阈值，单位为微秒，默认值为10000微秒（10毫秒）。若设置为0，会记录所有命令；若设置小于0，则不记录任何命令。

  * ```slowlog-max-len```：设置慢查询日志的最大长度。若超过最大长度，则会自动删除最早的命令。慢查询日志存放在```Redis```内部的一个列表中，该参数决定了列表最多存储多少条记录，当列表已满且有新的慢查询加入时，最早插入的记录会被移出（先进先出）。

* 慢查询管理命令

  * 设置慢查询的执行时间阈值命令：

    ```bash
    CONFIG SET slowlog-log-slower-than 10000
    ```

    将配置持久化到本地配置文件:

    ```bash
    CONFIG REWRITE slowlog-log-slower-than 10000
    ```

  * 设置慢查询日志的最大长度命令：

    ```bash
    CONFIG SET slowlog-max-len 1024
    ```

    将配置持久化到本地配置文件:

    ```bash
    CONFIG REWRITE slowlog-max-len 1024
    ```

  * 获取慢查询日志命令：

    ```bash
    SLOWLOG GET [n]
    ```

    获取慢查询日志列表，包括慢查询日志的标识```id```、发生时间戳、命令耗时、执行命令和参数。

  * 获取慢查询日志长度命令：

    ```bash
    SLOWLOG LEN
    ```

  * 清空慢查询日志命令：

    ```bash
    SLOWLOG RESET
    ```

* 最佳实践

  * 根据并发量调整阈值：对于高流量、高```OPS```的场景，建议将 ```slowlog-log-slower-than```设置为1毫秒。

  * 调大日志列表长度：线上建议将```slowlog-max-len```设置为1000以上，能有效防止因记录被剔除而丢失关键信息。

  * 定期持久化：由于慢查询日志存储在内存队列中且长度有限，建议定期执行 ```slowlog get```将日志持久化到```MySQL```等外部存储，并利用可视化界面进行监控分析。

  * 可使用可视化界面（如```CacheCloud```）进行监控分析。

### Redis Shell

* ```Redis Shell``` 是 ```Redis``` 安装目录下```src``` 或 ````/usr/local/bin``` 的可执行文件。在 ```Redis``` 的日常开发、调试和运维中起着至关重要的作用，能够完成启动/停止 ```Redis```、检测和修复持久化文件、以及检测 ```Redis``` 性能等任务。

* ```redis-cli```，是 ```Redis```的命令行客户端：

  * 重复与间隔执行：

    ```bash
    ## 重复执行多次命令
    redis-cli -r [times] [cmd]
    ## 每隔 interval 秒执行一次命令，总共重复执行多次命令。
    redis-cli -r [times] -i [interval] [cmd]
    ```

  * 标准输入读取：

    ```bash
    ## 将标准输入（stdin）读取数据作为最后一个参数，如echo "hello" | redis-cli -x set key
    redis-cli -x [cmd] [stdin]
    ```

  * 集群模式：

    ```bash
    ## 连接 Redis 集群节点
    redis-cli -c -h [host] -p [port]
    ```

  * 密码验证：

    ```bash
    ## 连接 Redis 节点并验证密码
    redis-cli -a [password] -h [host] -p [port]
    ```

  * 扫描与采样：

    ```bash
    ## 扫描指定模式的键，如：redis-cli --scan --pattern "user:*"
    redis-cli --scan --pattern [pattern]
    ## 扫描指定模式中内存占用大的的键，如：redis-cli --scan --pattern "session:*" | xargs redis-cli --bigkeys
    redis-cli --scan --pattern [pattern] | xargs redis-cli --bigkeys
    ```

  * 运维监控：

    ```bash
    ## 将客户端模拟成从节点，记录主节点的更新操作
    redis-cli --slave
    ## 请求生成并发送 RDB 持久化文件保存在本地，用于备份
    redis-cli --rdb /path/to/backup.rdb
    ## 实时获取 Redis 的重要增量统计信息
    redis-cli --stat
    ## 测量网络延迟
    redis-cli --latency
    ## 查看历史延迟
    redis-cli --latency-history
    ## 查看延迟分布
    redis-cli --latency-dist
    ```

  * 批量执行与脚本：

    ```bash
    ## 批量执行命令
    redis-cli --pipe

    SET key1 value1
    SET key2 value2
    SET key3 value3

    ## 使用文件批量执行命令
    cat commands.txt | redis-cli --pipe

    ## 使用lua脚本，如 
    ## redis-cli --eval "return redis.call('get', 'key1') + redis.call('get', 'key2')"
    ## redis-cli --eval "return redis.call('set', KEYS[1], ARGV[1])" key1 "new_value"
    redis-cli --eval [script] [param1] [param2]
    ```

  * 输出格式化：

    ```bash
    ## 原始字符格式输出
    redis-cli --raw [getcmd]
    ## 原始字节格式输出
    redis-cli --no-raw [getcmd]
    ```

* ```redis-server```：

  * 调试：

    ```bash
    ## 检测当前操作系统能否稳定地分配指定容量的内存，如：redis-server --test-memory 1024
    redis-server --test-memory [megabytes]
    ```

* ```redis-benchmark```，用于 ```Redis``` 基准性能测试：

  * 并发与总量：

    ```bash
    ## 并发连接数，如：redis-benchmark -c 100 -n 100000
    redis-benchmark -c [connections] -n [requests]
    ```

  * 精简输出：

    ```bash
    ## 显示每秒查询数（RPS
    redis-benchmark -q
    ```

  * 随机键测试：

    ```bash
    ## 插入随机后缀的键后测试，如：redis-benchmark -r 100000 -n 100000
    redis-benchmark -r [randomkeys] -n [requests]
    ```

  * 流水线优化：

    ```bash
    ## 流水线优化，每个请求包含多个命令，如：redis-benchmark -P 10
    redis-benchmark -P [pipeline]
    ```

  * 特定测试：

    ```bash
    ## 指定对某个 Redis 命令进行基准测试，如：redis-benchmark -t set,lpush,lpop
    redis-benchmark -t [command]
    ## 将基准测试结果保存到csv文件，如：redis-benchmar --csv > benchmark.csv
    redis-benchmark --csv > [filename]
    ```

### Pipeline

* ```Redis``` 客户端执行一条命令通常分为四个过程：发送命令 -> 命令排队 -> 命令执行 ->返回结果。其中第1步和第4步的时间总和被称为往返时间（```Round Trip Time```，简称```RTT```）。我们可以发现 ```Redis``` 的性能瓶颈往往在于网络而非命令执行本身。当需要执行多条命令时，可以使用 ```Redis``` 提供了 ```mget```、```mset``` 等原生批量操作命令来节约 ```RTT```，或者使用 ```Pipeline``` 机制来一次性发送多条命令。 ```Pipeline``` 机制能将一组 ```Redis``` 命令进行组装，通过一次 ```RTT``` 传输给 ```Redis```，最后将这组命令的执行结果按顺序返回给客户端：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_6.png)

* 性能测试，使用 ```Pipeline``` 执行 10000 次 ```set``` 操作在不同网络延迟下的提升效果非常显著：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_7.png)

* 原生批量命令与 ```Pipeline``` 对比：

  * 原子性： 原生批量命令（如 ```mget```、```mset```）是原子的，而 ```Pipeline``` 是非原子的。
  * 命令支持： 原生批量命令通常是一个命令对应多个 ```key```，而 ```Pipeline``` 支持组装多个不同的命令。
  * 实现位置： 原生批量命令是由 ```Redis``` 服务端支持实现的，而 ```Pipeline``` 需要服务端和客户端共同实现。

* 最佳实践：

  * 适度组装：```Pipeline``` 组装的命令个数不能没有节制。如果一次组装的数据量过大，一方面会增加客户端的等待时间，另一方面会造成网络阻塞。建议将大批量命令拆分成多次较小的 ```Pipeline``` 来完成。
  * 单实例限制： ```Pipeline``` 通常只能操作 一个 ```Redis``` 实例。但在 ```Redis Cluster``` 等分布式场景中，仍可通过 ```hash_tag``` 等方式将 ```key``` 分配到相同节点，从而进行 ```IO``` 优化。 

### 事务与Lua

* ```Redis```使用事务与```Lua```脚本保证多条命令组合执行时的原子性。

* 事务：

  * 基本操作：事务以 ```MULTI``` 命令开始，以 ```EXEC``` 命令结束。在两者之间的命令不会立即执行，而是进入队列并返回 ```QUEUED```。只有执行 ```EXEC``` 后，这些命令才会原子地顺序执行。
  * 停止事务：如果在执行 ```EXEC``` 前想停止事务，可以使用 ```DISCARD``` 命令。
  * 错误处理机制：
    * 命令错误（语法错误）：如命令拼写错误，整个事务将无法执行，所有数据保持不变。
    * 运行时错误：如误把```SADD```命令写成了```ZADD```命令，Redis 不支持回滚，正确的命令会继续执行，开发人员需自行修复此类问题。
    * ```WATCH``` 命令：提供了一种乐观锁机制。在事务开始前监控某些键，如果在 ```EXEC``` 执行前这些键被其他客户端修改，则事务将不执行（返回 nil）。

* ```Lua```：

  * 基本概念：```Lua``` 是一种简单小巧但功能强大的脚本语言，被 ```Redis``` 集成用于帮助开发者定制自己的原子命令。
  * 数据类型：主要包括布尔（```booleans```）、数值（```numbers```）、字符串（```strings```）和表格（```tables```）。
  * 特殊点：```Lua``` 的数组（```tables```）下标是从 1 开始计算的
  * 控制结构：支持 ```for``` 循环、```while``` 循环以及 ```if else``` 逻辑判断。

    ```bash
    for ...
    do ...
    end
    ```

    ```bash
    while ...
    do ...
    end
    ```

    ```bash
    if ...
    then ... break
    else ...
    end
    ```

  * 更多使用请参考[官网](http://www.lua.org)。

* ```Redis``` 与 ```Lua``` 的集成

  * 在 ```Redis``` 中使用 ```Lua``` 脚本主要有三种好处：原子执行（不会被其他命令干扰）、定制化命令（常驻内存复用）、减少网络开销（多条命令打包）。
  * 执行方式：
    * ```EVAL```：直接发送脚本内容执行，支持通过 ```KEY``` 列表和参数列表增加灵活性，如 ```EVAL 'return "hello " .. KEYS[1] .. ARGV[1]' 1 redis world```。还可使用```redis-cli --eval script.lua key1 key2 arg1 arg2```命令直接执行整个脚本文件。
    * ```EVALSHA```：首先通过 ```script load``` 将脚本加载到 ```Redis``` 并获取 ```SHA1``` 校验和，后续通过 ```SHA1``` 执行，避免每次发送脚本带来的网络开销，如 ```redis-cli script load "$(cat script.lua)"```、```EVALSHA sha1_value key_count .. KEYS[1] .. ARGV[1]```。
  * ```Lua``` 中的 ```Redis API```：
    * ```redis.call```：调用 ```Redis``` 命令，如果执行失败，脚本会直接报错并结束。如 ```redis.call("set", "hello", "world")```。
    * ```redis.pcall```：调用 ```Redis``` 命令，如果失败则忽略错误继续执行。

* ```Lua```脚本管理：

  * ```script load script.lua```：将脚本加载到内存。
  * ```script exists sha1 [sha1 …]```：判断 ```SHA1``` 是否已加载。
  * ```script flush```：清除内存中所有已加载的脚本。
  * ```script kill```：杀掉正在执行且超时的脚本。如果脚本已执行过写操作，则无法直接 ```kill```，需使用 ```shutdown nosave``` 停止服务。

* 超时控制：```Redis``` 默认设置 ```lua-time-limit``` 为 5 秒，超过此时间会向其他调用发送 ```BUSY``` 信号。

### Bitmaps

* 数据结构模型
  *   **本质**：Bitmaps 本身并不是一种独立的数据结构，它实际上是**字符串（String）**。
  *   **模型**：可以将其想象成一个以位（bit）为单位的数组，数组的每个单元只能存储 **0** 和 **1**。
  *   **偏移量（Offset）**：数组的下标在 Bitmaps 中被称为偏移量，通过对字符串的位进行操作来实现各种功能，下标从左（0）到右（n）开始计算。存储海量数据时，偏移量一般都是代表存储的数值。

* 常用操作命令

  *   **`setbit key offset value`（设置值）**：设置键的第 offset 位的值。
      *   *示例*：将访问过网站的用户（用用户 ID 作为偏移量）记为 1。
      *   *注意*：如果偏移量非常大，第一次初始化时可能会因为申请大量内存而导致 Redis 阻塞。
  *   **`getbit key offset`（获取值）**：获取键第 offset 位的值。如果该位不存在，则返回 0。
  *   **`bitcount [start] [end]`（获取 1 的个数）**：统计 Bitmaps 指定范围内值为 1 的个数。
  *   **`bitop op destkey key[key...]`（位运算）**：这是一个复合操作，可以对多个 Bitmaps 做 **and（交集）**、**or（并集）**、**not（非）**、**xor（异或）** 操作，并将结果保存在 `destkey` 中。
      *   *应用场景*：计算两天都访问过网站的用户量（交集）或月活跃用户量（并集）。
  *   **`bitpos key targetBit [start] [end]`（计算位置）**：计算 Bitmaps 中第一个值为 targetBit（0 或 1）的偏移量。

* Bitmaps 的分析与优势
  *   **极高的空间效率**：
      *   在处理大量级用户统计时，Bitmaps 具有显著优势。例如，存储 1 亿用户每天的独立访问情况，如果使用集合（Set）存储 5000 万活跃用户 ID 约需 400MB 内存，而使用 Bitmaps 仅需约 12.5MB。
      *   随着时间推移（如按月、年统计），Bitmaps 节省的内存空间非常客观。
  *   **局限性**：
      *   Bitmaps 并非“万金油”。如果该网站的独立访问用户非常少（例如 1 亿用户中只有 10 万活跃），使用 Bitmaps 反而可能比使用 Set 更浪费内存，因为 Bitmaps 的大部分位都是 0，但依然占据空间。
      *   **不支持二级结构过期**：Redis 不支持对 Bitmaps 内部的位设置过期时间。

* 最佳实践建议
  *   **用户 ID 处理**：如果用户 ID 以较大的数字（如 10000）开头，建议在操作前将用户 ID 减去该起始值，以减小偏移量并减少内存浪费。
  *   **避免大偏移量阻塞**：在第一次初始化 Bitmaps 时，应尽量规避使用超大的偏移量以防止阻塞。
  *   **场景选择**：Bitmaps 适合用于计算独立总数且能容忍 ID 密集分布的场景。

### HyperLogLog

* ```HyperLogLog``` 不是一种新的数据结构，其实际类型为**字符串类型**，而是一种基于概率的**基数算法**。

* 核心功能与特点
  *   **用途**：利用极小的内存空间完成**独立总数（基数）**的统计，例如统计独立 ```IP``` 、```Email``` 或用户 ```ID``` 等。
  *   **优势（节省内存）**：内存占用量小得惊人。源文件中的测试显示，统计 100 万个独立 ```ID``` 时，使用集合（```Set```）类型需要约 **84MB** 内存，而使用 ```HyperLogLog``` 仅需约 **15KB**。
  *   **局限性**：
      *   **存在误差**：它不是 100% 正确的，```Redis``` 官方给出的失误率约为 **0.81%**。
      *   **无法取回单条数据**：它只负责计算总量，无法像 ```Set``` 那样获取具体存入了哪些数据。

* 常用操作命令，```HyperLogLog``` 主要提供了三个命令：
  *   **`pfadd key element [element ...]`（添加元素）**：向指定的 ```HyperLogLog``` 中添加元素，成功则返回 1。
  *   **`pfcount key [key ...]`（计算独立总数）**：计算一个或多个 ```HyperLogLog``` 的独立总数。
  *   **`pfmerge destkey sourcekey [sourcekey ...]`（合并）**：求出多个 ```HyperLogLog``` 的并集并赋值给目标键。
      *   *示例*：可以用它来合并两天（如 3月5日和3月6日）的独立访问用户数。

* 内存占用对比（百万级用户统计），源文件通过表 3-6 对比了 ```Set``` 和 ```HyperLogLog``` 在不同时间维度的空间占用情况：

  | 统计时长 | 集合（```Set```）类型占用 | ```HyperLogLog``` 占用 |
  | :--- | :--- | :--- |
  | **1 天** | ```80MB``` | **15KB** |
  | **1 个月** | ```2.4GB``` | **450KB** |
  | **1 年** | ```28GB``` | **5MB** |

* 使用建议，开发人员在选择是否使用 ```HyperLogLog``` 时，只需确认以下两点：
  *  **目标明确**：仅需计算独立总数，不需要获取原始单条数据。
  *  **容忍误差**：业务场景能够接受约 0.81% 的误差率。

### 发布订阅

* ```Redis``` 的**发布订阅**（```Publish/Subscribe```）功能是其提供的一种基于“发布/订阅”模式的消息通信机制。在这种模式下，消息发布者和订阅者不进行直接通信，发布者向指定的**频道**（```channel```）发布消息，所有订阅该频道的客户端都会收到该消息。以下是发布订阅模型：
  *   **发布者**（```Publisher```）：向频道发送消息的客户端。
  *   **频道**（```Channel```）：消息传输的通道。
  *   **订阅者**（```Subscriber```）：接收频道消息的客户端。
  *   **特点**：发送的消息不会被持久化。新开启的订阅客户端无法收到该频道之前的消息。
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_8.png)

* 相关命令， ```Redis``` 提供了多条命令来管理发布订阅功能：
  *   **发布消息**：`publish channel message`。例如向 `channel:sports` 发布消息，返回结果为订阅者的个数。
  *   **订阅频道**：`subscribe channel [channel ...]`。订阅后客户端进入订阅状态，实时接收频道消息。
  *   **取消订阅**：`unsubscribe [channel [channel ...]]`。
  *   **按照模式订阅和取消订阅**：`psubscribe pattern [pattern...]` 和 `punsubscribe [pattern...]`。支持 ```glob``` 风格的匹配（如 `it*` 匹配所有以 `it` 开头的频道）。
  *   **查询订阅状态**：
      *   `pubsub channels [pattern]`：查看当前活跃的频道（至少有一个订阅者）。
      *   `pubsub numsub [channel ...]`：查看指定频道的订阅数。
      *   `pubsub numpat`：查看模式订阅的总数。

* 使用场景，发布订阅模式常用于以下场景：
  *   **聊天室和公告牌**。
  *   **服务解耦**：例如视频管理系统在更新视频信息后，向频道发布消息；多个视频服务通过订阅该频道来实时更新本地缓存，从而解决业务间的耦合性。

* 开发提示与限制
  *   **命令限制**：客户端在进入订阅状态后，只能接收 `subscribe`、`psubscribe`、`unsubscribe` 和 `punsubscribe` 这四种命令。
  *   **消息积压**：与 ```Kafka``` 或 ```RocketMQ``` 等专业消息队列相比，```Redis``` 的发布订阅功能较弱，**不具备消息堆积（无法存储历史消息）和回溯能力**。
  *   **集群环境下的影响**：在 ```Redis Cluster``` 模式下，`publish` 命令会向所有节点进行广播，如果频繁使用会严重消耗集群内的网络带宽。对于此类高频需求，建议使用 Sentinel 架构专门处理。

### GEO

* **GEO（地理信息定位）功能**，该功能支持存储地理位置信息，常用于实现诸如“附近位置”、“摇一摇”等依赖于 ```LBS``` （基于位置服务）的功能。

* 核心命令
  *   **增加地理位置信息 (`geoadd`)**：
      *   语法：`geoadd key longitude latitude member [longitude latitude member ...]`。
      *   它将经度（```longitude```）、纬度（```latitude```）和成员（```member```）添加到指定的集合中。
      *   如果成员已存在，执行该命令会更新其地理位置信息，返回结果表示成功添加的新成员个数。
  *   **获取地理位置信息 (`geopos`)**：
      *   语法：`geopos key member [member ...]`。
      *   可以获取指定成员的经纬度坐标。
  *   **计算距离 (`geodist`)**：
      *   语法：`geodist key member1 member2 [unit]`。
      *   用于计算两个成员之间的距离，支持的单位包括：`m`（米）、`km`（公里）、`mi`（英里）、`ft`（尺）。
  *   **获取指定范围内的地理信息集合 (`georadius` / `georadiusbymember`)**：
      *   语法1：`georadius key longitude latitude radius m|km|ft|mi [withcoord] [withdist] [withhash] [count count] [asc|desc]`。
      *   语法2：`georadiusbymember key member radius m|km|ft|mi [withcoord] [withdist] [withhash] [count count] [asc|desc]`。
      *   这两个命令用于以一个地理位置（经纬度或已存在的成员）为中心，计算指定半径内的其他成员。不同的是，第一种命令以经纬度为中心，第二种命令以已存在的成员为中心。
      *   **可选参数**包括：`withcoord`（包含经纬度）、`withdist`（包含距离）、`withhash`（包含```geohash```）、`COUNT`（限制数量）、`asc|desc`（按距离排序）等。
  *   **获取 geohash (`geohash`)**：
      *   语法：`geohash key member [member ...]`。
      *   ```Redis```使用```geohash```算法将二维经纬度转换为一维字符串。字符串越长，表示的位置越精确。

* 实现原理与特点
  *   **底层数据结构**：```GEO```功能的底层实现是 **`zset`（有序集合）**。
  *   **数据转换**：```Redis```将地理位置信息的```geohash```值存放在`zset`中。
  *   **删除操作**：由于```GEO```没有专门的删除命令，删除成员时需借用`zset`的命令，如 **`zrem`**。
  *   **geohash特性**：
      *   两个字符串越相似，它们之间的距离通常越近。
      *   ```geohash```编码与经纬度之间可以相互转换。

* 运维提示
  *   在进行数据统计或监控时，可以通过 `info memory` 查看```GEO```（通过`zset`实现）所占用的内存情况。
  *   在集群环境下，```GEO```相关的操作也需要注意键的分布，尽管其底层是`zset`，但在大规模应用时仍需考虑节点性能和数据倾斜问题。