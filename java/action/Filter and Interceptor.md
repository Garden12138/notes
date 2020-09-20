## 过滤器与拦截器

> 认识过滤器

  * 过滤器Filter，是Servlet中常用技术，通常用于对Web服务器（部署项目的容器）的资源管理，如对Servlet，静态Html文件等进行拦截，从而实现特殊功能，如实现URL级别的权限访问，敏感词过滤，压缩响应信息等一些高级功能。
  * 定义过滤器只需要实现Filter接口，并注册配置过滤器（相关描述信息：过滤器名称，拦截Url，应用Servlet）即可。传统的SSM或SSH应用中，可在web.xml文件配置过滤器的相关描述信息；SpringBoot应用中我们可使用Servlet3.0提供@WebFilter注解定义拦截器。
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

> 过滤器与拦截器的不同

> 总结