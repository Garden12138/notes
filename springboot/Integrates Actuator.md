## 集成 Actuator

> pom 引入依赖

  ```bash
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-security</artifactId>
  </dependency>
  ```

> properties 编写配置

* 设置```actuator```配置：
  
  ```bash
  management:
  endpoint:
    shutdown:
      # 不需暴露端点时设置为true
      enabled: false
  endpoints:
    web:
      # 暴露端点的基础路径
      base-path: /exporter
      # 暴露端点的指标，默认为health和info，include为设置包含的指标，exclude为设置排除的指标。'*' 符号代表所有
      exposure:
        include: '*'
        #exclude: beans
  ```
  
  关于指标的详细信息可参考[这里](http://www.ityouknow.com/springboot/2018/02/06/spring-boot-actuator.html)

* 设置```spring security```用户密码访问配置：

  ```bash
  spring:
    security:
      user:
        name: ${ss.username}
        password: ${ss.password}
  ```

  除此之外还需新增配置类```ActuatorWebSecurityConfigurationAdapter```，针对暴露端点的基础路径添加访问权限：

  ```bash
  @Configuration
  @EnableWebSecurity
  public class ActuatorWebSecurityConfigurationAdapter extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
                .antMatchers("/exporter/**").authenticated()
                .anyRequest().permitAll()
                .and()
                .httpBasic();
    }
  }
  ```

> 启动SpringBoot项目并访问

  * 浏览器输入访问```prometheus```指标地址，如：

    ```bash
    http://${ip}:${port}/exporter/prometheus
    ```

  * 浏览器弹出用户密码，正确输入登录后，可查看指标信息：
    
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-10-01_16-24-09.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-10-01_16-24-38.png)



