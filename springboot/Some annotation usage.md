## 一些注解的用法

### @AutoConfigureBefore

* ```@AutoConfigureBefore```注解用于指定当前配置类在指定的配置类之前进行自动配置。这对于确保配置的加载顺序非常重要，特别是当配置类之间存在依赖关系时。

* 作用：
  - 控制自动配置类的加载顺序
  - 确保当前配置类在指定配置类之前被初始化
  - 主要用于```Spring Boot```的自动配置机制中

* 基本用法：

  ```java
  @Configuration
  @EnableAutoConfiguration
  @AutoConfigureBefore({DataSourceAutoConfiguration.class})
  public class CustomDataSourceConfiguration {
    
      @Bean
      @Primary
      public DataSource customDataSource() {
          // 自定义数据源配置
          HikariConfig config = new HikariConfig();
          config.setJdbcUrl("jdbc:h2:mem:testdb");
          config.setUsername("sa");
          config.setPassword("");
          return new HikariDataSource(config);
      }
  }
  ```

* 实际应用场景：
  - 自定义数据源配置：在```Spring Boot```默认数据源配置之前配置自己的数据源
  - 安全配置：确保安全相关配置在其他配置之前加载
  - 缓存配置：在业务配置之前初始化缓存相关配置

* 注意事项：
  - 该注解只在自动配置类中生效，需要配合```@Configuration```和```@EnableAutoConfiguration```使用，且指定的类也必须是自动配置类
  - 避免循环依赖，确保配置顺序的合理性

### @AutoConfigureAfter

* ```@AutoConfigureAfter```注解用于指定当前配置类在指定的配置类之后进行自动配置。这确保了依赖的配置类先被加载和初始化。

* 作用：
  - 控制自动配置类的加载顺序
  - 确保当前配置类在指定配置类之后被初始化
  - 主要用于当前配置依赖其他配置类的场景

* 基本用法：

  ```java
  @Configuration
  @EnableAutoConfiguration
  @AutoConfigureAfter({DataSourceAutoConfiguration.class})
  public class MyBatisConfiguration {
    
      @Bean
      public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
          SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
          factory.setDataSource(dataSource);
          factory.setMapperLocations(new PathMatchingResourcePatternResolver()
              .getResources("classpath:mapper/*.xml"));
          return factory.getObject();
      }
    
      @Bean
      public SqlSessionTemplate sqlSessionTemplate(SqlSessionFactory sqlSessionFactory) {
          return new SqlSessionTemplate(sqlSessionFactory);
      }
  }
  ```

* 实际应用场景：
  - ```ORM```配置：在数据源配置之后初始化```MyBatis、JPA```等```ORM```框架
  - 缓存配置：在数据源配置之后配置二级缓存
  - 监控配置：在核心业务配置之后加载监控相关配置
  - 安全配置：在基础配置之后加载安全增强配置

* 注意事项：
  - 该注解只在自动配置类中生效，需要配合```@Configuration```和```@EnableAutoConfiguration```使用，且指定的类也必须是自动配置类
  - 可以与 ```@ConditionalOnClass```、```@ConditionalOnBean```等条件注解组合使用
  - 避免循环依赖，确保配置顺序的合理性

### @Import
* 用于将一个或多个组件导入到```Spring```容器中，支持导入：
  - 普通组件类（作为```@Bean```等价的快速导入）
  - ```@Configuration```配置类
  - ```ImportSelector```返回的类
  - ```ImportBeanDefinitionRegistrar```注册的```BeanDefinition```

* 基本用法（导入普通类 / 配置类 / 实现```ImportSelector```接口的类 / 实现```ImportBeanDefinitionRegistrar```接口的类）：

  ```java
  @Configuration
  @Import({AService.class, BConfiguration.class, CImportSelector.class, DImportBeanDefinitionRegistrar.class})
  public class RootConfiguration {
  }
  ```

* 典型场景：
  - 按模块拆分，将模块配置聚合到主配置
  - 第三方```starter```暴露自动配置
  - 与条件注解（如```@ConditionalOnClass```）组合进行按需装配

* 注意事项：
  - 被导入的类若非配置类，应自身能被容器实例化（有无参构造或可用的```@Bean```工厂方法）
  - ```@Import```在解析阶段生效，优先级高于组件扫描
  - 可与```@AutoConfigureBefore/@AutoConfigureAfter```共同控制装配顺序（面向自动配置场景）

### @ImportSelector
* 通过实现```org.springframework.context.annotation.ImportSelector```接口，按条件返回需要导入的类名数组（全限定名），实现“延迟决策、批量导入”。

* 接口关键点：
  - 方法：```String[] selectImports(AnnotationMetadata importingClassMetadata)```
  - 参数```AnnotationMetadata```可读取触发```@Import```的类及其注解元信息，用于条件判断
  - 拓展：```DeferredImportSelector```可延迟到所有配置类处理后再选择导入（常用于自动配置）

