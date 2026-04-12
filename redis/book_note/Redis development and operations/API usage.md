## API的理解和使用

### API 的理解和实现

* 概要

  * 主要介绍```Redis```单线程架构以及一些全局命令，详细介绍了```Redis```提供的五种数据结构（字符串、哈希、列表、集合、有序集合）,通过理解这些数据结构及其常用命令，帮助开发者在合适的应用场景中选择合适的数据结构和命令，从而有效提高程序效率并降低潜在问题。

* 基础知识

  * 单线程架构，```Redis```是单线程处理命令的，客户端每次调用一般经历三个过程：命令发送、命令执行、命令返回：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_1.png)

    多个客户端调用，所有命令在一个队列里排队等待被执行：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_2.png)

    这种单线程架构仍然可实现高性能的内存数据库服务依赖于：

     - 纯内存存储
     - 使用```I/O```多路复用模型和自身事件模型，将```epoll```中的连接、读写、关闭都转换为事件，不在网络```I/O```上浪费时间。
     - 避免了线程切换和锁的开销，保证了高性能。

    又由于是单线程，每个命令必须被快速执行完毕。如果命令执行时间过长，会阻塞整个```Redis```。

  * 数据库管理，可通过一些全局命令管理数据库：
    
    - ```SELECT dbIndex```：选择指定数据库。
    - ```FLUSHDB```：清空当前数据库，删除当前数据库中的所有数据。
    - ```FLUSHALL```：清空整个数据库，删除所有数据。

  * 键管理，可通过一些全局命令管理键：

    - ```KEYS *```：查询所有键。
    - ```DBSIZE```：查询当前数据库中的键数量，其计算方式是取内置的计数器，不会遍历所有键，时间复杂度为```O(1)```。
    - ```EXISTS key```：判断键是否存在。
    - ```TYPE key```：查询键的类型。
    - ```DEL key```：删除键。
    - ```EXPIRE key seconds```：设置键的过期时间，单位为秒。
    - ```TTL key```：查询键的剩余过期时间，单位为秒，返回结果大于等于0表示剩余过期时间，返回结果为-1表示未设置过期时间，返回结果为-2表示键不存在。
    - ```RENAME key newkey```：重命名键，如果新键已经存在，则覆盖（即```newkey```原有值将不存在）。
    - ```RENAMENX key newkey```：重命名键，如果新键已经存在，则不覆盖。
    - ```MOVE key dbIndex```：移动键到指定数据库，不建议在生产使用。
    - ```DUMP key``` + ```RESTORE key TTL value```：实现键在不同实例间迁移，通过客户端分两步实现，非原子性，不建议在生产使用。
    - ```MIGRATE host port key destination-db timeout```：实现键在不同实例间迁移，原子性，推荐使用。
    - ```KEYS pattern```：查询符合给定模式的键，支持正则表达式。全局遍历，容易阻塞```Redis```主线程，不建议在生产使用。
    - ```SCAN cursor [MATCH pattern] [COUNT count]```：使用游标（```cursor```）进行迭代，直到游标返回0表示遍历结束。采用渐进式遍历，每次执行的时间复杂度为```O(1)```，有效解决了```KEYS```命令的阻塞问题。但不能保证在遍历过程中键发生变化时（增删改），能够完整遍历所有键或避免重复键。

  * 数据结构和内部编码，```Redis```提供了五种数据结构：字符串、哈希、列表、集合、有序集合，每种数据结构都有多种底层的内部编码实现：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_3.png)

    内部编码实现的好处：

     - 允许在不影响外部数据结构和命令的情况下改进内部编码（如```Redis 3.2```提供的 ```quicklist```优化了```list```的内部实现）
     - 多种内部编码可以在不同场景下发挥优势（例如，```ziplist```更省内存，但元素多时性能下降，此时```Redis```会切换到```linkedlist```）。

    可以使用```OBJECT ENCODING```命令查看键的内部编码实现。

