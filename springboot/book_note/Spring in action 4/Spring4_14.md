# Sprin4
## Spring Security的应用-保护方法应用

#### 使用注解保护方法

* Spring Security自带的@Secured注解
  * 启动支持@Secured注解的方法安全性
  ```
  @Configuration
  @EnableGlobalMethodSecurity(securedEnabled=true)
  public class SecuredConfig extends GlobalMethodSecurityConfiguration {
    //设置WEB层的安全认证配置
    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
      auth
       .inMemoryAuthentication()
       .withUser("user").password("password").roles("USER");
     }
   }
  ```
  * 在目标方法上添加注解
  ```
  @Secured({"ROLE_SPITTER", "ROLE_ADMIN"})/*表示只有数组中的任一权限时才可以调用此方法*/
  public void addSpittle(Spittle spittle) {
    System.out.println("Method was called successfully");
  }
  ```
* JSR-250的@RolesAllowed注解
  * 启动支持RolesAllowed注解的方法安全性
  ```
  @Configuration
  @EnableGlobalMethodSecurity(jsr250Enabled=true)
  public class JSR250Config extends GlobalMethodSecurityConfiguration {
    ...
  }
  ```
  * 在目标方法上添加注解
  ```
  @RolesAllowed("ROLE_SPITTER")
  public void addSpittle(Spittle spittle) {
    System.out.println("Method was called successfully");
  }
  ```
* 支持表达式驱动的注解（@PreAuthorize，@PostAuthorize，@PreFilter，@PostFilter）
  * 启动支持表达式注解的方法安全性
  ```
  @Configuration
  @EnableGlobalMethodSecurity(prePostEnabled=true)
  public class ExpressionSecurityConfig extends GlobalMethodSecurityConfiguration {
    ...
  }
  ```
  * 在目标方法上添加注解
  ```
  //方法调用之前，计算表达式，结果为true则允许访问；为false则拒绝访问。
  @PreAuthorize("(hasRole('ROLE_SPITTER') and #spittle.text.length() <= 140)"+"or hasRole('ROLE_PREMIUM')")
  public void addSpittle(Spittle spittle) {
    // ...
  }
  //方法调用之后，计算表达式，结果为true则允许返回；为false则拒绝返回并抛出异常。
  @PostAuthorize("returnObject.spitter.username == principal.username")
  public Spittle getSpittleById(long id) {
    // ...
  }
  @PreAuthorize("hasAnyRole({'ROLE_SPITTER', 'ROLE_ADMIN'})")
  //方法调用之后，计算表达式该方法所返回集合的每个成员，将计算结果为false的成员移除。
  @PostFilter( "hasRole('ROLE_ADMIN') || "+ "filterObject.spitter.username == principal.name")
  public List<Spittle> getOffensiveSpittles() {//
    ...
  }
  @PreAuthorize("hasAnyRole({'ROLE_SPITTER', 'ROLE_ADMIN'})")
  //方法调用之前，计算表达式该方法参数集合的每个成员，将计算结果为false的成员移除。
  @PreFilter( "hasRole('ROLE_ADMIN') || "+ "targetObject.spitter.username == principal.name")
  public void deleteSpittles(List<Spittle> spittles) {
    // ...
  }
  ```
  * PS:使用许可计算器代替@PostFilter与@PreFilter复杂的SpEL表达式
    * 重载GlobalMethodSecurityConfiguration的createExpressionHandler()以支持@PostFilter与@PreFilter注解中的hasPermission()表达式。
    ```
    @Configuration
    @EnableGlobalMethodSecurity(prePostEnabled=true)
    public class ExpressionSecurityConfig extends GlobalMethodSecurityConfiguration {
      @Override
      protected MethodSecurityExpressionHandler createExpressionHandler(){
        DefaultMethodSecurityExpressionHandler expressionHandler = new DefaultMethodSecurityExpressionHandler();
        expressionHandler.setPermissionEvaluator(new SpittlePermissionEvaluator());
        return expressionHandler;
      }
    }
    ```
    * 定义许可计算器为hasPermission()提供实现逻辑
    ```
    public class SpittlePermissionEvaluator implements PermissionEvaluator {
      private static final GrantedAuthority ADMIN_AUTHORITY = new GrantedAuthorityImpl("ROLE_ADMIN");
      public boolean hasPermission(Authentication authentication,Object target, Object permission) {
        if (target instanceof Spittle) {
          Spittle spittle = (Spittle) target;
          String username = spittle.getSpitter().getUsername();
          if ("delete".equals(permission)) {
            return isAdmin(authentication) || username.equals(authentication.getName());
          }
        }
        throw new UnsupportedOperationException("hasPermission not supported for object <" + target + "> and permission <" + permission + ">");
      }
      public boolean hasPermission(Authentication authentication,
        Serializable targetId, String targetType, Object permission) {
          throw new UnsupportedOperationException();
        }
      private boolean isAdmin(Authentication authentication) {
        return authentication.getAuthorities().contains(ADMIN_AUTHORITY);
      }
    }
    ```
    * 在目标方法上添加注解
    ```
    @PreAuthorize("hasAnyRole({'ROLE_SPITTER', 'ROLE_ADMIN'})")
    @PreFilter("hasPermission(targetObject, 'delete')")
    public void deleteSpittles(List<Spittle> spittles) {
      //...
  }
    ```