* 基本用法示例：

  ```java
  public class CacheImportSelector implements ImportSelector {
      @Override
      public String[] selectImports(AnnotationMetadata importingClassMetadata) {
          Map<String, Object> attrs = importingClassMetadata
              .getAnnotationAttributes(EnableCache.class.getName());
          String type = (String) attrs.getOrDefault("type", "memory");
          if ("redis".equalsIgnoreCase(type)) {
              return new String[]{"com.example.cache.RedisCacheConfiguration"};
          }
          return new String[]{"com.example.cache.MemoryCacheConfiguration"};
      }
  }

  @Retention(RetentionPolicy.RUNTIME)
  @Target(ElementType.TYPE)
  @Import(CacheImportSelector.class)
  public @interface EnableCache {
      String type() default "memory";
  }

  @Configuration
  @EnableCache(type = "redis")
  public class AppConfig {
  }
  ```

* 注意事项：
  - 返回的类名需可被容器实例化，常见为配置类或带```@Component```的类
  - 逻辑尽量纯粹做“选择”，复杂注册逻辑建议使用```ImportBeanDefinitionRegistrar```
  - 如需控制装配时机可考虑```DeferredImportSelector```

### @ImportBeanDefinitionRegistrar
* 通过实现```org.springframework.context.annotation.ImportBeanDefinitionRegistrar```接口，直接向容器注册```BeanDefinition```，适合更细粒度、动态的注册需求。

* 接口关键点：
  - 方法：```void registerBeanDefinitions(AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry)```
  - 可基于元信息与外部条件（classpath、配置等）动态注册```BeanDefinition```

* 基本用法示例：

  ```java
  public class ClientRegistrar implements ImportBeanDefinitionRegistrar {
      @Override
      public void registerBeanDefinitions(AnnotationMetadata meta, BeanDefinitionRegistry registry) {
          GenericBeanDefinition bd = new GenericBeanDefinition();
          bd.setBeanClass(Client.class);
          bd.getPropertyValues().add("endpoint", "https://api.example.com");
          registry.registerBeanDefinition("client", bd);
      }
  }

  @Retention(RetentionPolicy.RUNTIME)
  @Target(ElementType.TYPE)
  @Import(ClientRegistrar.class)
  public @interface EnableClient {}

  @Configuration
  @EnableClient
  public class ClientConfiguration {
  }
  ```

* 进阶示例（基于注解属性动态注册）：

  ```java
  @Retention(RetentionPolicy.RUNTIME)
  @Target(ElementType.TYPE)
  @Import(RepoRegistrar.class)
  public @interface EnableRepositories {
      String basePackage();
  }

  public class RepoRegistrar implements ImportBeanDefinitionRegistrar {
      @Override
      public void registerBeanDefinitions(AnnotationMetadata meta, BeanDefinitionRegistry registry) {
          Map<String, Object> attrs = meta.getAnnotationAttributes(EnableRepositories.class.getName());
          String base = (String) attrs.get("basePackage");
          // 这里可扫描包并为每个接口注册代理 BeanDefinition（伪代码）
          BeanDefinitionBuilder bdb = BeanDefinitionBuilder
              .genericBeanDefinition(RepositoryFactoryBean.class)
              .addPropertyValue("basePackage", base);
          registry.registerBeanDefinition("repositoryFactory", bdb.getBeanDefinition());
      }
  }
  ```

* 注意事项：
  - 更底层、更灵活；适合框架/组件做批量、动态注册（如```MyBatis/Spring Data```）
  - 小心与组件扫描、```@Bean```重复注册；注册前可通过```registry.containsBeanDefinition```检查
  - 与```ImportSelector```相比，```Registrar```负责“如何注册”，```Selector```负责“选哪些”

### @ConditionalOnProperty

* ```@ConditionalOnProperty```注解用于根据配置属性（```properties```或```yml```）的值来决定是否启用某个配置类或```Bean```。这是```Spring Boot```中最常用的条件注解之一。

* 作用：
  - 根据配置属性的值来控制```Bean```的创建和配置类的加载
  - 实现配置驱动的功能开关
  - 支持多环境配置切换

* 主要属性：
  - ```prefix```：配置属性的前缀
  - ```name```：配置属性的名称（与```prefix```组合成完整属性名）
  - ```havingValue```：配置属性的期望值（匹配时启用）
  - ```matchIfMissing```：当配置属性不存在时是否匹配（默认```false```）
  - ```value```：配置属性的完整名称（可替代```prefix + name```）

* 基本用法：

  ```java
  @Configuration
  @ConditionalOnProperty(prefix = "app.feature", name = "enabled", havingValue = "true")
  public class FeatureConfiguration {
      
      @Bean
      public FeatureService featureService() {
          return new FeatureService();
      }
  }
  
  // application.yml
  app:
    feature:
      enabled: true
  ```

