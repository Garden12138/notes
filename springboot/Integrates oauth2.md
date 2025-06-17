## 集成Oauth2

### 以授权码模式为例

* 引入依赖

  ```xml
  <dependency>
      <groupId>org.springframework.cloud</groupId>
      <artifactId>spring-cloud-starter-oauth2</artifactId>
      <version>2.2.5.RELEASE</version>
  </dependency>
  <dependency>
      <groupId>org.springframework.cloud</groupId>
      <artifactId>spring-cloud-starter-security</artifactId>
      <version>2.2.5.RELEASE</version>
  </dependency>
  ```

* 认证服务器配置

  ```java
  @Configuration
  @EnableAuthorizationServer
  public class AuthorizationServerConfig extends AuthorizationServerConfigurerAdapter {

      @Autowired
      private PasswordEncoder passwordEncoder;

      @Autowired
      private AuthenticationManager authenticationManager;

      @Autowired
      private UserService userService;

      /**
       * 使用密码模式需要配置
       */
      @Override
      public void configure(AuthorizationServerEndpointsConfigurer endpoints) {
          endpoints.authenticationManager(authenticationManager)
                  .userDetailsService(userService);
      }

      @Override
      public void configure(ClientDetailsServiceConfigurer clients) throws Exception {
          clients.inMemory()
                  .withClient("Is3Sm7qA")//配置client_id
                  .secret(passwordEncoder.encode("SgIhNhg6"))//配置client_secret
                  .accessTokenValiditySeconds(864000)//配置访问token的有效期
                  .refreshTokenValiditySeconds(864000)//配置刷新token的有效期
                  .redirectUris("http://www.baidu.com")//配置redirect_uri，用于授权成功后跳转
                  .scopes("all")//配置申请的权限范围
                  .authorizedGrantTypes("authorization_code", "password");//配置grant_type，表示授权类型
      }

      @Override
      public void configure(AuthorizationServerSecurityConfigurer security) throws Exception {
          security.tokenKeyAccess("permitAll()")
                  .checkTokenAccess("isAuthenticated()");
      }

  }
  ```

* 资源服务器配置

  ```java
  @Configuration
  @EnableResourceServer
  public class ResourceServerConfig extends ResourceServerConfigurerAdapter {

      @Override
      public void configure(HttpSecurity http) throws Exception {
          http.authorizeRequests()
                  .anyRequest()
                  .authenticated()
                  .and()
                  .requestMatchers()
                  .antMatchers("/resource/**");//配置需要保护的资源路径
      }
  }
  ```


* Security配置

  ```java
  @Configuration
  @EnableWebSecurity
  public class SecurityConfig extends WebSecurityConfigurerAdapter {

      @Bean
      public PasswordEncoder passwordEncoder() {
          return new BCryptPasswordEncoder();
      }

      @Bean
      @Override
      public AuthenticationManager authenticationManagerBean() throws Exception {
          return super.authenticationManagerBean();
      }

      @Override
      public void configure(HttpSecurity http) throws Exception {
          http.csrf()
                  .disable()
                  .authorizeRequests()
                  .antMatchers("/oauth/**", "/login/**", "/logout/**")
                  .permitAll()
                  .anyRequest()
                  .authenticated()
                  .and()
                  .formLogin()
                  .permitAll();
      }
  }
  ```

* 用户服务实现

  ```java
  @Service
  public class UserService implements UserDetailsService {

      private List<User> userList;
      @Autowired
      private PasswordEncoder passwordEncoder;

      @PostConstruct
      public void initData() {
          String password = passwordEncoder.encode("oauth2@2024");
          userList = new ArrayList<>();
          userList.add(new User("admin", password, AuthorityUtils.commaSeparatedStringToAuthorityList("admin")));
          userList.add(new User("client", password, AuthorityUtils.commaSeparatedStringToAuthorityList("client")));
      }

      /**
       * 根据用户名查询用户信息（正常从数据库获取用户信息）
       *
       * @param username
       * @return
       * @throws UsernameNotFoundException
       */
      @Override
      public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
          List<User> findUserList = userList.stream().filter(user -> user.getUsername().equals(username)).collect(Collectors.toList());
          if (!CollectionUtils.isEmpty(findUserList)) {
              return findUserList.get(0);
          } else {
              throw new UsernameNotFoundException("用户名或密码错误");
          }
      }

  }
  ```

* 测试资源

  ```java
  @RestController
  @RequestMapping("/resource")
  public class ResourceController {

      @RequestMapping("/hi")
      public String hi() {
          return "hello, i'm resource server";
      }

  }
  ```

* 验证

  * 浏览器访问获取授权码

    ```bash
    http://localhost:9401/oauth/authorize?response_type=code&client_id=Is3Sm7qA&redirect_uri=http://www.baidu.com&scope=all&state=normal
    ```

  * 根据授权码获取访问令牌

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/oauth2_token.png)

  * 携带访问令牌访问资源

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/oauth2_resource.png)


### 参考文献

* [SpringBoot整合OAuth2](https://developer.aliyun.com/article/824639)
* [Spring Boot Security Oauth2之客户端模式及密码模式实现](https://github.com/smltq/spring-boot-demo/blob/master/security-oauth2-credentials/README.md)
* [SpringBoot-OAuth2-JWT-WebFlux-ResourceServer](https://blog.hanqunfeng.com/2020/12/02/springboot-oauth2-jwt-webflux-resourceserver/)
* [OAuth2 WebFlux](https://www.docs4dev.com/docs/zh/spring-security/5.1.2.RELEASE/reference/webflux-oauth2.html)