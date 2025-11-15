## Redis development and operations

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


* 哈希（```Hash```）

* 列表（```List```）

* 集合（```Set```）

* 有序集合（```Sorted Set```）