* 字符串（```String```），是```Redis```中最基础的数据结构，其他几种数据结构也是在字符串类型的基础上构建的。字符串类型的值可以为字符串（包括简单的字符串，以及复杂的字符串，如```JSON```、```XML```）、数字（整数、浮点数）以及二进制（图片、音频、视频）数据，但值最大不能超过```512MB```。

  * 命令用法：

    * 设置值```SET```命令：

      ```bash
      SET key value [EX seconds] [PX milliseconds] [NX|XX]
      ```

      ```EX```表示设置键的过期时间，单位为秒；```PX```表示设置键的过期时间，单位为毫秒。```NX```表示只有键不存在时，才设置值；```XX```表示只有键存在时，才设置值。```EX```还衍生出```SETEX```命令：

      ```bash
      SETEX key seconds value
      ```

      ```NX```也衍生出```SETNX```命令：

      ```bash
      SETNX key value
      ```

      ```Redis```是单线程命令处理机制，若有多个客户端同时执行```SETNX key value```命令，根据```SETNX```的特性只有一个客户端能设置成功，所以其可以作为分布式锁的一种实现方案。

    * 获取值```GET```命令：

      ```bash
      GET key
      ```

      若键不存在，则返回```nil```。

    * 批量设置值```MSET```命令：

      ```bash
      MSET key value [key value...]
      ```

    * 批量获取值```MGET```命令：

      ```bash
      MGET key [key...]
      ```

      批量操作可减少网络开销，提高性能，但注意每次批量操作的命令数不要太多，否则会导致```Redis```主线程阻塞。

    * 自增值```INCR```命令：

      ```bash
      INCR key
      ```

      若值不是整数，返回错误；若值是整数，则自增值并返回；若键不存在，则设置值为1并返回。除了```INCR```命令，还提供了```DECR```（自减）、```INCRBY```（自增指定数字）、```DECRBY```（自减指定数字）、```INCRBYFLOAT```（自增浮点数）命令。

    * 追加值```APPEND```命令：

      ```bash
      APPEND key value
      ```

      向键追加值，若键不存在，则创建并追加值；若键存在，则追加值并返回追加后的长度。

    * 长度```STRLEN```命令：

      ```bash
      STRLEN key
      ```

      返回键值的长度，中文字符占3个字节。

    * 获取原值并设置新值```GETSET```命令：

      ```bash
      GETSET key value
      ```

    * 设置指定偏移量的字符串值```SETRANGE```命令：

      ```bash
      SETRANGE key offset value
      ```

    * 获取指定偏移量的字符串值```GETRANGE```命令：

      ```bash
      GETRANGE key start end
      ```

  * 内部编码：

    * ```embstr```：小于等于39个字节的字符串。
    * ```raw```：大于39个字节的字符串。
    * ```int```：8个字节的长整数。

  * 应用场景：

    * 缓存，是比较典型的使用场景，其中```Redis```作为缓存层，```MySQL```作为存储层，绝大部分请求的数据都是从```Redis```中获取。由于```Redis```具有支撑高并发的特性，所以缓存通常能起到加速读写和降低后端压力的作用：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_4.png)

      对于缓存键的命名建议在描述清楚含义的基础上减少长度，避免过长的键名带来的性能问题，一般以```业务:对象:id[属性]```的格式命名，如```oa:user:1```。

    * 计数，使用```Redis```的```INCR```命令可以方便地实现计数功能，如统计视频播放次数、点赞数、评论数等。但实际计数还需要考虑防作弊、按照不同维度计数，数据持久化到底层数据源等。

    * 共享```Session```，将分布式```Web```服务的用户```Session```数据存储到```Redis```中管理，可以避免用户重复登录的问题。

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_5.png)

    * 频控限制，如每次用户输入验证码后，需要限制用户在一段时间内不能重复提交指定次数，可以使用```Redis```的```SET```命令和```INCR```命令实现。


