## SpringBoot 集成 Redis 锁

> 集成```Redis```单机锁

* [集成```Redis（lettuce）```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis.md)

* 编写工具类：

  ```bash
  @Slf4j
  @Component
  public class RedisDistributedLockUtil {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * 使用ThreadLocal记录锁的唯一标识
     */
    private static final ThreadLocal<String> LOCK_FLAG = new ThreadLocal<>();

    /**
     * 创建锁的Lua脚本
     */
    private static final String LOCK_LUA_SCRIPT =
            "if redis.call('setnx', KEYS[1], ARGV[1]) == 1 then " +
                    "redis.call('pexpire', KEYS[1], ARGV[2]); " +
                    "return true; " +
                    "else return false; " +
                    "end";

    /**
     * 释放锁的Lua脚本
     */
    private static final String UNLOCK_LUA_SCRIPT =
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "redis.call('del', KEYS[1]); " +
                    "return true; " +
                    "else return false; " +
                    "end";

    /**
     * 单机版创建锁
     *
     * @param key
     * @param expire
     * @return
     */
    public boolean singleLock(String key, long expire) {
        String uuid = UUID.randomUUID().toString();
        try {
            String[] keys = {key};
            String[] args = {uuid, String.valueOf(expire)};
            RedisScript<Boolean> script = new DefaultRedisScript<>(LOCK_LUA_SCRIPT, Boolean.class);
            LOCK_FLAG.set(uuid);
            Boolean result = redisTemplate.execute(script, Arrays.asList(keys), args);
            return result != null && result;
        } catch (Exception e) {
            log.error("singleLock occurred an exception: {}, key : {}", e.getMessage(), key);
            LOCK_FLAG.remove();
        }
        return false;
    }

    /**
     * 单机版创建锁，支持重试
     *
     * @param key           key
     * @param expire        失效时间
     * @param retryTimes    重试次数
     * @param retryDuration 重试间隔
     * @return
     */
    public boolean singleLock(String key, long expire, int retryTimes, long retryDuration) {
        boolean result = singleLock(key, expire);
        while (!(result) && retryTimes-- > 0) {
            try {
                log.info("singleLock failed, key {} retryTimes {} retrying...", key, retryTimes);
                Thread.sleep(retryDuration);
            } catch (Exception e) {
                log.error("singleLock retry occurred an exception: {}, key: {}", e.getMessage(), key);
                return false;
            }
            result = singleLock(key, expire);
        }
        return result;
    }

    /**
     * 单机版释放锁
     *
     * @param key
     * @return
     */
    public boolean singleUnlock(String key) {
        boolean success = false;
        try {
            String[] keys = {key};
            String[] args = {LOCK_FLAG.get()};
            RedisScript<Boolean> script = new DefaultRedisScript<>(UNLOCK_LUA_SCRIPT, Boolean.class);
            success = redisTemplate.execute(script, Arrays.asList(keys), args);
        } catch (Exception e) {
            log.error("release single lock occurred an exception: {}, key: {}", e.getMessage(), key);
        } finally {
            if (success) {
                LOCK_FLAG.remove();
            }
        }
        return success;
    }

  }
  ```

> 集成```Redis```集群锁

