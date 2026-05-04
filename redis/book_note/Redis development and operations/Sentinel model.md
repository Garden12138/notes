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