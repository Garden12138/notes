## 哨兵

### 基本概念

* 相关名词解释，为了确保概念的一致性，书中首先对```Redis Sentinel```涉及的核心名词进行了定义：
  *   **主节点（master）：** ```Redis```主服务/数据库，是一个独立的```Redis```进程。
  *   **从节点（slave）：** ```Redis```从服务/数据库，也是一个独立的```Redis```进程。
  *   **Redis数据节点：** 泛指主节点和从节点的合称。
  *   **Sentinel节点：** 监控```Redis```数据节点的独立```Sentinel```进程。
  *   **Sentinel节点集合：** 由若干```Sentinel```节点组成的抽象组合。
  *   **Redis Sentinel：** 由```Sentinel```节点集合和```Redis```数据节点共同组成的```Redis```高可用实现方案。
  *   **应用方：** 泛指一个或多个连接```Redis```的客户端进程或线程。

* 主从复制模式存在的问题，传统的```Redis```主从复制模式虽然能实现数据同步，起到**备份（热备）**和**扩展读能力**的作用，但存在以下显著局限：
  *   **故障转移需人工干预：** 一旦主节点出现故障，必须手动将一个从节点晋升为主节点，同时需要修改应用方的主节点地址，并命令其他从节点去复制新的主节点。整个过程实时性和准确性都无法保障。
  *   **性能与存储限制：** 主节点的写能力和存储能力都受到单机的限制（这些问题由第10章的“集群”解决）。
  *   **高可用性不足：** 由于故障转移需要人工介入，应用方无法及时感知主节点变化，可能导致数据丢失或服务不可用。

* 高可用的手动处理过程，在没有哨兵的情况下，主节点故障的处理逻辑包含五个步骤：
  *  **主节点故障：** 客户端连接失败，主从复制中断。
  *  **晋升主节点：** 选出一个从节点执行`slaveof no one`命令，使其成为新主节点。
  *  **更新应用方：** 更新客户端的主节点信息并重启应用。
  *  **建立新复制：** 命令其余从节点去复制新的主节点。
  *  **老主节点恢复：** 待故障的主节点恢复后，让其成为新主节点的从节点。

  这种手动模式存在三个核心难点：**节点不可达的判定机制、多个从节点晋升的唯一性保证、通知客户端机制的健壮性**。

* ```Redis Sentinel```的高可用性，```Redis Sentinel```架构通过自动化上述过程实现了真正的**高可用**。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_21.png)

* **核心架构与工作逻辑**，```Redis Sentinel```是一个分布式架构，包含若干个```Sentinel```节点和```Redis```数据节点。
  *   **监控：** ```Sentinel```节点会定期检测所有```Redis```数据节点以及其余```Sentinel```节点是否可达。
  *   **协商与决策：** 当一个```Sentinel```节点发现主节点不可达时，会与其他```Sentinel```节点进行“协商”。当**大多数**```Sentinel```节点都认为主节点不可达时，它们会做出客观下线的判定。
  *   **故障转移：** 哨兵集合会选举出一个领导者```Sentinel```节点来完成自动故障转移工作，包括选出新主节点、让其他从节点复制新主、通知应用方等。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_22.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_23.png)

* **Redis Sentinel的核心功能**
  1.  **监控（Monitoring）：** 持续检测数据节点和哨兵节点的状态。
  2.  **通知（Notification）：** 将故障转移的结果实时通知给应用方。
  3.  **主节点故障转移（Automatic failover）：** 自动化完成从节点晋升和主从关系维护。
  4.  **配置提供者（Configuration provider）：** 客户端初始化时连接的是```Sentinel```集合，从中获取当前的主节点信息。

* **哨兵模式的优势**
  *   **防止误判：** 故障判定由多个```Sentinel```节点共同完成，有效避免单点误判。
  *   **系统健壮：** 即使个别```Sentinel```节点不可用，整个集合依然能正常工作。

* **版本建议：
  * ** 书中明确指出，```Redis 2.6```版本的```Sentinel v1```存在功能和健壮性问题，建议生产环境务必使用**Redis 2.8及以上版本**的```Sentinel v2```。

### 安装和部署

* 部署拓扑结构，为了演示方便，书中以一个典型的**3个Sentinel节点、1个主节点、2个从节点**组成的架构为例进行说明。
  *   **主节点**：127.0.0.1:6379。
  *   **从节点**：127.0.0.1:6380、127.0.0.1:6381。
  *   **Sentinel节点**：127.0.0.1:26379、127.0.0.1:26380、127.0.0.1:26381。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_24.png)

* 部署```Redis```数据节点，```Redis Sentinel```中的数据节点与普通的主从复制节点在配置上没有特殊区别。
  *   **启动主节点**：编写配置文件（如 `redis-6379.conf`），设置好端口、日志、工作目录等，使用 `redis-server` 启动。
  *   **启动从节点**：在从节点的配置文件中（如 `redis-6380.conf`）添加 `slaveof 127.0.0.1 6379` 配置，然后启动。
  *   **确认主从关系**：启动后，可以通过 `redis-cli` 执行 `info replication` 命令查看，主节点应显示有两个已连接的从节点，从节点应显示其主节点为6379。

