## 集成security

### 介绍

* ```Spring Security```是一种基于```Spring AOP```和```Servlet```过滤器```Filter```的安全框架，它提供了全面的安全解决方案，提供在```Web```请求和方法调用级别的用户鉴权和权限控制。

### 关键实现

* ```WebSecurityConfigurerAdapter```，继承该类实现自定义```Spring Security```配置：

  ```java
  @Configurable
  @EnableWebSecurity
  public class WebSecurityConfig extends WebSecurityConfigurerAdapter{

      @Autowired
      private CustomAccessDeniedHandler customAccessDeniedHandler;
      @Autowired
      private UserDetailsService userDetailsService;
    
      /**
       * 静态资源设置
       */
      @Override
      public void configure(WebSecurity webSecurity) {
          //不拦截静态资源,所有用户均可访问的资源
          webSecurity.ignoring().antMatchers(
                  "/",
                  "/css/**",
                  "/js/**",
                  "/images/**",
                  "/layui/**"
                  );
      }
      
      /**
       * http请求设置
       */
      @Override
      public void configure(HttpSecurity http) throws Exception {
          //http.csrf().disable(); //注释就是使用 csrf 功能        
          http.headers().frameOptions().disable();//解决 in a frame because it set 'X-Frame-Options' to 'DENY' 问题            
          //http.anonymous().disable();
          http.authorizeRequests()
              .antMatchers("/login/**","/initUserData")//不拦截登录相关方法        
              .permitAll()        
              //.antMatchers("/user").hasRole("ADMIN")//user接口只有ADMIN角色的可以访问
              //.anyRequest()
              //.authenticated()//任何尚未匹配的URL只需要验证用户即可访问
              .anyRequest()
              .access("@rbacPermission.hasPermission(request, authentication)")//根据账号权限访问            
              .and()
              .formLogin()
              .loginPage("/")
              .loginPage("/login")   //登录请求页
              .loginProcessingUrl("/login")  //登录POST请求路径
              .usernameParameter("username") //登录用户名参数
              .passwordParameter("password") //登录密码参数
              .defaultSuccessUrl("/main")   //默认登录成功页面
              .and()
              .exceptionHandling()
              .accessDeniedHandler(customAccessDeniedHandler) //无权限处理器
              .and()
              .logout()
              .logoutSuccessUrl("/login?logout");  //退出登录成功URL
            
      }
    
      /**
       * 自定义获取用户信息接口
       */
      @Override
      public void configure(AuthenticationManagerBuilder auth) throws Exception {
          auth.userDetailsService(userDetailsService).passwordEncoder(passwordEncoder());
      }
    
      /**
       * 密码加密算法
       * @return
       */
      @Bean
      public BCryptPasswordEncoder passwordEncoder() {
          return new BCryptPasswordEncoder();
      }
  }
  ```

* 继承用户实体表，自定义实现```UserDetails```接口，扩展属性

  ```java
  @Data
  public class LoginUser extends UserEntity implements UserDetails {

    private static final long serialVersionUID = -9005214545793249372L;

    private Long id;// 用户id
    private String username;// 用户名
    private String password;// 密码
    private List<Role> userRoles;// 用户权限集合
    private List<Menu> roleMenus;// 角色菜单集合

    private Collection<? extends GrantedAuthority> authorities;
    public LoginUser() {
        
    }
    
    public LoginUser(String username, String password, Collection<? extends GrantedAuthority> authorities,
            List<Menu> roleMenus) {
        this.username = username;
        this.password = password;
        this.authorities = authorities;
        this.roleMenus = roleMenus;
    }


    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return this.authorities;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }

  }
  ```

