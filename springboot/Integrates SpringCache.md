## 集成 SpringCache

> 简介

* ```SpringCache```是```Spring3.1```开始引入的一种规范，即```Spring```的缓存抽象。通过定义```org.springframework.cache.Cache```和```org.springframework.cache.CacheManager```接口来统一不同的缓存技术，并支持使用```JCache```注解简化开发过程。```Cache```接口为缓存的组件定义操作规范，包含缓存的各种集合操作；```CacheManager```指定缓存的组件实现，如```RedisCache```以及```RedissonSpringCache```等。

> 使用redis实现

* 集成```Redis```（[```Standalone```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Standalone.md)、[```MasterSlave```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Master-Slave.md)、[```Sentinel```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Sentinel.md)以及[```Cluster```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Cluster.md)）。

* 配置缓存管理器

  ```bash
  @Configuration
  @EnableCaching // 启动SpringCache
  public class SpringCacheRedisConfig extends CachingConfigurerSupport {

      /**
       * 缓存管理器：指定使用那种缓存的具体实现，方式一
       *
       * 只有CacheManger才能扫描到cacheable注解
       * Value使用Jackson工具序列化
       */
      @Bean
      public CacheManager cacheManager(RedisConnectionFactory connectionFactory) {
          RedisCacheManager cacheManager = RedisCacheManager.RedisCacheManagerBuilder
                  .fromConnectionFactory(connectionFactory) //设置Redis连接工厂
                  .cacheDefaults(getCacheConfigurationWithTtl(Duration.ofHours(1))) //设置缓存配置
                  .transactionAware() //设置同步修改或删除put/evict
                  //设置不同cacheName不同的过期时间
                  //.withCacheConfiguration("app:",getCacheConfigurationWithTtl(Duration.ofHours(5)))
                  //.withCacheConfiguration("user:",getCacheConfigurationWithTtl(Duration.ofHours(2)))
                  .build();
          return cacheManager;
      }

      private RedisCacheConfiguration getCacheConfigurationWithTtl(Duration duration) {
          return RedisCacheConfiguration
                  .defaultCacheConfig()
                  .serializeKeysWith(RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer())) //设置key的序列化为String
                  .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer())) //设置value的序列化为JSON
                  .computePrefixWith(name -> name + ":") //覆盖默认的构造key，默认构造的key包含两个冒号
                  .disableCachingNullValues() //设置不返回null
                  .entryTtl(duration); //设置缓存过期时间
      }

  }
  ```

> 使用redisson实现

* [集成```Redisson```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Intergrates%20Redisson.md)

* 配置缓存管理器

  ```bash
  @Configuration
  @EnableCaching // 启动SpringCache
  public class SpringCacheRedissonConfig extends CachingConfigurerSupport {

      @Bean
      public CacheManager cacheManager(RedissonClient redissonClient) {
          RedissonSpringCacheManager cacheManager = new RedissonSpringCacheManager(redissonClient);
          return cacheManager;
      }

  }
  ```

> 使用注解

  ```bash
  @CacheConfig(cacheNames = "cacheDemo")
  @Service
  public class SpringCacheDemoServiceImpl implements SpringCacheDemoService {

      @Override
      @CachePut(key = "'id:'+#springCacheDemo.id")
      public SpringCacheDemo save(SpringCacheDemo springCacheDemo) {
          System.out.println("【模拟】mysql保存成功");
          return springCacheDemo;
      }

      @Override
      @Cacheable(key = "'id:'+#id")
      public SpringCacheDemo getById(Long id) {
          SpringCacheDemo springCacheDemo = new SpringCacheDemo();
          springCacheDemo.setId(id);
          springCacheDemo.setName("Garden");
          System.out.println("【模拟】mysql查询成功");
          return springCacheDemo;
      }

      @Override
      @CacheEvict(key = "'id:'+#id")
      public long deleteById(Long id) {
          System.out.println("【模拟】mysql删除成功");
          return id;
      }

  }
  ```

  使用的基本注解的解释：

  * ```@Cacheable```：将方法的返回结果进行缓存，后续方法被调用直接返回缓存中的数据，不执行方法，适用于查询。
  * ```@CachePut```：将方法的返回结果进行缓存，无论缓存中是否有数据都会执行方法并缓存结果，适用于更新。
  * ```@CacheEvict```：删除缓存中的数据。
  * ```@Caching```：组合使用缓存注解。
  * ```@CacheConfig```：统一配置本类的缓存注解属性。
  * ```@EnableCaching```：用于启动类或缓存配置类，表示开启缓存。
  
  更详细的解释请参考[官方文档](https://docs.spring.io/spring-framework/docs/4.1.x/spring-framework-reference/html/cache.html)。

> 参考文献

* [Springboot 整合 SpringCache 使用 Redis 作为缓存](https://www.cnblogs.com/hanzhe/p/16935954.html#)
* [SpringCache整合Redis](https://blog.hackyle.com/article/java-demo/springcache-redis)