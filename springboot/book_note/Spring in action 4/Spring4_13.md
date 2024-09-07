# Spring4

#### Spring集成缓存

* 了解缓存
  * 背景：普遍的应用组件大多为无状态组件，故具有良好的扩展性，多次访问的情况下多次被使用，即可能造成一直在执行相同操作，造成性能问题。缓存的出现能够解决这一问题。
  * 缓存：经常用于存储常用信息，每次需要时即可使用。
  * Spring对缓存的支持：Spring自身没有实现缓存的技术方案，但对其他流行的缓存实现提供支持。
* 基于注解集成缓存
  * 启动缓存：
  ```
  @Configuration
  @EnableCaching    /*启用缓存（创建切面并触发Spring缓存注解的切点，通过切面操作缓存数据）*/
  public class CachingConfig {
    /声明一个缓存管理器/
    /Ehcache缓存管理器/
    @Bean
    public CacheCacheManager cacheManager(CacheManager cm) {/*配置Spring的CacheManager，注入EhCache的CacheManager*/
      return new EhCacheCacheManager(cm);
    }
    @Bean
    public EhCacheManagerFactoryBean ehcache() {/*配置EhCacheManagerFactoryBean，用于生成EhCache的CacheManager*/
      EhCacheManagerFactoryBean ehCacheFactoryBean = new EhCacheManagerFactoryBean();
      ehCacheFactoryBean.setConfigLocation(new ClassPathResource("spittr/cache/ehcache.xml"));
      return ehCacheFactoryBean;
    }
    /Redis缓存管理器/
    //@Bean
    //public CacheManager cacheManager(RedisTemplate redisTemplate) {
      //return new RedisCacheManager(redisTemplate);
     //}
    //@Bean
    //public JedisConnectionFactory redisConnectionFactory() {
      //JedisConnectionFactory jedisConnectionFactory = new JedisConnectionFactory();
      //jedisConnectionFactory.afterPropertiesSet();
      //return jedisConnectionFactory;
    //}
    //@Bean
    //public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory redisCF) {
      //RedisTemplate<String, Object> redisTemplate = new RedisTemplate<String, Object>();
      //redisTemplate.setConnectionFactory(redisCF);
      //redisTemplate.afterPropertiesSet();
      //return redisTemplate;
    //}
    /声明多个缓存管理器（按顺序查找使用缓存管理器）/
    //@Bean
    //public CacheManager cacheManager(net.sf.ehcache.CacheManager ehcm) {
      //CompositeCacheManager cacheManager = new CompositeCacheManager();
      //List<CacheManager> managers = new ArrayList<CacheManager>();
      //managers.add(new EhCacheCacheManager(cm));
      //managers.add(new RedisCacheManager(redisTemplate()));
      //cacheManager.setCacheManagers(managers);
      //return cacheManager;
    //}
  }
  ```
  * 使用缓存：
    * Spring缓存注解：可用于方法级别或者类级别
      * @Cacheable：调用方法前，先根据缓存key查找该方法的返回值是否存在缓存，若存在则不调用该方法，若不存在则调用该方法并将该方法返回值放置该缓存中。适用于查找方法。
      * @CachePut：直接调用该方法并将该方法返回值放置缓存中。适用于保存方法。
      ```
      -- @Cacheable，@CachePut属性
      属性    类型        描述
      value  String[]    指定缓存名称
      condition String   SpEL表达式，值为false则缓存不应用在此方法。适用于条件化填充缓存。
      key    String      SpEL表达式，值为缓存key。
      unless String      SpEL表达式，值为true则不将返回值放置缓存。适用于条件化填充缓存
      ```
      ```
      -- SpEL表达式扩展
      #root.args：传递给缓存方法的参数，形式为数组。
      #root.caches：该方法执行时所对应的缓存，形式为数组。
      #root.target：目标对象。
      #root.targetClass：目标对象的类。
      #root.method：缓存方法。
      #root.methodName：缓存方法名字。
      #result：方法调用的返回值（不能用于@Cacheable）。
      #Argument：任意方法参数名或参数索引。
      ```
      * @CacheEvict：清除缓存条目。
      ```
      属性    类型        描述
      value  String[]    指定缓存名称
      condition String   SpEL表达式，值为false则缓存不应用在此方法。适用于条件化填充缓存。
      key    String      SpEL表达式，值为缓存key。
      allEntries boolean 值为true，特定缓存的所有条目都被移除。
      beforeInvocation boolean 值为true，调用方法之前移除条目；值为false，调用方法之后移除条目。
      ```
      * @Caching：同时应用多个Spring缓存注解。
    * 填充缓存：默认情况下缓存key为方法参数
    ```
    @Cacheable(value="spittleCache"
    unless="#result.message.contains('NoCache')"
    condition="#id >= 10")
    public Spittle findOne(long id) {
      ...
    }
    @CachePut("spittleCache",key="#result.id")
    public Spittle save(Spittle spittle){
      ...
    }
    ```
    * 移除缓存条目：
    ```
    @CacheEvict("spittleCache")
    public void remove(long spittleId){
      ...  
    }
    ```
* 基于XML声明集成缓存:可以在没有源码的bean上应用缓存功能
  * 启用缓存：使用切面实现将Spring注解与源码分离。Spring的aop与cache命名空间混合使用。
  ```
  <?xml version="1.0" encoding="UTF-8"?>
  <beans xmlns="http://www.springframework.org/schema/beans"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:cache="http://www.springframework.org/schema/cache"
         xmlns:aop="http://www.springframework.org/schema/aop"
         xsi:schemaLocation="http://www.springframework.org/schema/aop
                             http://www.springframework.org/schema/aop/spring-aop.xsd
                             http://www.springframework.org/schema/beans
                             http://www.springframework.org/schema/beans/spring-beans.xsd
                             http://www.springframework.org/schema/cache
                             http://www.springframework.org/schema/cache/spring-cache.xsd">
  <!-- Caching configuration will go here -->
  <!-- 启动缓存 -->
  <cache:annotation-driven>
  <!-- 将缓存通知绑定到一个切点上 -->
  <aop:config>
      <aop:advisor advice-ref="cacheAdvice"
                   pointcut="execution(* com.habuma.spittr.db.SpittleRepository.*(..))"/>
  </aop:config>
  <!-- 配置缓存通知 -->
  <cache:advice id="cacheAdvice">
      <cache:caching>
          <cache:cacheable cache="spittleCache" method="findRecent" />
          <cache:cacheable cache="spittleCache" method="findOne" />
          <cache:cacheable cache="spittleCache" method="findBySpitterId" />
          <cache:cache-put cache="spittleCache" method="save" key="#result.id" />
          <cache:cache-evic cache="spittleCache" method="remove" />
      </cache:caching>
  </cache:advice>
  <bean id="cacheManager" class="org.springframework.cache.concurrent.ConcurrentMapCacheManager"/>
  </beans>
  ```