* 自定义实现```UserDetailsService```接口，实现获取用户信息

  ```java
  @Service
  public class UserDetailServiceImpl implements UserDetailsService {
    
      private Logger log = LoggerFactory.getLogger(UserDetailServiceImpl.class);

      @Autowired
      private UserDao userDao;
      @Autowired
      private RoleDao roleDao;
      @Autowired
      private MenuDao menuDao;

      @Override
      public LoginUser loadUserByUsername(String username) throws UsernameNotFoundException {
          // 根据用户名查找用户
          LoginUser user = userDao.getUserByUsername(username);
          log.info(JSON.toJSONString(user));
          if (user != null) {
              log.info("UserDetailsService");
              //根据用户id获取用户角色
              List<Role> roles = roleDao.getUserRoleByUserId(user.getId());
              // 填充权限
              Collection<SimpleGrantedAuthority> authorities = new HashSet<SimpleGrantedAuthority>();
              for (Role role : roles) {
                  authorities.add(new SimpleGrantedAuthority(role.getRoleName()));
              }
              //填充权限菜单
              List<Menu> menus=menuDao.getRoleMenuByRoles(roles);
              return new UserEntity(username,user.getPassword(),authorities,menus);
          } else {
              log.error(username +" not found");
              throw new UsernameNotFoundException(username + " not found");
          }        
      }

  }
  ```

* 自定义实现```URL```权限控制：

  ```java
  @Component("rbacPermission")
  public class RbacPermission{

      private Logger log = LoggerFactory.getLogger(RbacPermission.class);

      private AntPathMatcher antPathMatcher = new AntPathMatcher();

      public boolean hasPermission(HttpServletRequest request, Authentication authentication) {
          Object principal = authentication.getPrincipal();
          boolean hasPermission = false;
          if (principal instanceof UserEntity) {
              // 读取用户所拥有的权限菜单
              List<Menu> menus = ((UserEntity) principal).getRoleMenus();
              log.info("用户拥有权限菜单数：" + menus.size());
              for (Menu menu : menus) {
                  if (antPathMatcher.match(menu.getMenuUrl(), request.getRequestURI())) {
                      hasPermission = true;
                      break;
                  }
              }
          }
          return hasPermission;
      }
  }
  ```

* 实现```AccessDeniedHandler```，自定义处理无权限请求：

  ```java
  @Component
  public class CustomAccessDeniedHandler implements AccessDeniedHandler {

      private Logger log = LoggerFactory.getLogger(CustomAccessDeniedHandler.class);

      @Override
      public void handle(HttpServletRequest request, HttpServletResponse response,
              AccessDeniedException accessDeniedException) throws IOException, ServletException {
          boolean isAjax = ControllerTools.isAjaxRequest(request);
          log.info("CustomAccessDeniedHandler handle");
          if (!response.isCommitted()) {
              if (isAjax) {
                  String msg = accessDeniedException.getMessage();
                  log.info("accessDeniedException.message:" + msg);
                  String accessDenyMsg = "{\"code\":\"403\",\"msg\":\"没有权限\"}";
                  ControllerTools.print(response, accessDenyMsg);
              } else {
                  request.setAttribute(WebAttributes.ACCESS_DENIED_403, accessDeniedException);
                  response.setStatus(HttpStatus.FORBIDDEN.value());
                  RequestDispatcher dispatcher = request.getRequestDispatcher("/403");
                  dispatcher.forward(request, response);
              }
          }

      }

      public static class ControllerTools {
          public static boolean isAjaxRequest(HttpServletRequest request) {
              return "XMLHttpRequest".equals(request.getHeader("X-Requested-With"));
          }

          public static void print(HttpServletResponse response, String msg) throws IOException {
              response.setCharacterEncoding("UTF-8");
              response.setContentType("application/json; charset=utf-8");
              PrintWriter writer = response.getWriter();
              writer.write(msg);
              writer.flush();
              writer.close();
          }
      }
  }
  ```

### 版本更新

* ```Spring Security5.7.0```后，```WebSecurityConfigurerAdapter```，详细可参考[官方文档](https://spring.io/projects/spring-security#samples)

### 备注

* 以上代码仅供参考，具体实现还需要结合实际业务场景进行调整。另外由于时间问题，本文仅提供```Spring Security```的基本使用，不涉及```Spring Boot```的集成，具体集成方法请参考官方文档。

### 参考文献

* [Spring Boot 2.X(十八)：集成 Spring Security-登录认证和权限控制](https://developer.aliyun.com/article/728140)
* [Spring Boot Security Auto-Configuration](https://www.baeldung.com/spring-boot-security-autoconfiguration)
* [Spring Security 即将弃用配置类 WebSecurityConfigurerAdapter](https://www.51cto.com/article/702252.html)