* 哈希（```Hash```），是键值对结构如```value={{field1, value1}, ...{fieldN, valueN}}```，这种映射关系被称为```field-value```。合理使用哈希（即控制哈希在```ziplist```和```hashtable```这两种内部编码之间的转换），可以降低内存占用提高性能（```hashtable```会消耗更多的内存）。

  * 常用命令：

    * 设置字段值```HSET```命令：

      ```bash
      HSET key field value
      ```

      还有```NX```命令，```HSETNX```命令，表示只有字段不存在时，才设置值：

      ```bash
      HSETNX key field value
      ```

    * 获取字段值```HGET```命令：

      ```bash
      HGET key field
      ```

    * 删除字段```HDEL```命令：

      ```bash
      HDEL key field [field...]
      ```

    * 统计字段数量```HLEN```命令：

      ```bash
      HLEN key
      ```

    * 批量设置字段值```HMSET```命令：

      ```bash
      HMSET key field1 value1 [field2 value2...]
      ```

    * 批量获取字段值```HMGET```命令：

      ```bash
      HMGET key field [field...]
      ```

    * 字段是否存在```HEXISTS```命令：

      ```bash
      HEXISTS key field
      ```

    * 获取所有字段```HKEYS```命令：

      ```bash
      HKEYS key
      ```

    * 获取所有字段值```HVALS```命令：

      ```bash
      HVALS key
      ```

    * 获取所有字段对```HGETALL```命令：

      ```bash
      HGETALL key
      ```

      当元素数量较多时，使用该命令可能导致阻塞。若一定要获取所有字段对，建议使用```HSCAN```命令进行迭代：

      ```bash
      HSCAN key cursor [MATCH pattern] [COUNT count]
      ```

    * 字段值整型自增```HINCRBY```命令：

      ```bash
      HINCRBY key field increment
      ```

    * 字段值浮点型自增```HINCRBYFLOAT```命令：

      ```bash
      HINCRBYFLOAT key field increment
      ```

    * 获取字段值字符串长度```HSTRLEN```命令：

      ```bash
      HSTRLEN key field
      ```

  * 内部结构：

    * ```ziplist```：当哈希表中哈希类型元素个数小于```hash-max-ziplist-entries```配置（默认 512 个），并且 所有值都小于```hash-max-ziplist-value```配置（默认 64 字节）时，使用```ziplist```作为哈希表的底层实现。```ziplist```是一块连续的内存，保存着哈希表的键值对，键和值都以字符串的形式保存。```ziplist```的优点是内存使用效率高，但是当元素数量较多时，操作速度会降低。

    * ```hashtable```：当哈希表中哈希类型元素个数大于等于```hash-max-ziplist-entries```配置，或者 任意一个值都大于等于```hash-max-ziplist-value```配置时，使用```hashtable```作为哈希表的底层实现。```hashtable```是一张哈希表，保存着哈希表的键值对，键和值都以字符串的形式保存。```hashtable```的优点是操作速度快，缺点是内存使用效率低。

  * 应用场景：

    * 最经典的是用于缓存结构化数据，如用户信息，通过将用户```ID```作为键后缀，多对```field-value```对应每个用户的属性，可以将关系型数据库表中的记录缓存到```Redis```哈希中。相比于将整个对象序列化为字符串存储，哈希类型更直观，并且在更新单个属性时更加便捷。如果使用```ziplist```编码，还能减少内存空间使用。但是哈希类型是稀疏的（每个键可以有不同的字段），而关系型数据库是完全结构化的。此外，关系型数据库可以执行复杂的查询，而```Redis```难以模拟。  

