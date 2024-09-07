  # Spring4

## 高级装配

#### 自动化装配Bean的歧义性

* 场景：自动化装配Bean包括JavaConfig装配Bean时使用参数自动注入被依赖者时（实质上是自动扫描已创建该类型的Bean）的时候是使用接口注入，若该接口多个实现，则Spring无法得知需要注入的具体实现，故会抛出异常。
* 解决方式：
  * 使用首选的Bean，使用注解@Primary标识被依赖Bean。

  ```
  - 使用前例：
  - JayChouAlbum，JayChouAlbum2 实现 CompactDisc
  - CDPlayer 依赖 CompactDisc
  ```

  ```
  - 自动装配
  package com.web.spring4.bean.impl;
  import org.springframework.context.annotation.Primary;
  import org.springframework.stereotype.Component;
  import com.web.spring4.bean.CompactDisc;
  @Component
  @Primary
  public class JayChouAlbum implements CompactDisc{
    private String songs[] = {"夜曲"};
    private String artist = "周杰伦";

    @Override
    public void play() {
      // TODO Auto-generated method stub
      System.out.println("正在播放："+ songs[0] + "-" +artist);
    }
  }

  ```

  ```
  - JavaConfig
  @Bean
  @Primary
  public CompactDisc JayChouAlbum{
    return new JayChouAlbum();
  }
  ```

  ```
  - XML
  <bean id = "jayChouAlbum" class = "com.web.spring4.bean.impl.JayChouAlbum" primary = "true"/>
  ```

  * 使用限定符的Bean，使用注解@Qualifier标识依赖者注入，参数为被依赖者Bean ID，由于对类名称或方法名的任意改动会导致限定符失效，即限定符也伴随着改动。故常使用自定义的限定符，即依赖者和被依赖者约定相同的限定符（此时的限定符用于描述bean的属性），由于常会出现相同属性的Bean，故常使用自定义@Qualifier注解多次描述Bean以至于区分开Bean。

  ```
  - @Qualifier标识依赖者注入处（属性，setter）
  ```

  ```
  package com.web.spring4.bean.impl;
  import javax.annotation.Resource;
  import org.springframework.beans.factory.annotation.Autowired;
  import org.springframework.beans.factory.annotation.Qualifier;
  import org.springframework.stereotype.Component;
  import com.web.spring4.bean.CompactDisc;
  import com.web.spring4.bean.MediaPlayer;
  @Component
  public class CDPlayer implements MediaPlayer{
    @Resource
    @Qualifier("jayChouAlbum2")    /*限定符即字符串为Bean ID*/
    private CompactDisc cd1;
  //@Autowired /*@Resource不可用于构造函数*/
  //@Qualifier("jayChouAlbum2")  /*@Qualifier不能用于构造函数*/
    public CDPlayer(CompactDisc compactDisc) {
      super();
      this.cd1 = compactDisc;
    }
    public CDPlayer() {
      super();
    }
  //@Resource /*setter构造必需含有空构造函数*/
  //@Qualifier("jayChouAlbum2")
    public void setCd1(CompactDisc cd1) {
      this.cd1 = cd1;
    }
    @Override
    public void play() {
      // TODO Auto-generated method stub
      cd1.play();
    }
  }

  ```

  ```
  - 自定义限定符
  ```

  ```
  package com.web.spring4.bean.impl;
  import javax.annotation.Resource;
  import org.springframework.beans.factory.annotation.Autowired;
  import org.springframework.beans.factory.annotation.Qualifier;
  import org.springframework.stereotype.Component;
  import com.web.spring4.bean.CompactDisc;
  import com.web.spring4.bean.MediaPlayer;
  @Component
  public class CDPlayer implements MediaPlayer{
    @Resource
  //@Qualifier("jayChouAlbum2")    /*限定符即字符串为Bean ID*/
  	@QualiZfier("JCA")
	  private CompactDisc cd1;
  //@Autowired /*@Resource不可用于构造函数*/
  //@Qualifier("jayChouAlbum2")  /*@Qualifier不能用于构造函数*/
    public CDPlayer(CompactDisc compactDisc) {
      super();
      this.cd1 = compactDisc;
    }
    public CDPlayer() {
      super();
    }
  //@Resource /*setter构造必需含有空构造函数*/
  //@Qualifier("jayChouAlbum2")
    public void setCd1(CompactDisc cd1) {
      this.cd1 = cd1;
    }
    @Override
    public void play() {
      // TODO Auto-generated method stub
      cd1.play();
    }
  }
  ```

  ```
  package com.web.spring4.bean.impl;
  import org.springframework.beans.factory.annotation.Qualifier;
  import org.springframework.stereotype.Component;
  import com.web.spring4.bean.CompactDisc;
  @Component
  @Qualifier("JCA")
  public class JayChouAlbum2 implements CompactDisc{
    private String songs[] = {"告白气球"};
    private String artist = "周杰伦";
    @Override
    public void play() {
      // TODO Auto-generated method stub
      System.out.println("正在播放："+ songs[0] + "-" +artist);
    }
  }
  ```

  ```
  - 自定义@Qualifier注解
  ```

  ```
  package com.web.spring4.annotation;
  import java.lang.annotation.ElementType;
  import java.lang.annotation.Retention;
  import java.lang.annotation.RetentionPolicy;
  import java.lang.annotation.Target;
  import org.springframework.beans.factory.annotation.Qualifier;
  @Target({ElementType.FIELD,ElementType.CONSTRUCTOR,ElementType.METHOD,ElementType.TYPE})
  @Retention(RetentionPolicy.RUNTIME)
  @Qualifier
  public @interface JCA {

  }
  ```

  ```
  package com.web.spring4.annotation;
  import java.lang.annotation.ElementType;
  import java.lang.annotation.Retention;
  import java.lang.annotation.RetentionPolicy;
  import java.lang.annotation.Target;
  import org.springframework.beans.factory.annotation.Qualifier;
  @Target({ElementType.FIELD,ElementType.CONSTRUCTOR,ElementType.METHOD,ElementType.TYPE})
  @Retention(RetentionPolicy.RUNTIME)
  @Qualifier
  public @interface _1 {

  }
  ```

  ```
  package com.web.spring4.bean.impl;
  import javax.annotation.Resource;
  import org.springframework.stereotype.Component;
  import com.web.spring4.annotation.JCA;
  import com.web.spring4.annotation._2;
  import com.web.spring4.bean.CompactDisc;
  import com.web.spring4.bean.MediaPlayer;
  @Component
  public class CDPlayer implements MediaPlayer{

	@Resource
	@JCA
	@_2
	private CompactDisc cd1;
	public CDPlayer(CompactDisc compactDisc) {
		super();
		this.cd1 = compactDisc;
	}
	public CDPlayer() {
		super();
	}
	public void setCd1(CompactDisc cd1) {
		this.cd1 = cd1;
	}
	@Override
	public void play() {
		// TODO Auto-generated method stub
		cd1.play();
  }
  }
  ```

  ```
  package com.web.spring4.bean.impl;
  import org.springframework.stereotype.Component;
  import com.web.spring4.annotation.JCA;
  import com.web.spring4.annotation._2;
  import com.web.spring4.bean.CompactDisc;
  @Component
  @JCA
  @_2
  public class JayChouAlbum2 implements CompactDisc{
    private String songs[] = {"告白气球"};
    private String artist = "周杰伦";
    @Override
    public void play() {
      // TODO Auto-generated method stub
      System.out.println("正在播放："+ songs[0] + "-" +artist);
    }
  }
  ```


