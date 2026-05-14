## `Redis`配置统计字典

### `info`系统状态说明

* `info`命令的使用说明
  
  `info`命令是了解`Redis`运行状态最直接的工具，常用于查看实例运行状态、性能指标、内存使用、复制状态以及持久化状态。其使用方式主要分为三类：
    
    * `info`：返回部分最常用的`Redis`系统状态统计信息。
    * `info all`：返回全部`Redis`系统状态统计信息。
    * `info section`：仅返回指定模块的系统状态统计信息，其中`section`不区分大小写。
    * 使用示例：
      * 如果只关注内存情况，可以执行`info memory`。
      * 如果运维时发现客户端异常，可以执行`info clients`，并通过`client_longest_output_list`等指标判断是否存在输出缓冲区溢出的情况。

* 统计模块详细说明
  
  `info all`命令包含多个主要统计模块，通过这些模块可以较全面地掌握`Redis`实例的健康状况和运行负载。
    
    * `Server`：服务器基本信息，包括版本、`PID`、运行模式等。
    * `Clients`：客户端连接信息，包括连接数、缓冲区、阻塞客户端数量等。
    * `Memory`：内存使用统计，包括已用内存、内存峰值、碎片率等。
    * `Persistence`：持久化统计，包括`RDB`和`AOF`的运行状态。
    * `Stats`：全局统计，包括命令数、网络流量、`QPS`等。
    * `Replication`：复制统计，包括主从关系、复制偏移量、延迟等。
    * `CPU`：`CPU`消耗统计，包括主进程与子进程消耗时间。
    * `Commandstats`：命令执行统计，包括各命令调用次数和平均耗时。
    * `Cluster`：集群状态统计，用于判断是否开启集群模式。
    * `Keyspace`：数据库键统计，包括键总数、过期键统计等。

* 各模块关键指标解析
  
  不同模块反映的运行状态不同，运维排查时通常需要结合多个指标一起判断。
    
    * `Server`模块：包含`Redis`服务的版本号（`redis_version`）、运行模式（`redis_mode`）、进程`ID`（`process_id`）以及运行天数（`uptime_in_days`）等基础信息。
    * `Clients`模块：重点关注当前客户端连接数（`connected_clients`）和正在等待阻塞命令的客户端数量（`blocked_clients`）。
    * `Memory`模块：
      * `used_memory`：`Redis`分配器分配的内存总量，即存储数据的实际占用量。
      * `used_memory_rss`：从操作系统角度显示的进程占用物理内存总量。
      * `mem_fragmentation_ratio`：内存碎片率。若大于`1`，通常说明存在碎片消耗；若小于`1`，通常说明发生了`Swap`，会严重影响性能。
    * `Persistence`模块：记录`RDB`上次`bgsave`的状态（`rdb_last_bgsave_status`）和耗时（`rdb_last_bgsave_time_sec`），以及`AOF`文件当前尺寸（`aof_current_size`）和缓冲区长度等。
    * `Stats`模块：提供`Redis`基础性能指标，如每秒处理命令条数（`instantaneous_ops_per_sec`）、命中次数（`keyspace_hits`）和不命中次数（`keyspace_misses`）。
    * `Replication`模块：
      * 主节点视角：重点查看已连接从节点个数（`connected_slaves`）和主节点复制偏移量（`master_repl_offset`）。
      * 从节点视角：重点查看主节点`IP`（`master_host`）、连接状态（`master_link_status`）和自身复制偏移量。
    * `Commandstats`模块：为每个命令提供总调用次数（`calls`）、总耗时（`usec`）和平均耗时（`usec_per_call`），是排查性能瓶颈的重要依据。
    * `Keyspace`模块：列出每个数据库中的键总数（`keys`）和带有过期时间的键总数（`expires`）。

### `Standalone`配置说明和分析

