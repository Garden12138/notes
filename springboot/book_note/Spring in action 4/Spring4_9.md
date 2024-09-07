# Spring4

## 保护Web应用-Spring Security

#### 了解Spring Security

* Spring Security：基于Servlet规范中的Filter和Spring AOP实现的安全框架，能够在Web请求级别和方法调用级别处理身份验证和授权。

* Spring Security模块：保护Web应用需要配置，核心，标签库以及web模块。

| 模块 | 描述 |
| -------- | ----- |
| ACL | 支持通过访问控制列表为域对象提供安全性 |
| 切面 | 使用Spring Security注解时，使用基于AspectJ的切面 |
| CAS客户端 | 提供与Jasig的中心认证服务进行集成的功能 |
| 配置 | 通过XML和JavaConfig配置Spring Security的功能支持 |
| 核心 | 提供Spring Security基本库 |
| 加密 | 提供了加密和密码编码的功能 |
| LDAP | 支持基于LDAP进行认证 |
| OpenID | 支持使用OpenID进行集中式认证 |
| Remoting | 支持Spring Remoting |
| 标签库 | Spring Security的JSP标签库 |
| Web | 提供Spring Security基于Filter的Web安全性支持 |

#### 配置Spring Security

* 配置Spring Security的FilterProxy：使用Spring Security需借助一系列的Servlet Filter来提供安全性功能。为了避免在Web.xml或WebApplicationInitializer的扩展类中添加Filter带来的繁琐性，可以借助FilterProxy（DelegatingFilterProxy）将工作委托给Filter的实现类。
[![DelegatingFilterProxy把Filter的处理逻辑委托给Spring应用上下文定义的代理Filter bean.png](https://i.loli.net/2018/04/16/5ad445f5120c8.png)](https://i.loli.net/2018/04/16/5ad445f5120c8.png)
```
<!-- web.xml -->
<filter>
    <filter-name>springSecurityFilterChain</filter-name>
    <filter-class>org.springframework.web.filter.DelegatingFilterProxy</filter-class>
</filter>
<filter-mapping>
    <filter-name>springSecurityFilterChain</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```
```
//基于WebApplicationInitializer配置，Web容器会发现该类并注册DelegatingFilterProxy
public class SecurityWebInitializer extends AbstractSecurityWebApplicationInitializer {
}
```
* 配置启动Web安全性功能
  * 在Spring应用上下文，实现WebSecurityConfigurer的实现类配置
  * 在Spring应用上下文，扩展WebSecurityConfigurerAdapter配置
  ```
  @Configuration
  //@EnableWebSecurity   //启动Web安全性
  @EnableWebMvcSecurity  //启动Web Mvc安全性
  public class SecurityConfig extends WebSecurityConfigurerAdapter {
    //重载configure()方法，实现细节Web安全性配置

    //@Override
    //protected void configure(AuthenticationManagerBuilder auth) throws Exception {
    //配置user-detail服务  
    //}

    //@Override
    //protected void configure(HttpSecurity http) throws Exception {
    // 配置如何通过拦截器保护请求  
    //}

    //@Override
    //protected void configure(WebSecurity http) throws Exception {
    // 配置Spring Security的Filter链
    //}
  }
  ```
    * 配置用户存储：用户存储包括用户信息的保存以及用户信息认证两方面。重载configure(AuthenticationManagerBuilder auth)方法。
      * 基于内存的用户存储：用户信息的保存以及认证基于内存层面，适用于开发环境。
      ```
      @Override
      protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth
        .inMemoryAuthentication()              //启用内存用户存储
         .withUser("user")                     //添加用户，返回值为UserDetailsBuilder
          .password("password").roles("USER")  //添加该用户密码以及权限等用户详细信息
         .and()                                //连接同级配置
         .withUser("admin")
          .password("password").roles("USER","ADMIN");
      }
      ```
        * UserDetailsBuilder的常用方法
          * accountExpired(boolean)：定义账号是否已经过期。
          * accountLocked(boolean)：定义账号是否已经锁定。
          * disabled(boolean)：定义账号是否已被禁用。
          * credentialsExpired(boolean)：定义凭证是否已经过期。
          * and()：连接配置。
          * authorities(GrantedAuthority...)：授予某个用户一项或多项权限。
          * authorities(List<? extends GrantedAuthority>)：授予某个用户一项或多项权限。
          * authorities(String...)：授予某个用户一项或多项权限，需加上前缀"ROLE_"。
          * roles(String...)：授予某个用户一项或多项角色，自动加上前缀"ROLE_"。
          * password(String...)：定义用户密码。
      * 基于数据库表的用户存储：用户信息的保存以及认证基于数据库表层面，适用于生成环境。
      ```
      @Autowired
      private DataSource dataSource;
      @Override
      protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth
        .jdbcAuthentication()      //启用数据库表用户存储
         .dataSource(dataSource)
         .usersByUsernameQuery("select username,password,true "+"from tableName where username=?")    //自定义查询，所有查询都将用户名作为唯一的参数
         .authoritiesByUsernameQuery("select username,'ROLE_USER' from tableName where username=?")
         .passwordEncoder(new StandardPasswordEncoder("53cr3t"));    //转码，存储数据库的密码不是明文密码时使用。passwordEncoder()接受PasswordEncoder接口的任意实现，Spring Security中有BCryptPasswordEncoder,NoOpPasswordEncoder和StandardPasswordEncoder。可以自定义实现，PasswordEncoder接口如下代码片段
      }
      ```
      ```
      public interface PasswordEncoder{
        String encode(CharSequence rawPassword);
        boolean matches(CharSequence rawPassword,String encodePassword);
      }
      ```
      * 基于LDAP的用户存储
      ```
      @Override
      protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth
        .ldapAuthentication()    //启用LDAP用户存储
         .userSearchBase("ou=people")    //指定查询基础
         .userSearchFilter("(uid={0})")  //为查询提供过滤条件
         .groupSearchBase("ou=groups")
         .groupSearchFilter("member={0}")
         .passwordCompare()      //密码比对
         .passwordEncoder(new MD5PasswordEncoder())    //转码
         .passwordAttribute("passcode")    //声明密码属性的名称
       //.contextSource()    //远程LDAP服务器
        //.url("ldap://habuma.com:389/dc=habuma,dc=com");
         .contextSource()    //配置潜入式LDAP服务器
          .root("dc=habuma,dc=com")
          .ldif("classpath:users.ldif");
      }
      ```
      * 基于自定义的用户存储
      ```
      @Override
      protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth
        .UserDetailsService(new UserDetailsServiceImpl());    //启用自定义用户存储，UserDetailsService接口如下代码片段
      }
      ```
      ```
      public interface UserDetailsService{
        UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;
      }
      ```
    * 配置请求保护拦截：重载configure(HttpSecurity http)方法。
    ```
    @Override
    protected void configure(HttpSecurity http) throws Exception {
      http
      .authorizeRequests()    //返回对象用来配置请求级别的安全性细节
       .antMatchers("/spitters/me")    //支持Ant风格的通配符，匹配请求URL
        .authenticated()    //保护URL配置方法，允许认证过的用户访问                 
     //.antMatchers(HttpMethod.POST,"/spittles")
      //.authenticated()
     //.antMatchers("/spitters/**","/spittles/mine")
      //.authenticated()
     //.regexMatchers("/spitters/.*")    //支持正则表达式匹配请求URL
      //.authenticated()
       .anyRequest()    //任意请求
        .permitAll();   //保护URL配置方法，允许所有用户访问
      .and()
      .requiresChannel()    //启用强制通道安全性配置
       .antMatchers("/spitter/form").requiresSecure();    //需https
     //.antMatchers("/spitter/form").requiresInSecure();  //不需https    
    }
    ```
    * _
      * 保护URL配置方法
        * access(String)：参数为SpEL表达式，若结果为true则允许访问。
        * anonymous()：允许匿名用户访问。
        * authenticated()：允许认证过的用户访问。
        * denyAll()：无条件拒绝所有访问。
        * fullyAuthenticated()：允许完整认证过的用户访问（不通过Remember-me功能认证）。
        * hasAnyAuthority(String...)：如果用户具备给定权限中的某一个就允许访问。
        * hasAnyRole(String...)：如果用户具备给定角色中的某一个就允许访问。
        * hasAuthority(String...)：如果用户具备给定权限就允许访问。
        * hasRole(String...)：如果用户具备给定角色就允许访问。
        * hasIpAddress(String...)：如果请求来自给定IP地址的话就允许访问。
        * not()：对其他方法取反。
        * permitAll()：无条件允许访问。
        * rememberMe():如果用户是通过Remember-me功能认证的，就允许访问。
      * PS：保护URL配置方法不能复合使用。使用Spring Security表达式扩展的SpEL表达式可以解决此问题。
      * Spring Security表达式扩展的SpEL表达式
        * authentication:用户的认证对象。
        * denyAll：结果始终为false。
        * hasAnyRole(list of roles)：如果用户被授予了列表中任意的指定角色，结果为true。
        * hasRole(role)：如果用户被授予了指定的角色，结果为true。
        * hasIpAddress(IP Address)：如果请求来自指定IP的话，结果为true。
        * isAnonymous()：如果当前用户为匿名用户，结果为true。
        * isAuthenticated()：如果当前用户经过了认证，结果为true。
        * isFullAuthenticated()：如果当前用户经过了完整认证（不通过Remember-me功能认证），结果为true。
        * isRemember()：如果当前用户通过Remember-me功能认证，结果为true。
        * permitAll：结果始终为true。
        * principal：用户的principal对象。
        ```
        //demo
        .autMatchers("spitters/me")
         .access("hasRole('ROLE_USER') and hasIpAddress('192.168.1.2')");
        ```
    * 配置登录页面：若重载configure(HttpSecurity http)方法，需重新启用默认登录页面。若需自定义登录页面，则可以参考默认登陆页面源码，编写自定义登录页面(需注意表单提交URL)。
    ```
    @Override
    protected void configure(HttpSecurity http) throws Exception {
      http
      .formLogin()    //重新启用默认的登陆页
      ...
    }
    ```
    * 其他功能
      * 其他认证方式
        * 启用HTTP Basic认证：适用于Restful API（一般都是token认证）
        ```
        @Override
        protected void configure(HttpSecurity http) throws Exception {
          http
          .formLogin()
           .loginPage("/login")
          .and()
          .httpBasic()    //启用HTTP Basic认证
           .realmName("spittr")    //指定域
        }
        ```
        * 启用Remember-me功能：适用于登录过一次就不需再登录的场景
        ```
        @Override
        protected void configure(HttpSecurity http) throws Exception {
          http
          .formLogin()
           .loginPage("/login")
          .and()
          .rememberMe()    //启用Remember-me功能
           .tokenValiditySeconds(2419200)    //设置token有效时间
           .key("spittrKey")    //设置私钥
        }
        ```
        ```
        <!-- 登录请求必须包含一个名字为remember-me的参数 -->
        <input id="remember_me" name="remember-me" type="checkbox" />
        <label for="remember_me" class="inline">Remember me</label>
        ```
      * 退出：退出登录。当用户点击退出链接，会发送"/logout"请求，该请求被Spring Security的LogoutFilter处理。Remember-me Token都会被清除掉。退出完成后，浏览器重定向登录页。
      ```
      <a th:href="@{/logout}">Logout</a>
      ```
        * 退出完成重定向至指定页面
        ```
        @Override
        protected void configure(HttpSecurity http) throws Exception {
          http
          .formLogin()
           .loginPage("/login")
          .and()
          .logout()    //配置退出行为
           .logoutUrl("/logout")    //配置退出请求路径
           .logoutSuccessUrl("/")   //配置退出成功后重定向路径
        }
        ```
      * 保护视图
        * 使用Spring Security的JSP标签库
          * < security:accesscontrollist >：如果用户通过访问控制列表授予了指定的权限，那么渲染该标签体中的内容。
          * < security:authentication >：渲染当前用户认证对象的详细信息。用于访问认证信息的细节。
            * authorities属性：一组用于表示用户所授予权限的GrantedAuthority对象。
            * Credentials属性：用于核实用户凭证（密码）。
            * details属性：认证的附加消息（IP地址）。
            * principal属性：用户的基本信息对象。
          * ~
          ```
          <%@ taglib prefix="security" uri="http://www.springframework.org/security/tags" %>
          <security:authentication property="principal.username" var="loginId" scope="request" />
          ```
          * < security:authorize >：如果用户被授予了特定的权限或SpEL表达式的计算结果为true，那么渲染该标签体中的内容。用于条件性的渲染内容。
          ```
          <%@ taglib prefix="security" uri="http://www.springframework.org/security/tags" %>
          <security:authorize access="hasRole('ROLE_USER')">
              ...
          </security:authorize>
          ```
        * 使用Thymeleaf的Spring Security方言
          * sec:authorize-acl等同于< security:accesscontrollist >
          * sec:authentication等同于< security:authentication >
          * sec:authorize等同于< security:authorize >
          * sec:authorize-expr表示sec:authorize属性的别名
          * sec:authorize-url等同于使用url属性的< security:authorize >
          ```
          //注册Thymeleaf的Spring Security安全方言
          templateEngine.addDialect(new springSecurityDialect());
          ```
