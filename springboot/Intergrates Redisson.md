## SpringBoot 集成 Redisson

> 简介

* ```Redisson```是基于```Redis```实现的```Java```驻内存数据网格客户端，不仅提供了一系列```Redis```常用数据结构命令服务，还提供如分布式锁、分布式对象、分布式集合、分布式远程服务以及分布式调度任务服务等高级功能。

> 集成步骤

* 引入依赖：

  ```bash
  <!-- redisson -->
  <dependency>
      <groupId>org.redisson</groupId>
      <artifactId>redisson</artifactId>
      <version>${redisson.version}</version>
  </dependency>
  ```

  ```Redisson```版本选择需与```SpringBoot```版本相对应，```SpringBoot2.x```对应```Redisson2.x```，```SpringBoot3.x```对应```Redisson3.x```。

* 新增```Redisson```配置类：

  ```bash
  @Configuration
  public class RedissonConfig {

      /**
       * redisson客户端
       * @return
       * @throws IOException
       */
        @Bean(destroyMethod = "shutdown")
        public RedissonClient redissonClient() throws IOException {
            //Config config = Config.fromYAML(new ClassPathResource("master-slave-redisson.yaml").getInputStream());
            //Config config = Config.fromYAML(new ClassPathResource("sentinel-redisson.yaml").getInputStream());
            //Config config = Config.fromYAML(new ClassPathResource("cluster-redisson.yaml").getInputStream());
            Config config = Config.fromYAML(new ClassPathResource("standalone-redisson.yaml").getInputStream());
            return Redisson.create(config);
        }

  }
  ```

  单例配置如：

  ```bash
  # standalone-redisson.yaml
  singleServerConfig:
    # 连接空闲超时。若当前连接池里的连接数量超过最小空闲连接数，且连接空闲时间超过该数值，那么这些连接将会自动被关闭，并从连接池里移除，时间单位是毫秒。
    idleConnectionTimeout: 10000
    # 连接超时。与任何节点建立连接的等待超时，时间单位是毫秒。
    connectTimeout: 10000
    # 命令等待超时时间。从命令发送成功时开始计，等待节点回复命令的时间，时间单位是毫秒。
    timeout: 3000
    # 命令失败重试次数。若尝试达到命令失败重试次数（retryAttempts）仍不能将命令发送至某个指定节点，将抛出错误；若尝试在此限制内发送成功，则开启命令等待超时时间（timeout）计时。
    retryAttempts: 3
    # 命令重试发送时间间隔，单位为毫秒。执行另一次尝试发送redis命令的时间间隔。
    retryInterval: 1500
    # redis服务的认证密码
    password: ${password}
    # 每个连接最大订阅数量
    subscriptionsPerConnection: 5
    # 客户端名称。在Redis节点里显示的客户端名称。
    clientName: null
    # 节点的可访问地址
    address: "redis://114.132.78.39:6379"
    # 发布和订阅连接的最小空闲连接数
    subscriptionConnectionMinimumIdleSize: 1
    # 发布和订阅连接池大小
    subscriptionConnectionPoolSize: 50
    # （非发布和订阅）连接的最小空闲连接数
    connectionMinimumIdleSize: 24
    # （非发布和订阅）连接池大小
    connectionPoolSize: 64
    # 数据库
    database: 0
    dnsMonitoringInterval: 5000
  # 线程池数量。被所有RTopic对象监听器，RRemoteService调用者和RExecutorService任务共同共享。
  threads: 16
  # 线程池数量。这个线程池数量是在Redisson实例内，被其创建的所有分布式数据类型和服务，以及底层客户端所一同共享的线程池里保存的线程数量。
  nettyThreads: 32
  # Redisson的对象编码类是用于将对象进行序列化和反序列化，以实现对该对象在Redis里的读取和存储。
  codec: !<org.redisson.codec.JsonJacksonCodec> {}
  # 通道模式。ransportMode.NIO;TransportMode.EPOLL（Linux）;TransportMode.KQUEUE（macOS）
  transportMode: "NIO"
  ```

  主从复制模式如：

  ```bash
  # master-slave-redisson.yaml
  masterSlaveServersConfig:
    # 连接空闲超时。若当前连接池里的连接数量超过最小空闲连接数，且连接空闲时间超过该数值，那么这些连接将会自动被关闭，并从连接池里移除，时间单位是毫秒。
    idleConnectionTimeout: 10000
    # 连接超时。与任何节点建立连接的等待超时，时间单位是毫秒。
    connectTimeout: 10000
    # 命令等待超时时间。从命令发送成功时开始计，等待节点回复命令的时间，时间单位是毫秒。
    timeout: 3000
    # 命令失败重试次数。若尝试达到命令失败重试次数（retryAttempts）仍不能将命令发送至某个指定节点，将抛出错误；若尝试在此限制内发送成功，则开启命令等待超时时间（timeout）计时。
    retryAttempts: 3
    # 命令重试发送时间间隔，单位为毫秒。执行另一次尝试发送redis命令的时间间隔。
    retryInterval: 1500
    # 执行失败尝试次数。在某个节点执行相同或不同命令时，达到执行失败尝试次数（failedAttempts）时，该节点将被从可用节点列表里清除，直到重新连接时间间隔（reconnectionTimeout）超时以后再次尝试。
    failedAttempts: 3
    # redis服务的认证密码
    password: ${password}
    # 每个连接最大订阅数量
    subscriptionsPerConnection: 5
    # 客户端名称。在Redis节点里显示的客户端名称。
    clientName: null
    # 负载策略。WeightedRoundRobinBalancer为权重轮询调度算法；RoundRobinLoadBalancer为轮询调度算法；RandomLoadBalancer为随机调度算法
    loadBalancer: !<org.redisson.connection.balancer.RoundRobinLoadBalancer> {}
    # 从节点发布和订阅连接的最小空闲连接数
    slaveSubscriptionConnectionMinimumIdleSize: 1
    # 从节点发布和订阅连接池大小
    slaveSubscriptionConnectionPoolSize: 50
    # 从节点（非发布和订阅）连接的最小空闲连接数
    slaveConnectionMinimumIdleSize: 32
    # 从节点（非发布和订阅）连接池大小
    slaveConnectionPoolSize: 64
    # 主节点（非发布和订阅）连接的最小空闲连接数
    masterConnectionMinimumIdleSize: 32
    # 主节点（非发布和订阅）连接池大小
    masterConnectionPoolSize: 64
    # 设置读取操作选择节点的模式。SLAVE为只在从服务节点里读取。MASTER为只在主服务节点里读取。MASTER_SLAVE为在主从服务节点里都可以读取。
    readMode: "SLAVE"
    # 从节点的可访问地址
    slaveAddresses:
      - "redis://114.132.78.39:16377"
      - "redis://114.132.78.39:16378"
    # 主节点的可访问地址
    masterAddress: "redis://114.132.78.39:16379"
    # 数据库
    database: 0
  # 线程池数量。被所有RTopic对象监听器，RRemoteService调用者和RExecutorService任务共同共享。
  threads: 0
  # 线程池数量。这个线程池数量是在Redisson实例内，被其创建的所有分布式数据类型和服务，以及底层客户端所一同共享的线程池里保存的线程数量。
  nettyThreads: 0
  # Redisson的对象编码类是用于将对象进行序列化和反序列化，以实现对该对象在Redis里的读取和存储。
  codec: !<org.redisson.codec.JsonJacksonCodec> {}
  # 通道模式。ransportMode.NIO;TransportMode.EPOLL（Linux）;TransportMode.KQUEUE（macOS）
  transportMode: "NIO"
  ```

  哨兵模式如：

  ```bash
  # sentinel-redisson.yaml
  sentinelServersConfig:
    # 连接空闲超时。若当前连接池里的连接数量超过最小空闲连接数，且连接空闲时间超过该数值，那么这些连接将会自动被关闭，并从连接池里移除，时间单位是毫秒。
    idleConnectionTimeout: 10000
    # 连接超时。与任何节点建立连接的等待超时，时间单位是毫秒。
    connectTimeout: 10000
    # 命令等待超时时间。从命令发送成功时开始计，等待节点回复命令的时间，时间单位是毫秒。
    timeout: 3000
    # 命令失败重试次数。若尝试达到命令失败重试次数（retryAttempts）仍不能将命令发送至某个指定节点，将抛出错误；若尝试在此限制内发送成功，则开启命令等待超时时间（timeout）计时。
    retryAttempts: 3
    # 命令重试发送时间间隔，单位为毫秒。执行另一次尝试发送redis命令的时间间隔。
    retryInterval: 1500
    # redis服务的认证密码
    password: ${password}
    # 每个连接最大订阅数量
    subscriptionsPerConnection: 5
    # 客户端名称。在Redis节点里显示的客户端名称。
    clientName: null
    # 负载策略。WeightedRoundRobinBalancer为权重轮询调度算法；RoundRobinLoadBalancer为轮询调度算法；RandomLoadBalancer为随机调度算法
    loadBalancer: !<org.redisson.connection.balancer.RoundRobinLoadBalancer> {}
    # 从节点发布和订阅连接的最小空闲连接数
    slaveSubscriptionConnectionMinimumIdleSize: 1
    # 从节点发布和订阅连接池大小
    slaveSubscriptionConnectionPoolSize: 50
    # 从节点（非发布和订阅）连接的最小空闲连接数
    slaveConnectionMinimumIdleSize: 32
    # 从节点（非发布和订阅）连接池大小
    slaveConnectionPoolSize: 64
    # 主节点（非发布和订阅）连接的最小空闲连接数
    masterConnectionMinimumIdleSize: 32
    # 主节点（非发布和订阅）连接池大小
    masterConnectionPoolSize: 64
    # 设置读取操作选择节点的模式。SLAVE为只在从服务节点里读取。MASTER为只在主服务节点里读取。MASTER_SLAVE为在主从服务节点里都可以读取。
    readMode: "SLAVE"
    # 哨兵集群可访问地址
    sentinelAddresses:
      - "redis://114.132.78.39:26377"
      - "redis://114.132.78.39:26378"
      - "redis://114.132.78.39:26379"
    # 哨兵集群中所设置的主服务器名称
    masterName: "mymaster"
    # 数据库
    database: 0
  # 线程池数量。被所有RTopic对象监听器，RRemoteService调用者和RExecutorService任务共同共享。
  threads: 0
  # 线程池数量。这个线程池数量是在Redisson实例内，被其创建的所有分布式数据类型和服务，以及底层客户端所一同共享的线程池里保存的线程数量。
  nettyThreads: 0
  # Redisson的对象编码类是用于将对象进行序列化和反序列化，以实现对该对象在Redis里的读取和存储。
  codec: !<org.redisson.codec.JsonJacksonCodec> {}
  # 通道模式。ransportMode.NIO;TransportMode.EPOLL（Linux）;TransportMode.KQUEUE（macOS）
  transportMode: "NIO"
  ```

  集群模式如：

  ```bash
  # cluster-redisson.yaml
  clusterServersConfig:
    # 连接空闲超时。若当前连接池里的连接数量超过最小空闲连接数，且连接空闲时间超过该数值，那么这些连接将会自动被关闭，并从连接池里移除，时间单位是毫秒。
    idleConnectionTimeout: 10000
    # 连接超时。与任何节点建立连接的等待超时，时间单位是毫秒。
    connectTimeout: 10000
    # 命令等待超时时间。从命令发送成功时开始计，等待节点回复命令的时间，时间单位是毫秒。
    timeout: 3000
    # 命令失败重试次数。若尝试达到命令失败重试次数（retryAttempts）仍不能将命令发送至某个指定节点，将抛出错误；若尝试在此限制内发送成功，则开启命令等待超时时间（timeout）计时。
    retryAttempts: 3
    # 命令重试发送时间间隔，单位为毫秒。执行另一次尝试发送redis命令的时间间隔。
    retryInterval: 1500
    # 失败从节点重新连接时间间隔，单位为毫秒。
    failedSlaveReconnectionInterval: 3000
    # 失败从节点检查时间间隔，单位为毫秒。
    failedSlaveCheckInterval: 60000
    # redis服务的认证密码
    password: ${password}
    # 每个连接最大订阅数量
    subscriptionsPerConnection: 5
    # 客户端名称。在Redis节点里显示的客户端名称。
    clientName: null
    # 负载策略。WeightedRoundRobinBalancer为权重轮询调度算法；RoundRobinLoadBalancer为轮询调度算法；RandomLoadBalancer为随机调度算法
    loadBalancer: !<org.redisson.connection.balancer.RoundRobinLoadBalancer> {}
    # 从节点发布和订阅连接的最小空闲连接数
    subscriptionConnectionMinimumIdleSize: 1
    # 从节点发布和订阅连接池大小
    subscriptionConnectionPoolSize: 50
    # 从节点（非发布和订阅）连接的最小空闲连接数
    slaveConnectionMinimumIdleSize: 24
    # 从节点（非发布和订阅）连接池大小
    slaveConnectionPoolSize: 64
    # 主节点（非发布和订阅）连接的最小空闲连接数
    masterConnectionMinimumIdleSize: 24
    # 主节点（非发布和订阅）连接池大小
    masterConnectionPoolSize: 64
    # 设置读取操作选择节点的模式。SLAVE为只在从服务节点里读取。MASTER为只在主服务节点里读取。MASTER_SLAVE为在主从服务节点里都可以读取。
    readMode: "SLAVE"
    # 设置订阅操作选择节点的模式。SLAVE为只在从服务节点里订阅。MASTER为只在主服务节点里订阅。
    subscriptionMode: "SLAVE"
    # 集群节点的可访问地址
    nodeAddresses:
      - "redis://114.132.78.39:6379"
      - "redis://114.132.78.39:6378"
      - "redis://114.132.78.39:6377"
      - "redis://114.132.78.39:6376"
      - "redis://114.132.78.39:6375"
      - "redis://114.132.78.39:6374"
    # 扫描间隔时间，单位为毫秒。
    scanInterval: 1000
    # ping命令连接间隔时间，单位为毫秒。
    pingConnectionInterval: 30000
    # 是否启用tcp活性连接
    keepAlive: false
    # 是否启用tcp非延迟连接
    tcpNoDelay: true
  # 线程池数量。被所有RTopic对象监听器，RRemoteService调用者和RExecutorService任务共同共享。
  threads: 16
  # 线程池数量。这个线程池数量是在Redisson实例内，被其创建的所有分布式数据类型和服务，以及底层客户端所一同共享的线程池里保存的线程数量。
  nettyThreads: 32
  # Redisson的对象编码类是用于将对象进行序列化和反序列化，以实现对该对象在Redis里的读取和存储。
  codec: !<org.redisson.codec.JsonJacksonCodec> {}
  # 通道模式。ransportMode.NIO;TransportMode.EPOLL（Linux）;TransportMode.KQUEUE（macOS）
  transportMode: "NIO"
  ```

* 使用时依赖注入：

  ```bash
  @Autowired
  private RedissonClient redissonClient;
  ```

> 参考文献

* [Redisson Spring Boot Starter](https://github.com/redisson/redisson/tree/master/redisson-spring-boot-starter)
* [【进阶篇】Redis实战之Redisson使用技巧详解，干活！](https://ost.51cto.com/posts/20654)