* 总体配置
  
  该部分涵盖`Redis`服务运行的基础参数，包括运行方式、端口、日志、数据库数量以及工作目录等。
    
    * `daemonize`：是否以守护进程方式运行，默认值为`no`，不可通过`config set`热生效。
    * `port`：监听端口，默认值为`6379`，不可热生效。
    * `loglevel`：日志级别，包括`debug`、`verbose`、`notice`、`warning`，支持热生效。
    * `databases`：可用数据库总数，默认值为`16`，不可热生效。
    * `dir`：工作目录，用于存放`AOF`、`RDB`、日志等文件，支持热生效。
    * `lua-time-limit`：`Lua`脚本最长执行时间，单位为毫秒，支持热生效。

* 最大内存及策略
  
  内存管理是`Redis`配置中的核心内容，相关配置决定了实例达到内存上限后的处理方式。
    
    * `maxmemory`：最大可用内存。如果设为`0`，默认表示不限制；但在`32`位系统下限制为`3GB`。该配置支持热生效。
    * `maxmemory-policy`：内存溢出后的淘汰策略，如`allkeys-lru`、`volatile-ttl`或`noeviction`，支持热生效。
    * `maxmemory-samples`：`LRU`算法采样数，默认值为`5`。增加采样数可以提高算法精度，但会增加`CPU`消耗，支持热生效。

* `AOF`持久化配置
  
  `AOF`（`Append Only File`）用于保证数据的实时持久化，适合对数据安全性要求较高的场景。
    
    * `appendonly`：是否开启`AOF`，默认值为`no`，支持热生效。
    * `appendfsync`：刷盘频率，可选值包括`always`、`everysec`、`no`，通常建议使用`everysec`，支持热生效。
    * `auto-aof-rewrite-percentage`：`AOF`重写增长比例条件，支持热生效。
    * `auto-aof-rewrite-min-size`：触发`AOF`重写的最小文件尺寸，默认值为`64MB`，支持热生效。
    * `no-appendfsync-on-rewrite`：`AOF`重写期间是否不执行`fsync`。开启后可以减轻`IO`压力，但会增加数据丢失风险。

* `RDB`持久化配置
  
  `RDB`（`Redis DataBase`）通过快照方式记录数据状态，适合定期备份和灾难恢复场景。
    
    * `save`：触发`RDB`快照的条件。例如`save 900 1`表示`900`秒内至少有`1`次修改时触发快照，支持热生效。
    * `dbfilename`：`RDB`文件名，默认值为`dump.rdb`，支持热生效。
    * `rdbcompression`：是否对`RDB`文件进行`LZF`压缩，默认值为`yes`，支持热生效。
    * `stop-writes-on-bgsave-error`：`BGSAVE`执行错误时是否停止写请求，默认值为`yes`，支持热生效。

* 慢查询配置
  
  慢查询配置用于监控执行时间过长的命令，帮助定位业务调用或实例性能问题。
    
    * `slowlog-log-slower-than`：慢查询阈值，单位为微秒，默认值为`10000`，支持热生效。
    * `slowlog-max-len`：慢查询日志最大存储条数，默认值为`128`，支持热生效。

* 数据结构优化配置
  
  `Redis`为了节省内存，会对小规模数据结构进行特殊编码，如`ziplist`、`intset`等。
    
    * `hash-max-ziplist-entries` / `hash-max-ziplist-value`：`Hash`类型使用`ziplist`编码的元素个数及字节大小上限。
    * `list-max-ziplist-entries` / `list-max-ziplist-value`：`List`类型使用`ziplist`编码的限制。需要注意，`Redis 3.2`后相关实现逐步由`quicklist`参数取代。
    * `set-max-intset-entries`：集合使用`intset`编码的最大元素个数。
    * `zset-max-ziplist-entries` / `zset-max-ziplist-value`：有序集合使用`ziplist`编码的限制。

* 复制相关配置
  
  复制相关配置用于控制主从同步、复制超时、复制积压缓冲区以及网络延迟等行为。
    
    * `slaveof`：指定当前节点复制的主节点`IP`和端口。
    * `repl-timeout`：复制超时时间，默认值为`60`秒，支持热生效。
    * `repl-backlog-size`：复制积压缓冲区大小，默认值为`1MB`。增大该值可以减少全量复制概率，支持热生效。
    * `repl-disable-tcp-nodelay`：是否关闭`TCP_NODELAY`。开启后可以节省带宽，但会增加延迟，默认值为`no`，支持热生效。

