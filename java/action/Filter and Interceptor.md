## 过滤器与拦截器

> 认识过滤器

  * 过滤器Filter，是Servlet中常用技术，通常用于对Web服务器（部署项目的容器）的资源管理，如对Servlet，静态Html文件等进行拦截，从而实现特殊功能，如实现URL级别的权限访问，敏感词过滤，压缩响应信息等一些高级功能。
  * [定义过滤器只需要实现Filter接口，并注册配置过滤器（相关描述信息：过滤器名称，拦截Url，应用Servlet）即可。传统的SSM或SSH应用中，可在web.xml文件配置过滤器的相关描述信息；SpringBoot应用中我们可使用Servlet3.0提供@WebFilter注解定义拦截器](https://gitee.com/FSDGarden/springboot/tree/filter-interceptor)。
  * Filter接口定义了三个方法：
    * init()：容器启动初始化时调用，在整个生命周期中只会被调用一次。这个方法必须执行成功，否则过滤器不生效。
    * doFilter()：容器拦截对应请求时调用，可使用FilterChain来调用执行下一个过滤器Filter。
    * destroy()：容器销毁过滤器实例时调用该方法，一般在方法中销毁或关闭资源，在整个生命周期中只会被调用一次。
    ```
    public class MyFilter implements Filter {
        @Override
        public void init(FilterConfig filterConfig) throws ServletException {
            System.out.println("MyFilter过滤器初始化成功...");
        }

        @Override
        public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) throws IOException, ServletException {
            System.out.println("MyFilter过滤器处理中...");
            //处理业务逻辑
            //...
            //执行下一个过滤器Filter
            filterChain.doFilter(servletRequest, servletResponse);
        }

        @Override
        public void destroy() {
            System.out.println("MyFilter过滤器销毁中...");
        }
    }
    ```

> 认识拦截器
  * 拦截器Interceptor，是动态拦截行为中常使用的技术，它提供一种在具体请求执行前后进行拦截处理的机制（类似Spring的AOP机制）。它是链式调用，一个应用中可同时存在多个拦截器，一个请求也可以触发多个拦截器，每个拦截器的调用顺序会依据声明顺序执行。
  * [定义拦截器只需实现HandlerInterceptor接口的组件，并在自定义的拦截器处理类进行注册（相关描述信息：需拦截URL或排除URL）](https://gitee.com/FSDGarden/springboot/tree/filter-interceptor)。
  * HandlerInterceptor接口定义了三个方法：
    * preHandle()：这个方法将在请求处理之前进行调用。如果该方法返回值为false，将视为当前请求结束，不仅自身的拦截器会失效，还会导致其链式调用下的拦截器也会失效。多个拦截器，先声明的拦截器preHandle()方法先执行。
    * postHandle()：只有在preHandle()方法返回为true时并在DispatcherServlet返回渲染视图之前进行调用。多个拦截器，后声明的拦截器postHandle()方法先执行。
    * afterCompletion()：只有在pretHandle()方法返回为true时并在DispatcherServlet返回渲染视图之后进行调用。多个拦截器，后声明的拦截器afterCompletion()方法先执行。
    * 多个拦截器，先执行完所有拦截器的preHandle()方法，再执行所有拦截器的postHandle()方法，最后再执行所有拦截器的afterCompletion()方法。
    ```
    @Component
    public class MyInterceptor implements HandlerInterceptor {

        @Override
        public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
            System.out.println("Interceptor 前置");
            return true;
        }
        
        @Override
        public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) throws Exception {
            System.out.println("Interceptor 处理中");
        }
        
        @Override
        public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
            System.out.println("Interceptor 后置");
        }
    }
    ```

> 过滤器与拦截器的不同
  * 实现原理不同
    
    过滤器基于函数回调，拦截器基于Java的反射机制（动态代理）

    * 基于函数回调，在自定义过滤器实现的doFilter方法中的FilterChain参数，实际为一个回调接口，实现类为ApplicationFilterChain，其doFilter方法中通过调用自定义过滤器doFilter()实现回调。
      ```
      //FilterChain接口
      public interface FilterChain {

          void doFilter(ServletRequest var1, ServletResponse var2) throws IOException, ServletException;

      }
      //ApplicationFilterChain实现类
      public final class ApplicationFilterChain implements FilterChain {

          @Override
          public void doFilter(ServletRequest request, ServletResponse response){
            ...
            internalDoFilter(request,response);
          }
          
          private void internalDoFilter(ServletRequest request, ServletResponse response){
              if (pos < n) {
                  //获取第pos个filter    
                  ApplicationFilterConfig filterConfig = filters[pos++];
                  Filter filter = filterConfig.getFilter();
                  ...
                  filter.doFilter(request, response, this);
              }
            }
      }
      ```

      ![Snipaste_2020-10-05_16-25-59.png](https://i.loli.net/2020/10/05/iOBXIuEhDlQGfvA.png)

    * 基于Java的反射机制。

      ![Snipaste_2020-10-05_16-48-52.png](https://i.loli.net/2020/10/05/spUewgF39R2zQkt.png)

  * 使用范围不同
    * 过滤器实现的是javax.servlet.Filter接口，这个接口是Servlet规范中定义的，适用于以Tomcat为容器的Web应用。
    * 拦截器实现的是org.springframework.web.servlet.HandlerInterceptor接口，这个接口是Spring组件中定义的，适用于使用Spring框架的应用。

  * 触发时机不同
    * 过滤器Filter是在请求进入容器之后，在进入Servlet之前进行预处理，请求在Servlet处理完后结束。
    * 拦截器Interceptor是在进入Servlet之后，在进入Controller之前进行预处理，请求在Controller中渲染之后结束。

      ![Snipaste_2020-10-05_20-16-25.png](https://i.loli.net/2020/10/05/ui1txSqjOAcZ2Fv.png)

  * 拦截请求范围不同
    * 过滤器Filter对所有进入容器的请求起拦截作用。
    * 拦截器Interceptor只对Controller或访问static目录下的静态资源的请求起拦截作用。 

  * 注入Bean情况不同
    * 过滤器Filter中注入bean，由于SpringContext加载顺序在Filter之前，故在自定义Filter中直接使用@Autowired注入即可。
      
      ![Snipaste_2020-10-05_20-52-42.png](https://i.loli.net/2020/10/05/nCaeHKzRTlq8b6f.png)

      ![Snipaste_2020-10-05_20-59-11.png](https://i.loli.net/2020/10/05/nUXKlPh1d8TWNfO.png)

    * 拦截器Interceptor注入bean，由于拦截器注册器加载顺序在SpringContext之前，故在拦截器加载之前，需要手动注入自定义拦截器及其依赖的Bean，拦截器注册器使用手动注入的自定义拦截器。
    
      ![Snipaste_2020-10-05_20-59-49.png](https://i.loli.net/2020/10/05/mFreb6QHKMpNjho.png)

      ![Snipaste_2020-10-05_21-00-07.png](https://i.loli.net/2020/10/05/mIaG1TUjYS3kthe.png)

  * 控制执行顺序不同
    * 过滤器Filter，多个过滤器，默认根据过滤器名称顺序链式执行doFilter()方法，可使用Spring的@Order注解控制加载顺序。
    * 拦截器Interceptor，多个拦截器，先执行完所有拦截器的preHandle()方法，再执行所有拦截器的postHandle()方法，最后再执行所有拦截器的afterCompletion()方法。preHandle()方法顺序执行，postHandle()方法以及afterCompletion()方法倒序执行。

> 总结
  * 认识过滤器于拦截器的不同，在不同的场景选择最合适的技术方案。

> 参考文献
  * [过滤器 和 拦截器6个区别，别再傻傻分不清了](https://juejin.im/post/6847902221212844039)