* 简写形式（使用```value```）：

  ```java
  @Configuration
  @ConditionalOnProperty(value = "app.feature.enabled", havingValue = "true")
  public class FeatureConfiguration {
      // ...
  }
  ```

* 在方法上使用：

  ```java
  @Configuration
  public class FeatureConfiguration {
      
      @Bean
      @ConditionalOnProperty(prefix = "app.feature", name = "enabled", havingValue = "true")
      public FeatureService featureService() {
          return new FeatureService();
      }
  }
  ```

* 实际应用场景：
  - **功能开关**：根据配置启用/禁用某个功能模块
  - **多数据源切换**：根据配置选择不同的数据源实现
  - **中间件选择**：根据配置选择使用```Redis```或```Caffeine```作为缓存
  - **环境适配**：不同环境使用不同的配置实现
  - **自动配置**：在```Spring Boot Starter```中根据用户配置决定是否启用某些功能

* 注意事项：
  - ```havingValue```默认匹配任何非空值，如果设置为```""```则要求属性值为空字符串
  - ```matchIfMissing = true```时，即使属性不存在也会启用配置，常用于默认启用场景
  - 可以与其他条件注解（如```@ConditionalOnClass```、```@ConditionalOnBean```）组合使用
  - 在```@Configuration```类上使用时，会影响整个配置类的加载；在```@Bean```方法上使用时，只影响该方法的执行
  - 属性值匹配是区分大小写的，注意大小写匹配

### @ConditionalOnMissingBean

* 当容器中缺少指定类型/名称/注解的```Bean```时，才进行装配。常用于```Starter```提供“默认实现”，允许应用方通过自定义```Bean```进行覆盖。

* 作用：
  - 提供“默认```Bean```”，且允许用户按需覆盖
  - 避免重复注册，保证容器中同类```Bean```唯一性（或按名称唯一）
  - 与自动配置配合，增强可插拔性

* 主要属性：
  - ```value```：按类型判断是否缺失（```Class<?>[]```）
  - ```type```：按类型名判断是否缺失（```String[]```，避免类在编译期不可达）
  - ```name```：按```Bean```名称判断是否缺失
  - ```annotation```：按```Bean```上是否存在某注解判断
  - ```search```：搜索策略，是否在父容器中查找（```SearchStrategy.ALL/ CURRENT/ ANCESTORS```）
  - ```ignored```/```ignoredType```：判断缺失时需要忽略的类型/类型名

* 基本用法：

  ```java
  // 类型判断
  @Configuration
  public class JacksonConfiguration {
    
    @Bean
    @ConditionalOnMissingBean(ObjectMapper.class)
    public ObjectMapper objectMapper() {
      return new ObjectMapper().findAndRegisterModules();
    }
  }
  ```

  ```java
  // 类型名称判断
  @Configuration
  public class CacheConfiguration {
    
    @Bean
    @ConditionalOnMissingBean(type = "org.springframework.cache.CacheManager")
    public CacheManager simpleCacheManager() {
      return new ConcurrentMapCacheManager();
    }
  }
  ```

  ```java
  // 名称判断 
  @Configuration
  public class MailConfiguration {
    
    @Bean("mailSender")
    @ConditionalOnMissingBean(name = "mailSender")
    public JavaMailSender mailSender() {
      JavaMailSenderImpl sender = new JavaMailSenderImpl();
      sender.setDefaultEncoding("UTF-8");
      return sender;
    }
  }
  ```

* 在自动配置中的典型场景：
  - 提供默认的```DataSource/CacheManager/ObjectMapper```等
  - 当用户自定义同类型```Bean```后，自动配置的```Bean```不再生效
  - 搭配```@ConditionalOnClass```、```@ConditionalOnProperty```形成“类存在 + 无用户自定义 + 属性开启”的三重门槛

* 注意事项：
  - 判断“是否缺失”基于```BeanDefinition```级别而非实例；```FactoryBean```场景需留意实际暴露的```Bean```类型
  - 与```@Primary```/```@Qualifier```不冲突：该注解只负责“是否创建”，不负责“注入选择”
  - 合理设置```search```，避免父子容器重复定义导致的误判
  - 若存在多个候选默认实现，建议再配合属性开关或显式名称区分

### 参考文献

* [注解 @AutoConfigureBefore 和 @AutoConfigureAfter 的用途](https://www.cnblogs.com/lvjingying/p/14289589.html)
* [Spring中@Import注解详细讲解及示例](https://blog.csdn.net/zouliping123456/article/details/114096248)
* [Spring 中的 @ConditionalOnProperty 注解](https://springdoc.cn/spring-conditionalonproperty/)
* [@ConditionalOnMissingBean 注解](https://www.hxstrive.com/subject/spring_boot/480.htm)