#### 条件化的Bean装配

* 适用场景：
  * bean只有在应用的类路径下包含特定的库时才创建。
  * 只有当其他某个特定Bean声明后才被创建。
  * 只有在某个特定环境变量才被创建。
* 使用方法
  * 注解@Conditional与@Bean一起使用于创建Bean的方法之上（使用JavaConfig装配）
  * 创建条件类，实现Condition接口。
    * [了解Condition接口的match方法参数](https://github.com/Garden12138/Spring4/blob/master/spring-source-code.md)
* Demo

```
package com.web.spring4.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Conditional;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.condition.ChooseJayChouAlbum;
import com.web.spring4.bean.impl.*;
/**
 * JavaConfig - 条件化装配Bean
 * @author Garden
 * 2018年3月13日
 */
@Configuration
public class CDPlayerConfig3 {
	@Bean
	@Conditional(ChooseJayChouAlbum.class)
	public  CompactDisc jayChouAlbum(){
		return new JayChouAlbum();
	}
	@Bean
	public  CompactDisc jayChouAlbum2(){
		return new JayChouAlbum2();
	}
}
```

```
package com.web.spring4.bean.condition;
import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.core.type.AnnotatedTypeMetadata;
public class ChooseJayChouAlbum implements Condition{
	@Override
	public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
		// TODO Auto-generated method stub
		Object ob = context.getBeanFactory().getBean("jayChouAlbum2");
		return null == ob ? false : true;
	}
}
```

#### 特殊条件化Bean装配-Profile Bean

* 使用场景：避免应用程序在环境迁移时出现代码重构的情况，如数据库配置，加密算法以及外部系统的集成等。
* 使用方法：
  * 配置Profile Bean：
    * JavaConfig装配：使用@Profile与@Bean结合使用，声明该bean只有在指定Profile激活的情况下才创建。

    ```
    package com.web.spring4.config;
    import org.springframework.context.annotation.Bean;
    import org.springframework.context.annotation.Configuration;
    import org.springframework.context.annotation.Profile;
    @Configuration
    public class DataSourceConfig {
      @Bean(name = "DataSource")
      @Profile("pro")
      public String proDataSource(){
        return "pro-dataSource";
      }
      @Bean(name = "DataSource")
      @Profile("dev")
      public String devDataSource(){
        return "dev-dataSource";
      }
    }
    ```

    * XML装配：使用< beans >标签属性profile，声明该bean只有在指定Profile激活的情况下才创建。

    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:context="http://www.springframework.org/schema/context"
    xmlns:p="http://www.springframework.org/schema/p"
    xmlns:mvc="http://www.springframework.org/schema/mvc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:tx="http://www.springframework.org/schema/tx"
    xmlns:task="http://www.springframework.org/schema/task"
    xmlns:c="http://www.springframework.org/schema/c"
    xmlns:util="http://www.springframework.org/schema/util"
    xsi:schemaLocation="http://www.springframework.org/schema/beans  
      http://www.springframework.org/schema/beans/spring-beans-3.0.xsd  
      http://www.springframework.org/schema/context  
      http://www.springframework.org/schema/context/spring-context.xsd
      http://www.springframework.org/schema/util
      http://www.springframework.org/schema/util/spring-util.xsd" >

      <beans profile="dev">
          <bean id="dataSource" class="java.lang.String" />
      <beans>

      <beans profile="pro">
          <bean id="dataSource" class="java.lang.String" />
      <beans>

    </beans>
    ```

  * 激活Profile Bean：
    * spring.profiles.active属性比spring.profiles.default优先级高
    * 作为DispatcherServlet的初始化参数

    ```
    <servlet>
        <servlet-name>springMVC</servlet-name>
        <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
        <init-param>
            <param-name>contextConfigLocation</param-name>
            <param-value>classpath:SpringMVC.xml,classpath:config.xml</param-value>
        </init-param>
        <!-- Servlet激活默认Profile Bean -->
        <init-param>
            <param-name>spring.profiles.default</param-name>
            <param-value>dev</param-value>
        </init-param>
        <!--  
        <init-param>
            <param-name>spring.profiles.active</param-name>
            <param-value>pro</param-value>
        </init-param>
        -->
        <load-on-startup>1</load-on-startup>
    </servlet>
    <servlet-mapping>
        <servlet-name>springMVC</servlet-name>
        <url-pattern>/</url-pattern>
    </servlet-mapping>
    ```

    * 作为WEB应用的上下文参数

    ```
    <!-- 上下文激活默认Profile Bean -->
    <context-param>
        <param-name>spring.profiles.default</param-name>
        <param-value>dev</param-value>
    </context-param>
    <!--  
    <context-param>
        <param-name>spring.profiles.active</param-name>
        <param-value>pro</param-value>
    </context-param>
    -->
    ```

    * 测试集成环境

    ```
    package com.web.spring4.test;
    import static org.junit.Assert.*;
    import javax.annotation.Resource;
    import org.junit.Test;
    import org.junit.runner.RunWith;
    import org.springframework.beans.factory.annotation.Autowired;
    import org.springframework.test.context.ActiveProfiles;
    import org.springframework.test.context.ContextConfiguration;
    import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
    import com.web.spring4.bean.impl.*;
    import com.web.spring4.config.DataSourceConfig;
    @RunWith(SpringJUnit4ClassRunner.class)
    @ContextConfiguration(classes=DataSourceConfig.class)
    @ActiveProfiles("pro")
    public class DataSourceConfigTest {
      @Autowired    /*顺序扫描*/
      private String dataSource;   
      @Test
      public void test(){
        System.out.println(dataSource.toString());
      }
    }
    ```

    * 作为JNDI条目
    * 作为环境变量
    * 作为JVM的系统属性

#### Bean的作用域

* 单例(Singleton)：在整个应用中，只创建一个bean实例，默认创建的bean的作用域为单例。
* 原型(Prototype)：每次注入或Spring应用上下文获取Bean时，新创建一个bean实例

```
//自动化装配
@Component
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
public class BeanDemo{
  ...
}
```

```
//JavaConfig装配
@Bean
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
public BeanDemo beanDemo(){
  return new BeanDemo();
}
```

```
//XML装配
< bean id = "beanDemo" class="" scope="prototype" />
```

* 会话(Session)：web应用中，为每个会话创建一个bean实例
* 请求(Request)：web应用中，为每个请求创建一个bean实例

```
//自动化装配
@Component
@Scope(ConfigurableBeanFactory.SCOPE_SESSION,proxyMode=ScopedProxyMode.INTERFACES)
//@Scope(ConfigurableBeanFactory.SCOPE_SESSION,proxyMode=ScopedProxyMode.TARGET_CLASS)
public class BeanDemo{
  ...
}
```

```
//JavaConfig装配
@Bean
@Scope(ConfigurableBeanFactory.SCOPE_SESSION,proxyMode=ScopedProxyMode.INTERFACES)
//@Scope(ConfigurableBeanFactory.SCOPE_SESSION,proxyMode=ScopedProxyMode.TARGET_CLASS)
public BeanDemo beanDemo(){
  return new BeanDemo();
}
```

```
//XML装配
< bean id = "beanDemo" class="" scope="session" >
    < aop:scoped-proxy proxy-target-class="false" />
    <aop:scoped-proxy />
< /bean >
```

#### 运行时值注入

* 值注入方式
  * 内部注入（硬编码注入）
  ```
  @Bean
  public CompactDisc jayChouAlbum3(){
    return new JayChouAlbum3("双截棍","周杰伦");
  }
  ```

  * 外部注入（运行时注入）
  ```
  data.properties
  songs = \u53CC\u622A\u68CD
  artist = \u5468\u6770\u4F26
  ```
  ```
  package com.web.spring4.config;
  import org.springframework.beans.factory.annotation.Autowired;
  import org.springframework.context.annotation.Bean;
  import org.springframework.context.annotation.Configuration;
  import org.springframework.context.annotation.PropertySource;
  import org.springframework.core.env.Environment;
  import com.web.spring4.bean.CompactDisc;
  import com.web.spring4.bean.impl.JayChouAlbum3;
  @Configuration
  @PropertySource("classpath:/data.properties")
  public class CDConfig {
    @Autowired
    private Environment env;
    @Bean
    public CompactDisc jayChouAlbum3(){
      return new JayChouAlbum3(env.getProperty("songs"),env.getProperty("artist"));
    }
  }
  ```
  [Environment API](https://github.com/Garden12138/Spring4/blob/master/spring-source-code.md)
    * 使用占位符：占位符用"${}"表示。自动装配和JavaConfig都需配置PropertySourcesPlaceholderConfigurer Bean，用于解析占位符
    ```
    自动装配
    public JayChouAlbum3(@Value("${album.songs}") String songs
    ,@Value("${album.artist}") String artist) {
      super();
      this.songs = songs;
      this.artist = artist;
    }
    ```
    ```
    JavaConfig
    package com.web.spring4.config;
    import org.springframework.beans.factory.annotation.Value;
    import org.springframework.context.annotation.Bean;
    import org.springframework.context.annotation.Configuration;
    import org.springframework.context.annotation.PropertySource;
    import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
    import com.web.spring4.bean.CompactDisc;
    import com.web.spring4.bean.impl.JayChouAlbum3;
    @Configuration
    @PropertySource("classpath:/data.properties")    //设置属性源
    public class CDConfig {
      @Bean    //必须配置 用于解析占位符
      public static PropertySourcesPlaceholderConfigurer placeholderCongigurer(){
        return new PropertySourcesPlaceholderConfigurer();
      }
      @Bean
      public CompactDisc jayChouAlbum3(@Value("${album.songs}") String songs,@Value("${album.artist}") String artist){
        return new JayChouAlbum3(songs,artist);
      }
    }
    ```
    ```
    XML
    <context:property-placeholder location="classpath:/data.properties"/>
    <bean id = "JayChouAlbum3" class = "com.web.spring4.bean.impl.JayChouAlbum3" >
        <constructor-arg value = "${album.songs}" />
        <constructor-arg value = "${album.artist}" />
    </bean>
    ```

    * 使用Spring表达式
      * 使用#{}标识。
      * 特性：
        * 表示字面量
        ```
        整型：#{1}
        浮点型：#{3.14}，#{9.87E4}
        String：#{'string'}
        Boolean：#{false}
        ```
        * 使用bean的ID来引用bean。
        * 访问bean的属性以及调用bean方法。
        ```
        #{JayChouAlbum3}
        #{JayChouAlbum3.songs}
        #{JayChouAlbum3.getSongs()}
        #{JayChouAlbum3.getSongs()?.toString()}    //若getSongs()返回为null，这不执行toString()
        ```
        * 对值进行算术，关系和逻辑运算。
        ```
        #{2 * T(java.lang.Math).PI > 1 and 1 > 0 ? "true or not null" : "false or null"}
        T()元算符的结果是Class对象
        ```
        * 正则表达式匹配。
        ```
        #{admin.email matches '[a-zA-z0-9._%+-]+@[a-zA-z0-9.-]+\\.com'}
        ```
        * 集合操作。
        ```
        #{JayChouAlbum5.songs[0]}
        #{JayChouAlbum5.songs[T(java.lang.Math).random * 10]}
        #{JayChouAlbum5.songs.?[title eq '夜曲']} -查询运算符 title为song属性
        #{JayChouAlbum5.songs.^[title eq '夜曲']} -查询第一项运算符
        #{JayChouAlbum5.songs.$[title eq '夜曲']} -查询最后一项运算符
        #{JayChouAlbum5.songs.！[title]} -投影运算符  
        ```