* 部署```Sentinel```节点，```Sentinel```节点本质上是**特殊的Redis节点**，它们不存储数据，主要用于监控。
  *   **配置Sentinel**：典型的配置文件内容如下：
      ```text
      port 26379
      daemonize yes
      logfile "26379.log"
      dir /opt/soft/redis/data
      sentinel monitor mymaster 127.0.0.1 6379 2
      sentinel down-after-milliseconds mymaster 30000
      sentinel parallel-syncs mymaster 1
      sentinel failover-timeout mymaster 180000
      ```
      其中 `sentinel monitor mymaster 127.0.0.1 6379 2` 表示监控主节点，“2”代表判定主节点失败至少需要2个```Sentinel```节点同意，“```mymaster```”是主节点的别名。
  *   **启动Sentinel**：有两种等价方法：
      1. 使用 `redis-sentinel` 命令：`redis-sentinel redis-sentinel-26379.conf`。
      2. 使用 `redis-server` 加参数：`redis-server redis-sentinel-26379.conf --sentinel`。
  *   **确认状态**：使用 `info Sentinel` 命令可以查看，正常的```Sentinel```节点应能感知到主节点、从节点以及其他```Sentinel```节点的存在。

* 配置优化及参数详解，书中深入分析了Sentinel的核心配置参数：
  *   **`sentinel monitor <master-name> <ip> <port> <quorum>`**：
      *   **Quorum（票数）**：用于故障发现和判定。建议设置为```Sentinel```节点数的一半加1。
      *   **自动发现**：```Sentinel```只需配置主节点信息，它会通过主节点自动发现从节点和其他```Sentinel```节点，并动态更新配置文件。
  *   **`sentinel down-after-milliseconds`**：判定节点不可达的超时时间（毫秒）。设置过大会导致故障发现延迟，设置过小可能增加误判率。
  *   **`sentinel parallel-syncs`**：限制故障转移后，同时向新主节点发起复制操作的从节点个数。设为1可以降低主节点的网络和磁盘```IO```压力（轮询复制）。
  *   **`sentinel failover-timeout`**：作用于故障转移的各个阶段（如选出从节点、晋升主节点等），如果某阶段执行时间超过此值，则认为转移失败。
  *   **脚本通知**：
      *   `sentinel notification-script`：故障转移期间发生警告事件时触发的脚本，可用于邮件或短信报警。
      *   `sentinel client-reconfig-script`：故障转移结束后触发，用于通知应用方主节点已切换。
  *   **动态调整**：可以使用 `sentinel set <master-name> <param> <value>` 命令动态修改配置，且执行成功后会**立即刷新配置文件**。

* 部署技巧与实践建议
  *   **物理机隔离**：```Sentinel```节点不应部署在同一台物理机器上（包括同一物理机上的不同虚拟机或容器），以实现真正的高可用。
  *   **节点数量**：建议部署至少**3个且为奇数个**的```Sentinel```节点。奇数节点可以在满足“半数以上”选举条件的同时节省资源。
  *   **监控模式选择**：
      *   **方案一（一套Sentinel监控多个主节点）**：降低维护成本，但一旦```Sentinel```集合异常，会影响多个```Redis```应用，且网络连接较多。
      *   **方案二（每个主节点配置一套Sentinel）**：彼此隔离，更加安全，但会造成资源浪费。
      *   **建议**：如果监控的是同一业务的多个主节点，选方案一；否则建议采用方案二进行隔离。

### API

* 基础信息查询命令
  *   **`sentinel masters`**：展示所有被当前```Sentinel```节点监控的主节点状态及其相关的统计信息。
  *   **`sentinel master <master name>`**：展示指定名称的主节点状态及其相关统计信息。
  *   **`sentinel slaves <master name>`**：展示指定主节点属下的所有从节点状态及其相关统计信息。
  *   **`sentinel sentinels <master name>`**：展示监控该主节点的所有```Sentinel```节点集合，但不包含当前执行命令的这个```Sentinel```节点。
  *   **`sentinel get-master-addr-by-name <master name>`**：返回指定主节点的当前```IP```地址和端口号。

* 状态维护与配置操作命令
  *   **`sentinel reset <pattern>`**：对符合通配符风格的主节点配置进行重置。这包括清除主节点的相关状态（如故障转移状态），并触发```Sentinel```重新发现从节点和其他Sentinel节点。
  *   **`sentinel ckquorum <master name>`**：检查当前可达的```Sentinel```节点总数是否达到了配置的`<quorum>`票数。如果可达数不足，将无法进行自动故障转移，这意味着高可用特性将暂时失效。
  *   **`sentinel flushconfig`**：强制将当前```Sentinel```节点的配置刷新到磁盘上。这在外部原因（如磁盘损坏）导致配置文件损坏或丢失时非常有用。
  *   **`sentinel set <master name> <param> <value>`**：动态修改```Sentinel```节点的配置选项。该命令执行成功后会立即刷新配置文件，且仅对当前执行命令的```Sentinel```节点有效。