* 引入```redisson```依赖（```SpringBoot3.x```对应```Redisson3.x```、```SpringBoot2.x```对应```Redisson2.x```）：

  ```bash
  <properties>
      <redisson.version>2.15.2</redisson.version>
  </properties>
  <!-- redisson -->
  <dependency>
      <groupId>org.redisson</groupId>
      <artifactId>redisson</artifactId>
      <version>${redisson.version}</version>
  </dependency>
  ```

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
          Config config = Config.fromYAML(new ClassPathResource("master-slave-redisson.yaml").getInputStream());
      //    Config config = Config.fromYAML(new ClassPathResource("sentinel-redisson.yaml").getInputStream());
      //    Config config = Config.fromYAML(new ClassPathResource("cluster-redisson.yaml").getInputStream());
          return Redisson.create(config);
      }

  }
  ```

* 编写集群配置文件：

  * 主从复制模式```master-slave-redisson.yaml```：

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

  * 哨兵模式```sentinel-redisson.yaml```：

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

  * 集群主从复制模式```cluster-redisson.yaml```：

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

* 编写工具类：

  ```bash
  @Slf4j
  @Component
  public class RedisDistributedLockUtil {

    /**
     * 集群版创建锁
     *
     * @param key
     * @param expire
     * @return
     */
    public boolean distributedLock(String key, long expire) {
        RLock lock = redissonClient.getLock(key);
        try {
            return lock.tryLock(expire, TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            log.error("distributedLock occurred an exception: {}, key : {}", e.getMessage(), key);
            Thread.currentThread().interrupt();
            return false;
        }
    }

    /**
     * 集群版创建锁，支持重试
     *
     * @param key
     * @param expire
     * @param retryTimes
     * @param retryDuration
     * @return
     */
    public boolean distributedLock(String key, long expire, int retryTimes, long retryDuration) {
        boolean result = distributedLock(key, expire);
        while (!(result) && retryTimes-- > 0) {
            try {
                log.info("distributedLock failed, key {} retryTimes {} retrying...", key, retryTimes);
                Thread.sleep(retryDuration);
            } catch (Exception e) {
                log.error("distributedLock retry occurred an exception: {}, key: {}", e.getMessage(), key);
                return false;
            }
            result = singleLock(key, expire);
        }
        return result;
    }

    /**
     * 集群版释放锁
     *
     * @param key
     * @return
     */
    public boolean distributedUnLock(String key) {
        boolean success = false;
        try {
            RLock lock = redissonClient.getLock(key);
            if (lock.isLocked()) {
                lock.unlock();
                success = true;
            }
        } catch (Exception e) {
            log.error("release distributed lock occurred an exception: {}, key: {}", e.getMessage(), key);
        }
        return success;
    }

  }
  ```

* 可使用注解封装分布式锁：

  * 定义注解：

    ```bash
    @Target({ElementType.METHOD})
    @Retention(RetentionPolicy.RUNTIME)
    @Inherited
    public @interface RedisLock {

        /**
         * redis key
         *
         * @return
         */
        String value() default "";

        /**
         * 过期时间
         *
         * @return mills
         */
        long expireMills() default 30000;

        /**
         * 重试次数
         *
         * @return retry times
         */
        int retryTimes() default 0;

        /**
         * 重试间隔
         *
         * @return mills
         */
        long retryDurationMills() default 200;
  
        /**
         * 模式：single为单机，distributed为集群
         *
         * @return
         */
        String model() default "single";

    }
    ```

  * 定义切面拦截处理注解：

    ```bash
    @Slf4j
    @Aspect
    @Configuration
    public class RedisLockAspect {

        @Autowired
        private RedisDistributedLockUtil redisDistributedLockUtil;


        /**
         * 环绕redis单机版锁切面
         *
         * @param pjp
         * @return
         * @throws Throwable
         */
        @Around("@annotation(com.garden.redis.annotation.RedisLock)")
        public Object aroundRedisLock(ProceedingJoinPoint pjp) throws Throwable {
            Method method = ((MethodSignature) pjp.getSignature()).getMethod();
            RedisLock redisLock = method.getAnnotation(RedisLock.class);
            String key = redisLock.value();
            if (StringUtils.isEmpty(key)) {
                Object[] args = pjp.getArgs();
                key = Arrays.toString(args);
            }
            String model = redisLock.model();
            // 创建锁
            boolean lock = "distributed".equals(model)
                    ? redisDistributedLockUtil.distributedLock(key, redisLock.expireMills(), redisLock.retryTimes(), redisLock.retryDurationMills())
                    : redisDistributedLockUtil.singleLock(key, redisLock.expireMills(), redisLock.retryTimes(), redisLock.retryDurationMills());
            if (!lock) {
                log.error("get lock failed, key: {}", key);
                return null;
            }
            // 执行方法后释放锁
            log.info("get lock success, key: {}", key);
            try {
                return pjp.proceed();
            } catch (Exception e) {
                log.error("execute locked method occurred an exception: {}, key: {}", e.getMessage(), key);
            } finally {
                boolean releaseResult = "distributed".equals(model)
                        ? redisDistributedLockUtil.distributedUnLock(key)
                        : redisDistributedLockUtil.singleUnlock(key);
                log.info("release lock success: {}, key: {}", releaseResult, key);
            }
            return null;
        }

    }
    ```

  * 测试使用注解，如：

    ```bash
    @Slf4j
    @RestController
    @RefreshScope
    public class ConsumerController {
        
        /**
         * ab -n 10 -c 10 http://localhost:8763/redisSingleLock?key=user:garden
         *
         * @param key
         * @return
         */
        @GetMapping("/redisSingleLock")
        @RedisLock(retryTimes = 3)
        public Boolean redisSingleLock(@RequestParam String key) {
            log.info("redisSingleLock method doing...");
            try {
                log.info("thread {} is sleeping,", Thread.currentThread().getName());
                Thread.sleep(5000);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            return true;
        }

        /**
         * ab -n 20 -c 10 http://localhost:8763/redisDistributedLock?key=user:garden
         *
         * @param key
         * @return
         */
        @GetMapping("/redisDistributedLock")
        @RedisLock(retryTimes = 3, model = "distributed")
        public Boolean redisDistributedLock(@RequestParam String key) {
            log.info("redisDistributedLock method doing...");
            try {
                log.info("thread {} is sleeping,", Thread.currentThread().getName());
                Thread.sleep(5000);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            return true;
        }

    }
    ```

> 参考文献

* [springboot集成redis 分布式锁(redistemplate,lua,redisson)](https://segmentfault.com/a/1190000043489696)
* [基于redis如何实现分布式锁？有什么缺陷？](https://pdai.tech/md/arch/arch-z-lock.html#%E5%9F%BA%E4%BA%8Eredlock%E5%AE%9E%E7%8E%B0%E5%88%86%E5%B8%83%E5%BC%8F%E9%94%81)
* [redisson trylock 一直返回true redisson trylock原理](https://blog.51cto.com/u_12929/6528527)
* [redisson-spring-boot-starter](https://github.com/redisson/redisson/tree/master/redisson-spring-boot-starter)
* [redisson configuration](https://github.com/redisson/redisson/wiki/2.-Configuration)
* [redisson 配置方法](https://github.com/redisson/redisson/wiki/2.-%E9%85%8D%E7%BD%AE%E6%96%B9%E6%B3%95)