## SpringBoot 集成 Redis 单例

> 简介

* ```Reids```是高性能高可用的键值对数据库。详细信息可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/redis/redis%20started.md)。

> 集成步骤

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

* 设置```Redis```服务连接配置：

  ```bash
  spring:
    redis:
      # Redis数据库索引(默认为0)
      database: 0
      # Redis服务器连接端口
      port: 6379
      # Redis服务器地址
      host: 127.0.0.1
      # Redis服务器连接密码(默认为空)
      password: redis@2024
      # 连接超时时间（毫秒）
      timeout: 5000
      lettuce:
        # 关闭超时时间
        shutdown-timeout: 100
        pool:
          # 连接池最大连接数（使用负值表示没有限制）
          max-active: 8
          # 连接池最大阻塞等待时间（使用负值表示没有限制）
          max-wait: 10000
          # 连接池中的最大空闲连接
          max-idle: 8
          # 连接池中的最小空闲连接
          min-idle: 0
  ```

* 新增```Redis```配置类型：

  ```bash
  @Configuration
  public class RedisConfig {

      @Autowired
      private LettuceConnectionFactory factory;

      /**
       * RedisTemplate配置
       * 注意： 注入的是LettuceConnectionFactory
       */
      @Bean
      public RedisTemplate<String, Object> redisTemplate() {
          RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
          redisTemplate.setConnectionFactory(factory);
          redisTemplate.setKeySerializer(keySerializer());
          redisTemplate.setHashKeySerializer(keySerializer());
          redisTemplate.setValueSerializer(valueSerializer());
          redisTemplate.setHashValueSerializer(valueSerializer());
          return redisTemplate;
      }

      /**
       * key序列化
       */
      private RedisSerializer<String> keySerializer() {
          return new StringRedisSerializer();
      }

      /**
       * value序列化
       */
      private RedisSerializer<Object> valueSerializer() {
          return new GenericJackson2JsonRedisSerializer();
      }

  }
  ```

* 封装访问```Redis```服务访问工具类（基于```RedisTemplate API```），可参考[项目](https://gitee.com/FSDGarden/microservices-spring/tree/feature%2Fsc-2020.0.1-v1/)。使用时可直接注入```RedisTemplate```或封装的```RedisUtil```：

  ```bash
  @Autowired
  private RedisTemplate redisTemplate;
  ```

  或

  ```bash
  @Autowired
  private RedisUtil RedisUtil;
  ```

  ```RedisUtil```实现类参考[这里](https://gitee.com/FSDGarden/microservices-spring/blob/feature/sc-2020.0.1-v1/common/common-redis/src/main/java/com/garden/redis/utils/RedisUtil.java)

> 参考文献

* [【第二章】SpringBoot2.x集成Redis](https://juejin.cn/post/6844903936143392775)