* 监控节点的动态管理
  *   **`sentinel remove <master name>`**：取消当前```Sentinel```节点对指定主节点的监控。需要注意，此操作仅在当前执行命令的节点上生效。
  *   **`sentinel monitor <master name> <ip> <port> <quorum>`**：通过命令形式让```Sentinel```节点开始监控一个新的主节点，其参数含义与配置文件中的相同。

* 故障转移相关命令
  *   **`sentinel failover <master name>`**：对指定主节点发起**强制故障转移**，而不需要与其他```Sentinel```节点进行协商。故障转移完成后，其他```Sentinel```节点会根据结果自动更新自身的配置。该命令在日常运维（如计划内的设备维护或主节点迁移）中非常有用。
  *   **`sentinel is-master-down-by-addr`**：这是```Sentinel```节点之间用于交换对主节点下线判断的内部```API```。根据参数不同，它还可以作为```Sentinel```领导者选举的通信方式。

* 客户端连接与支持
  * 作者特别强调，为了使```Redis Sentinel```发挥作用，客户端必须显式支持```Sentinel```协议。客户端在初始化时不再直接连接```Redis```数据节点，而是连接```Sentinel```节点集合，并通过`sentinel get-master-addr-by-name`获取当前真正的主节点信息。在```Java```环境下，可以使用`JedisSentinelPool`来实现这一逻辑。

### 客户端连接

* 客户端仍然像主从复制模式那样直接连接主节点的```IP```和端口，那么在主节点发生故障转移后，客户端将无法感知新主节点的变化，从而导致服务不可用。因此，各个语言的客户端需要显式支持```Redis Sentinel```。

* ```Redis Sentinel```客户端的基本概念，```Redis Sentinel```集成了监控、通知、自动故障转移和配置提供者等功能。实际上，**Sentinel节点集合才是最了解主节点信息的来源**。
  *   **核心标识**：各个主节点通过`master-name`进行标识。
  *   **必要参数**：无论使用何种编程语言，正确连接```Redis Sentinel```必须具备两个参数：**Sentinel节点集合**和**masterName**。

* ```Redis Sentinel```客户端的实现原理，实现一个支持```Redis Sentinel```的客户端通常遵循以下四个基本步骤：
  *  **获取可用节点**：遍历```Sentinel```节点集合，获取一个可用的```Sentinel```节点。由于```Sentinel```节点之间共享数据，从任意一个可用的```Sentinel```节点获取主节点信息都是可行的。
  *  **查询主节点信息**：通过```Sentinel```提供的```API``` `sentinel get-master-addr-by-name master-name` 来获取当前主节点的```IP```地址和端口。
  *  **角色验证**：在获取到“主节点”信息后，客户端会通过 `role` 或 `info replication` 命令验证该节点是否真的是主节点。这一步是为了防止在故障转移期间，获取到的是过时或发生变化的信息。
  *  **订阅变更通知**：客户端会保持与```Sentinel```节点集合的联系，**订阅Sentinel节点上的 `+switch-master` 频道**。一旦```Sentinel```完成了故障转移并发布了切换主节点的消息，客户端能够立刻感知并自动切换连接。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_25.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_26.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_27.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_28.png)

* ```Java```客户端```Jedis```的操作实践，书中以```Java```客户端```Jedis```（版本2.8.2）为例，介绍了具体的实现方法。```Jedis```提供了 **`JedisSentinelPool`** 类来支持```Sentinel```模式。
  * ```JedisSentinelPool```的初始化，初始化时需要传入 `masterName`、`sentinels` 集合、连接池配置（`poolConfig`）以及超时时间等参数。
    *   **代码示例**：
        ```java
        JedisSentinelPool jedisSentinelPool = new JedisSentinelPool(masterName, sentinelSet, poolConfig, timeout);
        ```
    *   **获取资源**：使用方式与普通连接池类似，通过 `getResource()` 获取```Jedis```对象，使用完后调用 `close()` 将其归还给连接池。
  * ```JedisSentinelPool```的内部实现逻辑
    1.  **initSentinels**：在初始化时，```Jedis```会遍历```Sentinel```节点，执行 `sentinelGetMasterAddrByName` 找到主节点信息。
    2.  **MasterListener**：```Jedis```会为每一个```Sentinel```节点单独启动一个名为 `MasterListener` 的线程。
    3.  **发布订阅**：这些线程的核心任务是订阅```Sentinel```节点的 `+switch-master` 频道。
    4.  **自动重连**：当 `+switch-master` 频道接收到消息时（消息包含新的主节点IP和端口），`MasterListener` 会调用 `initPool` 方法重新初始化连接池，从而实现对新主节点的连接。

* 关键点总结
  *   **配置发现服务**：在```Redis Sentinel```架构中，客户端应将```Sentinel```节点集合视为**配置发现服务**，而非简单的连接目标。
  *   **全局唯一性**：在实际开发中，建议 `JedisSentinelPool` 尽可能在全局范围内只有一个实例。
  *   **API限制**：```Sentinel```节点本身是特殊的```Redis```节点，它们不存储数据，仅支持如 `ping`、`sentinel`、`subscribe`、`publish`、`info`、`role` 等有限的命令。