* 列表（```List```），是用来存储多个有序的字符串的数据结构。一个列表最多可以存储 2 ^ 32 −1 个元素。列表是一种非常灵活的数据结构，元素是有序的，可以通过索引下标获取某个元素或某个范围内的元素列表，支持从两端推入和弹出元素，且列表中的元素是可以重复的，所以在```Redis```中，它可以充当栈（```Stack```）、队列（```Queue```）、阻塞队列等角色。

  * 常用命令：

    * 在左侧推入元素```LPUSH```命令：
      
      ```bash
      LPUSH key value [value...]
      ```

    * 在右侧推入元素```RPUSH```命令：

      ```bash
      RPUSH key value [value...]
      ```

    * 向某个指定元素前或后添加元素```LINSERT```命令：

      ```bash
      LINSERT key BEFORE|AFTER pivot value
      ```

    * 获取指定索引范围内元素```LRANGE```命令：

      ```bash
      LRANGE key start stop
      ```

    * 获取指定索引元素```LINDEX```命令：

      ```bash
      LINDEX key index
      ```

    * 获取列表长度```LLEN```命令：

      ```bash
      LLEN key
      ```

    * 在左侧弹出元素```LPOP```命令：

      ```bash
      LPOP key
      ```

    * 在右侧弹出元素```RPOP```命令：

      ```bash
      RPOP key
      ```

    * 删除指定元素```LREM```命令：

      ```bash
      LREM key count value
      ```

      当```count```为0时，删除所有```value```元素；当```count```大于0时，删除最多```count```个```value```元素；当```count```小于0时，删除最少```-count```个```value```元素。

    * 按索引范围修剪```LTRIM```命令：

      ```bash
      LTRIM key start stop
      ```

      只保留索引范围内的元素。

    * 修改指定索引下元素```LSET```命令：

      ```bash
      LSET key index value
      ```

    * 在左侧阻塞弹出元素```BLPOP```命令：

      ```bash
      BLPOP key [key...] timeout
      ```

      在右侧阻塞弹出元素```BRPOP```命令：

      ```bash
      BRPOP key [key...] timeout
      ``` 

      若列表为空，则客户端会被阻塞，直到有元素被推入或超时（```timeout```秒，若```timeout```为0，则一直等待），客户端返回。

      若同时指定多个键进行阻塞弹出，会从左到右依次检查各键，一旦有一个键能弹出元素，客户端就会立即返回。

      若多个客户端同时对同一个键进行阻塞弹出，最先执行命令的客户端可优先获取弹出的值。

  * 内部编码：

    * ```ziplist```，列表元素个数小于```list-max-ziplist-entries```（默认 512 个），且每个元素的值都小于```list-max-ziplist-value```（默认 64 字节）。紧凑结构存储，节省内存。

    * ```linkedlist```，当无法满足```ziplist```的条件时（元素过多或元素过大），```Redis```会将内部实现转换为```linkedlist```。在```Redis 3.2```版本提供了```quicklist```内部编码，它结合了```ziplist```和```linkedlist```的优势（本质是以```ziplist```为节点的```linkedlist```），为列表类型提供了一种更为优秀的内部编码实现。

  * 应用场景：

    * 消息队列，使用```lpush + brpop```命令组合可以实现阻塞队列。生产者使用```lpush```从左侧插入元素，多个消费者使用```brpop```阻塞式地消费（弹出）列表尾部的元素。

* 集合（```Set```），是用来存储多个不重复且无序字符串元素的数据结构。多个集合之间可进行交集、并集、差集等运算，解决复杂的逻辑问题。

  * 常用命令：

    * 添加元素```SADD```命令（集合内）：

      ```bash
      SADD key element [element...]
      ```

    * 删除元素```SREM```命令（集合内）：

      ```bash
      SREM key element [element...]
      ```

    * 计算元素数量```SCARD```命令（集合内）：

      ```bash
      SCARD key
      ```

    * 判断元素是否存在```SISMEMBER```命令（集合内）：

      ```bash
      SISMEMBER key element
      ```

    * 随机获取指定个数元素```SRANDMEMBER```命令（集合内）：

      ```bash
      SRANDMEMBER key [count]
      ```

    * 随机弹出元素```SPOP```命令（集合内）：

      ```bash
      SPOP key [count]
      ```

    * 获取所有元素```SMEMBERS```命令（集合内）：

      ```bash
      SMEMBERS key
      ```

    * 多个集合交集```SINTER```命令（集合间）：

      ```bash
      SINTER key [key...]
      ```

    * 多个集合并集```SUNION```命令（集合间）：

      ```bash
      SUNION key [key...]
      ```

    * 多个集合差集```SDIFF```命令（集合间）：

      ```bash
      SDIFF key [key...]
      ```

      此时结果是第一个集合中独有的元素。

    * 将多个集合交集并保存到新集合（```destination```）```SINTERSTORE```命令（集合间）：

      ```bash
      SINTERSTORE destination key [key...]
      ```

    * 将多个集合并集并保存到新集合（```destination```）```SUNIONSTORE```命令（集合间）：

      ```bash
      SUNIONSTORE destination key [key...]
      ```

    * 将多个集合差集并保存到新集合（```destination```）```SDIFFSTORE```命令（集合间）：

      ```bash
      SDIFFSTORE destination key [key...]
      ```

  * 内部编码：

    * ```intset```，元素值都是整数，且元素个数小于```set-max-intset-entries```（默认 512 个），使用整数集合。使用更加紧凑的结构存储，可以有效减少内存的使用。

    * ```hashtable```，元素值不是整数，或者元素个数大于等于```set-max-intset-entries```，使用哈希表。

  * 应用场景：

    * 打标使用，如使用```sadd user:1:tags tag1 tag2```为用户添加标签。又可使用```sinter```、```sunion```、```sdiff```等命令实现标签的交集、并集、差集等操作。