* 客户端及安全配置
  
  客户端及安全配置主要控制连接数量、空闲连接释放、访问密码和网络绑定等内容。
    
    * `maxclients`：最大客户端连接数，默认值为`10000`，支持热生效。
    * `timeout`：客户端闲置关闭时间，默认值为`0`，表示永不关闭，支持热生效。
    * `requirepass`：设置`Redis`访问密码，支持热生效。
    * `bind`：绑定的`IP`地址，不可热生效。
    * `masterauth`：从节点连接主节点所需的密码。

### `Sentinel`配置说明和分析

* `sentinel monitor`
  
  该配置用于定义`Sentinel`节点监控的主节点信息。
    
    * 配置格式：`sentinel monitor <master-name> <ip> <port> <quorum>`。
    * `<master-name>`：主节点别名，用于标识被监控的主节点集合。
    * `<quorum>`：判定主节点“客观下线”所需的票数。只有当认为主节点不可达的`Sentinel`节点数达到该值时，才会触发客观下线判定。
    * 该参数还与领导者选举有关。进行领导者选举时，至少需要`max(quorum, num(sentinels)/2+1)`个在线节点参与。

* `sentinel down-after-milliseconds`
  
  该配置用于控制`Sentinel`判断节点“主观下线”的时间阈值。
    
    * 配置格式：`sentinel down-after-milliseconds <master-name> <times>`。
    * 默认值：`30000`，即`30`秒。
    * 判断逻辑：`Sentinel`通过`PING`命令检测节点可达性。如果节点在指定时间内没有有效回复，`Sentinel`会将其判定为“主观下线”。
    * 适用范围：该配置不仅对主节点有效，对从节点和其他`Sentinel`节点同样有效。

* `sentinel parallel-syncs`
  
  该配置用于限制故障转移完成后，每次向新主节点发起复制操作的从节点数量。
    
    * 配置格式：`sentinel parallel-syncs <master-name> <nums>`。
    * 默认值：`1`。
    * 如果设置较大，多个从节点会同时复制，可能增加新主节点的网络和磁盘`IO`开销。
    * 如果设置为`1`，从节点会轮询发起复制，能够减轻主节点负载。

* `sentinel failover-timeout`
  
  该参数作用于故障转移过程中的多个阶段，而不只是总超时时间。
    
    * 配置格式：`sentinel failover-timeout <master-name> <times>`。
    * 默认值：`180000`，即`180`秒。
    * 如果故障转移失败，下次再对该主节点尝试转移的起始时间通常是该值的`2`倍。
    * 在执行`slaveof no one`晋升主节点、执行`info`确认状态、命令其他从节点复制等阶段，如果执行时间超过该值，则判定故障转移失败。

* `sentinel auth-pass`
  
  该配置用于让`Sentinel`正确连接设置了密码的主节点。
    
    * 配置格式：`sentinel auth-pass <master-name> <password>`。
    * 如果被监控主节点设置了密码（`requirepass`），`Sentinel`必须配置该参数，否则无法正常监控主节点。

* `sentinel notification-script`
  
  该配置用于在故障转移期间触发外部通知脚本。
    
    * 配置格式：`sentinel notification-script <master-name> <script-path>`。
    * 当故障转移期间发生重要警告级别事件，例如客观下线时，`Sentinel`会触发指定路径的脚本。
    * 开发者可以利用脚本参数实现邮件或短信报警。

* `sentinel client-reconfig-script`
  
  该配置用于在故障转移完成后通知客户端或代理层更新连接目标。
    
    * 配置格式：`sentinel client-reconfig-script <master-name> <script-path>`。
    * 故障转移成功结束后会触发该脚本。
    * 脚本会接收原主节点和新主节点的`IP`及端口等参数，可用于通知客户端或代理层切换连接。

* 运维与动态配置提示
  
  `Sentinel`配置在运维时需要特别关注一致性和动态修改方式。
    
    * 热生效支持：上述`Sentinel`特殊配置均支持通过`sentinel set`命令在运行时动态修改并立即生效，且会自动刷新配置文件。
    * 配置一致性：建议所有`Sentinel`节点配置尽可能保持一致，以确保故障发现和转移过程中的判定逻辑统一。
    * 命令限制：`Sentinel`节点不支持`config`命令，修改现有运行参数必须使用`sentinel set`命令。

