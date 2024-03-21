## SpringBoot 集成 Redis 主从

> 简介

* 主从复制模式由主服务器与从服务器组成，经常使用“一主二从”的模式。主服务器可进行读写操作（客户端请求），当发生写操作时自动将写操作同步至从服务器，而从服务器接收并执行主服务器同步的写操作命令，但从服务器一般只进行读操作（客户端请求）。通过主从服务器间的读写分离以及复制方式实现多台服务器的数据一致性。

> 背景

* ```SpringBoot```通过```application```配置实现```Redis```集群目前只支持```Sentinel```以及```Cluster```模式。对于常用的主从复制模式则需自定义实现。

> 实现思路

* 启动时获取```Redis```主从配置环境变量。
* 启动时动态创建```Redis```主从不同的```Bean```。
* ```Redis```封装工具```Bean```在初始化时动态注入主从不同的```Bean```。
* ```Redis```封装工具对于写操作使用主```Bean```，对于读操作使用从```Bean```。

> 搭建步骤

* 引入依赖：

  ```bash
  <!-- springboot data redis 2.x版本默认使用lettuce实现 -->
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-redis</artifactId>
  </dependency>
  <!-- apache common pool lettuce实现结合连接池-->
  <dependency>
      <groupId>org.apache.commons</groupId>
      <artifactId>commons-pool2</artifactId>
  </dependency>
  ```

* 新增```Redis```主从配置：

  ```bash
  garden:
  redis:
    master-slave:
      bean-class: org.springframework.data.redis.core.RedisTemplate
      nodes:
        - name: master
          host: 114.132.78.39
          port: 16379
          password: ${password}
          database: 0
          lettuce-pool-max-active: 8
          lettuce-pool-max-wait: 10000
          lettuce-pool-max-idle: 8
          lettuce-pool-min-idle: 0
        - name: slave1
          host: 114.132.78.39
          port: 16378
          password: ${password}
          database: 0
          lettuce-pool-max-active: 8
          lettuce-pool-max-wait: 10000
          lettuce-pool-max-idle: 8
          lettuce-pool-min-idle: 0
        - name: slave2
          host: 114.132.78.39
          port: 16377
          password: ${password}
          database: 0
          lettuce-pool-max-active: 8
          lettuce-pool-max-wait: 10000
          lettuce-pool-max-idle: 8
          lettuce-pool-min-idle: 0
  ```

* 新增```Redis```主从配置类：

  ```bash
  @Data
  public class GardenRedisMasterSlaveProperties {

    private Class<?> beanClass;

    private List<GardenRedisMasterSlaveNode> nodes;

    @Data
    public static class GardenRedisMasterSlaveNode {

        private String name;
        private String host;
        private Integer port;
        private String password;
        private Integer database;
        private Integer lettucePoolMaxActive;
        private Long lettucePoolMaxWait;
        private Integer lettucePoolMaxIdle;
        private Integer lettucePoolMinIdle;

    }
  }
  ```

