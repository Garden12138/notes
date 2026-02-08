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