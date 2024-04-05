## 集成 Session

> 简介

* 分布式会话（```Session```）场景中，通常集成```Redis```并借助```Spring Session```框架管理。

> 集成步骤

* 集成```Redis```，[单例](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Standalone.md)、[主从复制](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Master-Slave.md)、[哨兵](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Sentinel.md)以及[集群](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis%20Cluster.md)。

* 引入依赖

  ```bash
  <dependencies>  
      <!-- Spring Session Data Redis -->  
      <dependency>  
          <groupId>org.springframework.session</groupId>  
          <artifactId>spring-session-data-redis</artifactId>  
      </dependency>  
      <!-- other... -->  
  </dependencies>
  ```

* 添加配置类，使用注解```@EnableRedisHttpSession```启用```Spring Session```。
  
  ```bash
  @Configuration
  @EnableRedisHttpSession(maxInactiveIntervalInSeconds = 10)
  public class SpringSessionRedisConfig {

  }
  ```

* 使用```Spring Session Redis```管理会话：

  ```bash
  import javax.servlet.http.HttpSession;  
  
  // ... 在某个控制器或者服务中  
  @Autowired  
  private HttpSession session;  
  
  public void someMethod() {  
      session.setAttribute("someKey", "someValue");  
      String value = (String) session.getAttribute("someKey");  
      // ...  
  }
  ```

  ```Redis```中所存储的数据结构由三部分组成：

    * ```Key```为```spring:session:sessions:${sessionId}```，```Value```为```Hash```类型，如：
      
      ```bash
      {
          "lastAccessedTime": 1712305485000,
          "creationTime": 1712305485000,
          "maxInactiveInterval": 1800,
          "sessionAttr:k": "v"
      }
      ```

      ```creationTime```为创建时间，```lastAccessedTime```为最后访问时间，```maxInactiveInterval```为```session```失效的间隔时长，这些字段为系统字段，```sessionAttr:k```是```HttpServletRequest.setAttribute("k"，"v")```存入的，它可存在多个键值对，用户信息存放在```Session```中的数据存放于此。键对应的默认```TTL```是35分钟。

    * ```Key```为````spring:session:expirations:${timestamp}```，```Value```为```set```类型，存在第三种```Key```。键对应的默认```TTL```是30分钟。
    * ```Key```为```spring:session:sessions:expires:${sessionId}```，```Value```为空。键对应的默认```TTL```是30分钟。

> 存在问题

* 实践发现当```Redis```客户端服务保持正常，上诉产生的三种```Key```会大量存在```Redis```中：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/WechatIMG4012.png)

  目前个人觉得合适的解决办法是自定义```Session```管理，因为分布式```Session```管理的核心在于将```Session```存储在中间件（```Redis```），我们可以利用```WebServlet Filter```以及```Spring```容器化实现自定义```Session```，如

  ```bash
  // 过滤器
  public class GardenAuthFilter implements Filter {

      private final RedisUtil redisUtil;

      public GardenAuthFilter(RedisUtil redisUtil) {
          this.redisUtil = redisUtil;
      }

      @Override
      public void init(FilterConfig filterConfig) throws ServletException {
          Filter.super.init(filterConfig);
      }

      @Override
      public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) throws IOException, ServletException {
          HttpServletRequest httpServletRequest = (HttpServletRequest) servletRequest;
          Cookie[] cookies = httpServletRequest.getCookies();
          String sessionId = "";
          for (Cookie cookie : cookies) {
              if ("garden-consumer-session".equals(cookie.getName())) {
                  sessionId = cookie.getValue();
              }
          }
          if (StringUtils.isBlank(sessionId)) {
              throw new RuntimeException("非法访问");
          }
          Object sessionObj = redisUtil.get("garden:consumer:session:".concat(sessionId));
          if (Objects.isNull(sessionObj)) {
              throw new RuntimeException("权限失效，请重新登录");
          }
          filterChain.doFilter(servletRequest, servletResponse);
      }

      @Override
      public void destroy() {
          Filter.super.destroy();
      }

  }
  
  // 请求过滤配置
  @Configuration
  public class FilterConfiguration {

      @Autowired
      private RedisUtil redisUtil;

      @Bean(name = "gardenAuthFilter")
      public FilterRegistrationBean<GardenAuthFilter> gardenAuthFilter() {
          FilterRegistrationBean filterRegistrationBean = new FilterRegistrationBean();
          filterRegistrationBean.setFilter(new GardenAuthFilter(redisUtil));
          filterRegistrationBean.setOrder(0);
          filterRegistrationBean.addUrlPatterns("/redisSessionGet");
          Map<String, String> initParams = new HashMap<>();
          initParams.put("excludes", "/login");
          filterRegistrationBean.setInitParameters(initParams);
          return filterRegistrationBean;
      }

  }
  ```

  验证时，可启动两个不同端口的实例，一个实例用于访问```/login```接口，另一个用于访问```/redisSessionGet```接口。

> 参考文献

* [Spring Session](https://spring.io/projects/spring-session)
* [Spring-Session实现session共享原理及解析](https://blog.csdn.net/Along1325/article/details/123133306)