* 新增```Redis```主从不同```Bean```的注册类：

  ```bash
  @Slf4j
  @Component
  public class MSRedisTemplateBeanDefinitionRegistryPostProcessor implements BeanDefinitionRegistryPostProcessor, EnvironmentAware {

      private GardenRedisMasterSlaveProperties gardenRedisMasterSlaveProperties;

      @Override
      public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry beanDefinitionRegistry) throws BeansException {
          List<GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode> nodes = gardenRedisMasterSlaveProperties.getNodes();
          for (GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode node : nodes) {
              GenericBeanDefinition beandefinition = new GenericBeanDefinition();
              beandefinition.setBeanClass(gardenRedisMasterSlaveProperties.getBeanClass());
              GenericObjectPoolConfig poolConfig = localPoolConfig(node.getLettucePoolMaxActive(), node.getLettucePoolMaxIdle(), node.getLettucePoolMaxWait(), node.getLettucePoolMinIdle());
              RedisStandaloneConfiguration redisConfig = localRedisConfig(node.getHost(), node.getPort(), node.getPassword(), node.getDatabase());
              LettuceConnectionFactory connectionFactory = localLettuceConnectionFactory(redisConfig, poolConfig);
              beandefinition.getPropertyValues().add("connectionFactory", connectionFactory);
              beandefinition.getPropertyValues().add("keySerializer", keySerializer());
              beandefinition.getPropertyValues().add("hashKeySerializer", keySerializer());
              beandefinition.getPropertyValues().add("valueSerializer", valueSerializer());
              beandefinition.getPropertyValues().add("hashValueSerializer", valueSerializer());
              beanDefinitionRegistry.registerBeanDefinition(node.getName(), beandefinition);
              log.info("bean : {} registry success", node.getName());
          }
      }

      @Override
      public void postProcessBeanFactory(ConfigurableListableBeanFactory configurableListableBeanFactory) throws BeansException {
      }

      @Override
      public void setEnvironment(Environment environment) {
          BindResult<GardenRedisMasterSlaveProperties> bindResult = Binder.get(environment).bind("garden.redis.master-slave", GardenRedisMasterSlaveProperties.class);
          gardenRedisMasterSlaveProperties = bindResult.get();
      }

      public GardenRedisMasterSlaveProperties getGardenRedisMasterSlaveProperties() {
          return this.gardenRedisMasterSlaveProperties;
      }

      /**
       * 连接池属性
       *
       * @param maxActive
       * @param maxIdle
       * @param maxWait
       * @param minIdle
       * @return
       */
      private GenericObjectPoolConfig localPoolConfig(Integer maxActive, Integer maxIdle, Long maxWait, Integer minIdle) {
          GenericObjectPoolConfig config = new GenericObjectPoolConfig();
          config.setMaxTotal(maxActive);
          config.setMaxIdle(maxIdle);
          config.setMinIdle(minIdle);
          config.setMaxWaitMillis(maxWait);
          return config;
      }

      /**
       * Redis单例配置
       *
       * @param host
       * @param port
       * @param password
       * @param database
       * @return
       */
      private RedisStandaloneConfiguration localRedisConfig(String host, Integer port, String password, Integer database) {
          RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
          config.setHostName(host);
          config.setPassword(RedisPassword.of(password));
          config.setPort(port);
          config.setDatabase(database);
          return config;
      }

      /**
       * 根据连接池配置、Redis单例配置创建连接工厂
       *
       * @param localRedisConfig
       * @param localPoolConfig
       * @return
       */
      private LettuceConnectionFactory localLettuceConnectionFactory(RedisStandaloneConfiguration localRedisConfig,
                                                                         GenericObjectPoolConfig localPoolConfig) {
          LettuceClientConfiguration clientConfig =
                  LettucePoolingClientConfiguration.builder().commandTimeout(Duration.ofMillis(100))
                          .poolConfig(localPoolConfig).build();
          LettuceConnectionFactory factory = new LettuceConnectionFactory(localRedisConfig, clientConfig);
          factory.afterPropertiesSet();
          return factory;
      }

      /**
       * key 序列化方式
       */
      private RedisSerializer<String> keySerializer() {
          return new StringRedisSerializer();
      }

      /**
       * value 序列化方式
       */
      private RedisSerializer<Object> valueSerializer() {
          return new GenericJackson2JsonRedisSerializer();
      }


  }
  ```

* 新增```Redis```封装工具类，完整代码参考[这里](https://gitee.com/FSDGarden/microservices-spring/blob/feature/sc-2020.0.1-v1/common/common-redis/src/main/java/com/garden/redis/utils/RedisMasterSlaveUtil.java)：

  ```bash
  @Component
  public class RedisMasterSlaveUtil {
      
      private final MSRedisTemplateBeanDefinitionRegistryPostProcessor msRedisTemplateBeanDefinitionRegistryPostProcessor;
      private final ApplicationContext applicationContext;
      private RedisTemplate<String, Object> master;
      private List<RedisTemplate<String, Object>> slaves;

      public RedisMasterSlaveUtil(MSRedisTemplateBeanDefinitionRegistryPostProcessor msRedisTemplateBeanDefinitionRegistryPostProcessor, ApplicationContext applicationContext) {
          this.msRedisTemplateBeanDefinitionRegistryPostProcessor = msRedisTemplateBeanDefinitionRegistryPostProcessor;
          this.applicationContext = applicationContext;
          List<GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode> nodes = this.msRedisTemplateBeanDefinitionRegistryPostProcessor
                  .getGardenRedisMasterSlaveProperties().getNodes();
          List<GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode> slaveNodes = nodes.stream().filter(n -> n.getName().contains("slave")).collect(Collectors.toList());
          slaves = Lists.newArrayList();
          for (GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode node : slaveNodes) {
              RedisTemplate slave = this.applicationContext.getBean(node.getName(), RedisTemplate.class);
              this.slaves.add(slave);
          }
          GardenRedisMasterSlaveProperties.GardenRedisMasterSlaveNode masterNode = nodes.stream().filter(n -> n.getName().contains("master")).findFirst().get();
          master = this.applicationContext.getBean(masterNode.getName(), RedisTemplate.class);
      }

      /**
       * 普通缓存放入
       *
       * @param key   键
       * @param value 值
       * @return true成功 false失败
       */
      public boolean set(String key, Object value) {
          try {
              master.opsForValue().set(key, value);
              return true;
          } catch (Exception e) {
              e.printStackTrace();
              return false;
          }
      }

      /**
       * 普通缓存获取
       *
       * @param key 键
       * @return 值
       */
      public Object get(String key) {
          return key == null ? null : getRandomSlaveRedisTemplate().opsForValue().get(key);
      }

      // 其他操作...

  }
  ```

> 参考文献

* [Spring Boot配置Redis主从复制](https://blog.csdn.net/qq_41989109/article/details/109630857)
* [SpringBoot根据配置文件动态创建Bean](https://blog.csdn.net/Yh360311/article/details/126941798)
* [使用 RedisTemplate Lettuce 自定义连接对象](https://blog.csdn.net/weixin_43958556/article/details/119515216)