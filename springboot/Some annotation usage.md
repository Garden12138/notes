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

### 参考文献

* [注解 @AutoConfigureBefore 和 @AutoConfigureAfter 的用途](https://www.cnblogs.com/lvjingying/p/14289589.html)