### `Cluster`配置说明和分析

* 核心运行配置
  
  核心运行配置决定`Redis`实例是否以集群模式运行，以及集群元数据如何保存。
    
    * `cluster-enabled`：是否开启集群模式。
      * 含义：决定当前`Redis`实例是否以集群模式运行。
      * 默认值：`yes`。
      * 分析：必须在启动前配置，不支持通过`config set`动态修改。
    * `cluster-config-file`：集群配置文件名称。
      * 含义：`Redis`集群自动维护的配置文件，用于保存节点`ID`、槽映射关系、节点角色等状态信息。
      * 默认值：`nodes.conf`。建议设置为`nodes-{port}.conf`，以区分同一机器上的不同实例。
      * 分析：该文件由`Redis`自动管理，严禁手动修改，以防重启时集群信息错乱。

* 超时与健康检查配置
  
  超时与健康检查配置直接影响集群故障发现速度、误判概率和节点间通信频率。
    
    * `cluster-node-timeout`：集群节点超时时间。
      * 含义：节点间通信（`ping` / `pong`消息）的超时时间。
      * 默认值：`15000`毫秒，即`15`秒。
      * 分析：这是集群中最关键的参数之一。设置过短可能因网络波动产生频繁误判；设置过长则会增加故障转移耗时。
      * 额外影响：当节点发现与其他节点最后通信时间超过该值的一半时，会直接发送`ping`消息，因此该参数也会影响带宽消耗。
    * `cluster-slave-validity-factor`：从节点有效性判断因子。
      * 含义：用于过滤主节点故障时数据过旧的从节点，使其不具备故障转移资格。
      * 判断公式：如果从节点与主节点最后通信时间超过`(cluster-node-timeout * cluster-slave-validity-factor) + repl-ping-slave-period`，则该从节点失效。
      * 默认值：`10`。
      * 分析：设置为`0`表示从节点永远不过期，无论其数据有多旧都会尝试晋升。

* 可用性与容错配置
  
  可用性配置主要决定部分槽不可用时，整个集群是否继续对外提供服务。
    
    * `cluster-require-full-coverage`：集群完整性要求。
      * 含义：是否要求`16384`个槽必须全部分配给在线节点，集群才对外提供服务。
      * 默认值：`yes`。
      * 分析：如果设为`yes`，只要有一个槽不可用，整个集群就会返回`(error) CLUSTERDOWN`错误。
      * 运维建议：线上环境建议设为`no`。这样当某个持有槽的主节点故障且尚未完成转移时，只影响该节点负责的槽，集群其他部分仍能正常工作。

* 节点迁移与平衡配置
  
  节点迁移配置用于提升集群高可用能力，避免部分主节点长期没有从节点保护。
    
    * `cluster-migration-barrier`：主从切换的最小从节点数。
      * 含义：当一个主节点拥有富余从节点时，可以将从节点迁移给孤立主节点。该参数定义主节点需要保留的最小从节点数。
      * 默认值：`1`。
      * 分析：设置为`1`意味着只有在主节点拥有至少`2`个从节点时，才会将其中`1`个迁移给其他没有从节点的主节点。

* 配置总结
  
  `Cluster`相关配置可按是否支持热生效进行分类，便于运维时快速判断修改方式。
    
    * 支持热生效的配置：
      * `cluster-node-timeout`：默认值为`15000ms`，影响故障发现速度和`Gossip`消息频率。
      * `cluster-require-full-coverage`：默认值为`yes`，决定部分槽失效时整个集群是否可用。
      * `cluster-slave-validity-factor`：默认值为`10`，用于防止数据过旧的从节点参与选举。
      * `cluster-migration-barrier`：默认值为`1`，用于控制从节点迁移触发条件。
    * 不支持热生效的配置：
      * `cluster-enabled`：默认值为`yes`，用于控制集群模式开关。
      * `cluster-config-file`：默认值为`nodes.conf`，用于存储集群元数据。
