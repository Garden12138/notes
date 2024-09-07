# Spring4

## Spring集成持久化机制的数据访问（基于关系型数据库）

#### 了解Spring的数据访问

* 数据访问对象（DAO|Repository）：将数据访问的功能放到一个或多个专注于此任务的组件。良好的DAO|Repository以接口形式暴露。

  [![无标题.png](https://i.loli.net/2018/04/22/5adc646c7de8b.png)](https://i.loli.net/2018/04/22/5adc646c7de8b.png)

* 数据访问异常体系 :Sprin提供平台无关的持久化异常，既比JDBC的异常体系丰富，又没有绑定特定的持久化方案（Hibernate异常体系）。

* 数据访问模板化：数据访问过程中可分成固定以及可变部分，分别划分为两个不同的类：模板以及回调。模板负责处理管理资源，事务控制以及异常处理。回调负责查询语句，参数绑定以及整理结果集。
[![Spring数据访问模板化.png](https://i.loli.net/2018/04/24/5adef627125a8.png)](https://i.loli.net/2018/04/24/5adef627125a8.png)
  * Spirng提供的常用数据访问模板，每个模板对应每种持久化机制。
    * jdbc.core.JdbcTemplate：JDBC连接。
    * jdbc.core.namedparam.NamedParameterJdbcTemplate：支持命名参数的JDBC连接。
    * orm.hibernate3.HibernateTemplate：hibernate3.x以上的session。
    * orm.jpa.JpaTemplate：Java持久化API的实体管理器。

* 配置数据源：
  * 使用JNDI配置数据源：适用WEB应用生产环境
    * JNDI：JavaNaming and Directory Interface，即Java命名与目录接口，为Java应用程序提供命名服务（如DNS映射服务）以及目录服务（如互联网上寻找离散资源服务）。
    * 配置：
    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <datasources>
        <local-tx-datasource>
            <jndi-name>MySqldruidDataSource</jndi-name>
            <connection-url>jdbc:mysql://localhost:3306/lw</connection-url>
            <driver-class>com.mysql.jdbc.Driver</driver-class>
            <user-name>root</user-name>
            <password>rootpassword</password>
            <exception-sorter-class-name>
                org.jboss.resource.adapter.jdbc.vendor.MySQLExceptionSorter
            </exception-sorter-class-name>
            <metadata>
                <type-mapping>mySQL</type-mapping>
            </metadata>
        </local-tx-datasource>
    </datasources>
    ```
    ```
    <!-- Spring应用上下文 -->
    <!-- XML Config -->
    <jee:jndi-lookup id="dataSource" jndi-name="/jdbc/MySqldruidDataSource" resource-ref="true" />
    <!-- Java Config -->
    @Bean
    public JndiObjectFactoryBean dataSource(){
      JndiObjectFactoryBean jndiObjectFB = new JndiObjectFactoryBean();
      jndiObjectFB.setJndiName("/jdbc/MySqldruidDataSource");
      jndiObjectFB.setResource(true);
      jndiObjectFB.setProxyInterface(javax.sql.DataSource.class);
    }
    ```
  * 使用连接池配置数据源：适用WEB应用生产环境
    * 主流连接池：[Druid](https://github.com/alibaba/druid)
    * 配置：[DruidDataSource](tool.oschina.net/uploads/apidocs/druid0.26/com/alibaba/druid/pool/DruidDataSource.html)
    ```
    <!-- Spring应用上下文 -->
    <!-- XML Config -->
    <bean id = "dataSource" class = "com.alibaba.druid.pool.DruidDataSource" destroy-method = "close">    
        <!-- 数据库基本信息配置 -->  
        <property name = "url" value = "${url}" />    
        <property name = "username" value = "${username}" />    
        <property name = "password" value = "${password}" />    
        <property name = "driverClassName" value = "${driverClassName}" />    
        <property name = "filters" value = "${filters}" />    
        <!-- 最大并发连接数 -->  
        <property name = "maxActive" value = "${maxActive}" />  
        <!-- 初始化连接数量 -->  
        <property name = "initialSize" value = "${initialSize}" />  
        <!-- 配置获取连接等待超时的时间 -->  
        <property name = "maxWait" value = "${maxWait}" />  
        <!-- 最小空闲连接数 -->  
        <property name = "minIdle" value = "${minIdle}" />    
        <!-- 配置间隔多久才进行一次检测，检测需要关闭的空闲连接，单位是毫秒 -->  
        <property name = "timeBetweenEvictionRunsMillis" value ="${timeBetweenEvictionRunsMillis}" />  
        <!-- 配置一个连接在池中最小生存的时间，单位是毫秒 -->  
        <property name = "minEvictableIdleTimeMillis" value ="${minEvictableIdleTimeMillis}" />    
        <property name = "validationQuery" value = "${validationQuery}" />    
        <property name = "testWhileIdle" value = "${testWhileIdle}" />    
        <property name = "testOnBorrow" value = "${testOnBorrow}" />    
        <property name = "testOnReturn" value = "${testOnReturn}" />    
        <property name = "maxOpenPreparedruidDataSourcetatements" value ="${maxOpenPreparedruidDataSourcetatements}" />  
        <!-- 打开 removeAbandoned 功能 -->  
        <property name = "removeAbandoned" value = "${removeAbandoned}" />  
        <!-- 1800 秒，也就是 30 分钟 -->  
        <property name = "removeAbandonedTimeout" value ="${removeAbandonedTimeout}" />  
        <!-- 关闭 abanded 连接时输出错误日志 -->     
        <property name = "logAbandoned" value = "${logAbandoned}" />  
    </ bean >
    <!-- Java Config -->
    InputStream in = RootConfig.class.getClassLoader().getResourceAsStream("database.properties");
    Properties properties = new Properties();
    properties.load(in);
    @Bean
    public DruidDataSource dataSource(){
      DruidDataSource druidDataSource = new DruidDataSource ();
      druidDataSource.setDriverClassName(properties.getProperty("jdbc.driver"));
      druidDataSource.setUsername(properties.getProperty("jdbc.user"));
      druidDataSource.setPassword(properties.getProperty("jdbc.password"));
      druidDataSource.setUrl(properties.getProperty("jdbc.url"));
      druidDataSource.setInitialSize(Integer.parseInt(properties.getProperty("jdbc.initialSize")));
      druidDataSource.setMaxActive(Integer.parseInt(properties.getProperty("jdbc.maxActive")));
      druidDataSource.setMinIdle(Integer.parseInt(properties.getProperty("jdbc.minIdle")));
      druidDataSource.setMaxWait(Integer.parseInt(properties.getProperty("jdbc.maxWait")));
      druidDataSource.setFilters("stat,wall,log4j");
      druidDataSource.setPoolPreparedruidDataSourcetatements(true);
      druidDataSource.setMaxPoolPreparedruidDataSourcetatementPerConnectionSize(20);
    }
    ```
  * 使用JDBC驱动配置数据源：适用WEB应用开发环境
    * JDBC驱动：
      * DriverManagerDataSource：在每个连接请求时都会返回一个新建的连接。
      * SimpleDriverDataSource：工作方式与DriverManagerDataSource相似。但其直接JDBC驱动来解决特点环境下的类加载问题。
      * SingleConnectionDataSource:在每个连接请求时都会返回同一个连接。
    * 配置  
    ```
    <!-- Spring应用上下文 -->
    <!-- XML Config -->
    <bean id="dataSource" class="org.springframework.jdbc.datasource.DriverManagerDataSource"
          p:driverClassName="org.h2.Driver"
          p:url="jdbc:h2:tcp://localhost/~/spitter"
          p:username="garden"
          p:password="garden" />
    <!-- Java Config -->
    @Bean
    public DataSource dataSource(){
      DriverManagerDataSource ds = new DriverManagerDataSource();
      ds.setDriverClassName("org.h2.Driver");
      ds.setUrl("jdbc:h2:tcp://localhost/~/spitter");
      ds.setUsername("garden");
      ds.setPassword("garden");
    }
    ```
  * 使用嵌入式配置数据源：适用WEB应用测试环境。
    * 嵌入式：嵌入外部sql文件作为数据源。
    * 配置
    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns="http://www.springframework.org/schema/beans"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    	     xmlns:c="http://www.springframework.org/schema/c"
    	     xmlns:jdbc="http://www.springframework.org/schema/jdbc"
    	     xsi:schemaLocation="http://www.springframework.org/schema/jdbc     http://www.springframework.org/schema/jdbc/spring-jdbc-3.1.xsd
    		   http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
           <jdbc:embedded-database id="dataSource" type="H2">
               <jdbc:script location="classpath:spittr/db/jdbc/schema.sql" />
               <jdbc:script location="classpath:spittr/db/jdbc/test-data.sql" />
           </jdbc:embedded-database>
    </beans>
    ```
  * [使用Profile选择数据源](https://github.com/Garden12138/Spring4/blob/master/Spring4_3.md)

#### Spring集成JDBC的数据访问
* JDBC建立于SQL基础之上，能够更好地对数据访问的性能进行调优。使用JDBC包括使用原生JDBC和模板JDBC，原生JDBC职责不专一，除了进行数据访问还需负责管理事务与资源，处理异常等任务，故不建议使用。
* 使用模板JDBC：Spring的JDBC框架承担了资源管理和异常的工作，我们只需关心从数据库读写数据的代码。
  * JdbcTemplate：支持简单的JDBC数据库访问功能以及基于索引参数的查询。
  * NamedParameterJdbcTemplate：支持简单的JDBC数据库访问功能以及基于参数命名方式的查询。
* Demo：[JdbcTemplate API](https://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/jdbc/core/JdbcTemplate.html)
```
//Spring应用上下文
@Bean
public JdbcTemplate jdbcTemplate(DataSource dataSource){
  return new JdbcTemplate(dataSource);
}
```
```
//Repository|dao层
@Repository
public class JdbcRepositoryImpl implements JdbcRepository{
  @Autowired
  private JdbcOperations jdbcOperations;    //JdbcOperations实现JdbcTemplate所有操作。
  ...  
}
```
#### Spring集成ORM的数据访问
* ORM，object-relational mapping，即对象-关系映射，将对象的属性映射关系型数据库表的列，并且自动生成sql语句，具有延迟加载，懒加载以及级联特性。Spring对ORM框架的支持有Hibernate，iBATIS,JDO,JPA等，为这些框架提供附加的服务包括支持集成Spring声明式事务，透明的异常处理，线程安全轻量级的模板类，DAO支持类以及资源管理。
* 在Spring中集成Hibernate
  * 准备：Hibernate SessionFactoryBean（Spring中用于获取Hibernate SessionFactory的Bean）->Hibernate SessionFactory（该接口提供了获取，打开，关闭以及管理Hibernate Session功能）->Hibernate Session（该接口提供基本数据的访问功能）->Hibernate
  * 步骤：
    * 于Spring应用上下文中配置Hibernate SessionFactoryBean
    ```
    //hibernate3支持xml配置
    @Bean
    public LocalSessionFactoryBean sessionFactory(DataSource dataSource){
      LocalSessionFactoryBean lsfb = new LocalSessionFactoryBean();
      lsfb.setDataSource(dataSource);
      lsfb.setMappingResources(new String[]{"Spitter.hbm.xml"});
      Properties props = new Properties();
      props.setProperty("dialect","org.hibernate.dialect.H2Dialect");
      lsfb.setHibernateProperties("props");
      return lsfb;
    }
    //hibernate3支持annotation配置
    @Bean
    public AnnotationSessionFactoryBean sessionFactory(DataSource dataSource){
      AnnotationSessionFactoryBean asfb = new AnnotationSessionFactoryBean();
      asfb.setDataSource(dataSource);
      asfb.setPackagesToScan(new String[]{"com.web.spring4.entity"});
      Properties props = new Properties();
      props.setProperty("dialect","org.hibernate.dialect.H2Dialect");
      asfb.setHibernateProperties("props");
      return asfb;
    }
    //hibernate4-支持xml和annotation配置
    @Bean
    public LocalSessionFactoryBean sessionFactory(DataSource dataSource){
      LocalSessionFactoryBean lsfb = new LocalSessionFactoryBean();
      lsfb.setDataSource(dataSource);//装配数据源
      lsfb.setMappingResources(new String[]{"Spitter.hbm.xml"});//装配映射配置文件
      //lsfb.setPackagesToScan(new String[]{"com.web.spring4.entity"});//扫描带有@Entity与@MappedSuperClass的实体类
      Properties props = new Properties();
      props.setProperty("dialect","org.hibernate.dialect.H2Dialect");
      lsfb.setHibernateProperties("props");//装配细节配置
      return lsfb;
    }
    ```
    * 构建不依赖Spring的Repository：不使用HibernateTemplate（HibernateTemplate保证每个事务使用同个session，使Repository的实现与Spring耦合），而是使用上下文[Session](http://docs.jboss.org/hibernate/orm/3.2/api/org/hibernate/Session.html)。
    ```
    //Repository|dao层
    @Repository
    public class HibernateRepositoryImpl implements HibernateRepository{
      @Autowired
      private SessionFactory sessionFactory;    
      private Session currentSession(){
        return sessionFactory.getCurrentSession();
      }
      public void save(Spitter spitter){
        currentSession.save(spitter);
      }
      ...
    }
    ```
    * 添加异常转换功能：若使用Hibernate上下文Session而不是Hibernate模板的时候，需将Hibernate的异常处理转交给Spring统一处理。
    ```
    @Bean
    public BeanPostProcessor persistenceTranslation(){
      return new PersistenceExceptionTranslationPostProcessor();
      //PersistenceExceptionTranslationPostProcessor是一个bean后置处理器，为所有带有@Repository注解的类添加一个通知器，用于统一处理数据访问异常。
    }
    ```
* 在Spring中集成JPA
  * 准备：EntityManagerFactoryBean（Spring中获取EntityManagerFactory的Bean）->EntityManagerFactory（获取EntityManager实例）->EntityManager（应用程序类型的实体管理器或容器类型的实体管理器）->JPA（Java Persistence API）
  * 步骤：
    * 于Spring应用上下文中配置实体管理器工厂
    ```
    -- 生产应用程序类型的实体管理器工厂
    //persistence.xml配置数据源，放置META-INF目录下
    <persistence xmlns="http://java.sun.com/xml/ns/persistence" version="1.0">
        <persistence-unit name="SpitterPU">
            <!-- 全限定实体类名 -->
            <class>com.web.spring4.entity.Spitter</class>
            <!-- 数据源 -->
            <properties>
                <property name="toplink.jdbc.driver" value="org.hsqldb.jdbcDriver" />
                <property name="toplink.jdbc.url" value="jdbc:hsqldb:hsql://localhost/spring4" />
                <property name="toplink.jdbc.user" value="garden" />
                <property name="toplink.jdbc.password" value="org.hsqldb.garden" />
            </properties>
        </<persistence-unit>
    </persistence>
    //配置实体管理器工厂
    @Bean
    public LocalEntityManagerFactoryBean entityManagerFactoryBean(){
      LocalEntityManagerFactoryBean lemfb = new LocalEntityManagerFactoryBean();
      lemfb.setPersistenceUnitName("SpitterPU");//配置数据源，persistence.xml中持久话单元名称。
    }
    ```
    ```
    -- 生产容器类型的实体管理器工厂
    //配置JPA具体实现
    @Bean
    public JpaVendorAdapter jpaVendorAdapter(){
      HibernateJpaVendorAdpater adapter = new HibernateJpaVendorAdpater();
      adapter.setDataBase("HSQL");
      adapter.setShowSql("true");
      adapter.setGenerateDdl(false);
      adapter.setDatabasePlatform("org.hibernate.dialect.HSQLDialect");
      return adapter;
    }
    //配置实体管理器工厂
    @Bean
    public LocalContainerEntityManagerFactoryBean entityManagerFactoryBean(){
      LocalContainerEntityManagerFactoryBean lcemfb = new LocalContainerEntityManagerFactoryBean();
      lcemfb.setDataSource(dataSource);//配置数据源
      lcemfb.setJpaVendorAdapter(jpaVendorAdapter);//指明具体JPA实现
      lcemfb.setPackagesToScan("com.web.spring4.entity");//扫描实体
    }
    ```
    * 编写基于JPA的Repository：[EntityManager](https://blog.csdn.net/fly910905/article/details/78600251?locationNum=4&fps=1)
    ```
    //Repository|dao层
    @Repository
    @Transactional
    public class SpitterRepositoryImpl implements SpitterSweeper{
      //@PersistenceUnit
      //private EntityManagerFactory emf;
      //public void addSpitter(Spitter spitter){
      //  emf.createEntityManager().persist(spitter);
      //}
      @PersistenceContext
      private EntityManager em;//注入EntityManager代理，真正的EntityManager与当前事务绑定
      public void addSpitter(Spitter spitter){
        em.persist(spitter);
      }
      ...
    }
    ```
    ```
    //若无启用JPA注解如<context:annotation-config>或<context:component-scan>，则需注册
    @Bean
    public PersistenceAnnotationBeanPostProcessor paPostProcessor(){
      return new PersistenceAnnotationBeanPostProcessor();
    }
    ```
    * 添加异常转换功能：若使用Hibernate上下文Session而不是Hibernate模板的时候，需将Hibernate的异常处理转交给Spring统一处理。
    ```
    @Bean
    public BeanPostProcessor persistenceTranslation(){
      return new PersistenceExceptionTranslationPostProcessor();
      //PersistenceExceptionTranslationPostProcessor是一个bean后置处理器，为所有带有@Repository注解的类添加一个通知器，用于统一处理数据访问异常。
    }
    ```
  * 借助[Spring Data实现自动化的JPA](https://www.oschina.net/translate/getting-started-with-spring-data-jpa?cmp) Repository
    * 于Spring应用上下文启动Spring Data JPA
    ```
    -- 扫描查找扩展Spring Data JPA的所有repository接口并自动实现
    <!-- xml -->
    <jpa:repositories base-package="com.web.spring4.dao" repository-impl-postfix="Helper" />
    //JavaConfig
    @Configuration
    @EnableJpaRepositories(basePackages="com.web.spring4.dao",repositoryImplementationPostfix="Helper")
    public class JpaConfiguration{
      ...
    }
    ```
    * 借助Spring Data，以接口形式创建Repository
    ```
    public interface SpitterRepository extends JpaRepository<Spitter,Long>,SpitterSweeper{
      public Spitter findByUsername(String username);//定义自动查询方法，根据方法名中的动词，主题，By以及断言自动生成查询语句
      @Query("select s from Spitter s where s.email like '%@mail.com'")/定义自定义查询方法
      public List<Spitter> findAllMailSpitters();
      //混合自定义：自动合并接口名+Impl后缀的实现方法，如SpitterRepositoryImpl。可选择修改后缀（repository-impl-postfix="Helper"或repositoryImplementationPostfix="Helper"）
    }
    ```
    * [Demo](https://www.ibm.com/developerworks/cn/opensource/os-cn-spring-jpa/index.html)