* 有序集合（```Sorted Set```），也叫```ZSet```，保留了集合（```Set```）不能有重复成员的特性，但不同的是，有序集合中的每个元素都可以设置一个分数（```score```）作为排序的依据。

  * 常用命令：

    * 添加元素```ZADD```命令（有序集合内）：

      ```bash
      ZADD key score1 member1 [score2 member2]
      ```

      ```Redis3.2```为```zadd```命令添加了```nx、xx、ch、incr```四个选项：

      ```-nx```，表示只当```member```不存在时，才添加；
      ```-xx```，表示只当```member```存在时，才更新；
      ```-ch```，返回集合内元素和分数发生变化的个数；
      ```-incr```，表示对```score```进行增量更新。

    * 计算元素数量```ZCARD```命令（有序集合内）：

      ```bash
      ZCARD key
      ```

    * 计算元素分数```ZSCORE```命令（有序集合内）：

      ```bash
      ZSCORE key member
      ```

    * 计算元素排名（低 -> 高）```ZRANK```命令（有序集合内）：

      ```bash
      ZRANK key member
      ```

    * 计算元素排名（高 -> 低）```ZREVRANK```命令（有序集合内）：

      ```bash
      ZREVRANK key member
      ```

    * 删除元素```ZREM```命令（有序集合内）：
     
      ```bash
      ZREM key member [member...]
      ```

    * 增加元素分数```ZINCRBY```命令（有序集合内）：

      ```bash
      ZINCRBY key increment member
      ```

    * 获取指定排名范围内（低 -> 高）元素```ZRANGEBYSCORE```命令（有序集合内）：

      ```bash
      ZRANGE key start stop [WITHSCORES]
      ```

    * 获取指定排名范围内（高 -> 低）元素```ZREVRANGEBYSCORE```命令（有序集合内）：

      ```bash
      ZREVRANGE key start stop [WITHSCORES]
      ```

    * 获取指定分数范围内（低 -> 高）元素```ZRANGEBYSCORE```命令（有序集合内）：

      ```bash
      ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]
      ```

    * 获取指定分数范围内（高 -> 低）元素```ZREVRANGEBYSCORE```命令（有序集合内）：

      ```bash
      ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]
      ```

    * 获取指定分数范围成员数量```ZCOUNT```命令（有序集合内）：

      ```bash
      ZCOUNT key min max
      ```

    * 删除指定排名内的升序元素```ZREMRANGEBYRANK```命令（有序集合内）：

      ```bash
      ZREMRANGEBYRANK key start stop
      ```

    * 删除指定分数范围内的升序元素```ZREMRANGEBYSCORE```命令（有序集合内）：

      ```bash
      ZREMRANGEBYSCORE key min max
      ```

    * 交集```ZINTERSTORE```命令（有序集合间）：

      ```bash
      ZINTERSTORE destination numkeys key [key...] [WEIGHTS weight [weight...]] [AGGREGATE SUM|MIN|MAX]
      ```

      ```destination```，新集合的键名；
      ```numkeys```，参与计算的有序集合个数；
      ```key```，参与计算的有序集合键名；
      ```WEIGHTS```，分数权重；
      ```AGGREGATE```，聚合方式，交集后分数可按照```SUM```、```MIN```、```MAX```方式计算。

    * 并集```ZUNIONSTORE```命令（有序集合间）：

      ```bash
      ZUNIONSTORE destination numkeys key [key...] [WEIGHTS weight [weight...]] [AGGREGATE SUM|MIN|MAX]
      ```

  * 内部编码：

    * ```ziplist```，有序集合元素个数小于```zset-max-ziplist-entries```（默认 128 个），并且每个元素的值都小于```zset-max-ziplist-value```（默认 64 字节）。使用更加紧凑的结构存储，有效减少内存使用。

    * ```skiplist```，当不满足```ziplist```条件时（元素过多或过大），会使用```skiplist```作为内部实现。

  * 应用场景：

    * 适用于排行榜实现，以用户赞数排行榜为例：

     * 添加用户赞数：```zadd user:ranking:2016_03_15 3 mike```

     * 当用户获得新的赞时增加分数：```zincrby user:ranking:2016_03_15 1 mike```

     * 取消用户赞：```zrem user:ranking:2016_03_15 mike```

     * 展示赞数最多的前10个用户排行：```zrevrange user:ranking:2016_03_15 0 9```

     * 展示个人排名：```zrank user:ranking:2016_03_15 mike```

     * 展示用户赞数：```zscore user:ranking:2016_03_15 mike```