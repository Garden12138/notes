# Spring4

## 渲染Web视图-常用视图解析器

#### 理解视图解析器
* 视图解析器实现基本原理：ViewResolver接口实现解析视图名任务并返回View接口。View接口任务就是接受模型以及servlet的request和response对象，并将输出结果渲染到response中。
```
public interface ViewResolver{
  View resolverViewName(String viewName,Locale locale) throw Exception;
}
```
```
public interface View{
  String getContentType();
  void render(Map<String,?> model,HttpServletRequest request,HttpServletResponse) throw Exception;
}
```
* Spring4支持的视图解析器

| 视图解析器 | 描述 |
| -------- | ----- |
| BeanNameViewResolver | 将视图解析为Spring应用上下文的bean定义，视图名与bean id 相匹配 |
| ContentNegotiatingViewResolver | 将视图解析任务委托给另一个能够产生客户端需要的内容类型的视图解析器 |
| FreeMarkerViewResolver | 将视图解析为[FreeMark模板](http://freemarker.foofun.cn/)定义，视图名与HTML名相匹配 |
| InternalResourceViewResolver | 将视图解析为Web应用的内部资源（一般为JSP）定义，视图名与JSP名相匹配 |
| JasperReportsViewResolver | 将视图解析为[JasperReports](https://www.yiibai.com/jasper_reports/)定义 ,视图名与报表视图配置上的bean id 相匹配|
| ResourceBundleViewResolver | 将视图解析为ResourceBundle定义，通过属性文件解析视图，视图名与JSP名相匹配 |
| TilesViewResolver | 将视图解析为Tiles定义，视图名与tile id 相匹配 |
| UrlBasedViewResolver | 将视图解析为物理路径的视图定义 （一般为静态页面），视图名与物理路径视图名相匹配 |
| VelocityLayoutViewResolver | 将视图解析为[Velocity布局](https://www.oschina.net/question/12_4580)定义，从不同的Velocity模板中组合页面 |
| VelocityViewResolver | 将视图解析为Velocity模板定义，已被Velocity布局代替 |
| XmlViewResolver | 将视图解析为XML里的bean定义，视图名与bean id 相匹配 |
| XsltViewResolver | 将视图解析为[XSLT](http://www.codejava.net/frameworks/spring/spring-mvc-xstlview-and-xsltviewresolver-example)转换后的结果定义 |
| ThymeleafViewResolver | 将视图解析为Thymeleaf定义，视图名与HTML名相匹配 |

#### 常用视图解析器

* InternalResourceViewResolver:
  * 配置：
  ```
  //JavaConfig
  @Bean
  public ViewResolver viewResolver(){    /*配置JSP视图解析器*/
    InternalResourceViewResolver resolver = new InternalResourceViewResolver();
  	resolver.setPrefix("/WEB-INF/jsp/");
  	resolver.setSuffix(".jsp");
  	resolver.setExposeContextBeansAsAttributes(true);
  	resolver.setViewClass(org.springframework.web.servlet
      .view.JstlView.class);    /*设置返回View为JSTLView*/
      return resolver;
    }
  ```
  ```
  <!-- XML -->
  <bean id="viewResolver" class="org.springframework.web.servlet.view.InternalResourceViewResolver" p:prefix="/WEB-INF/jsp/" p:suffix=".jsp" />
  ```
  * 解析过程：视图解析器将逻辑视图名称与设定前后缀拼接成web内部资源路径，从该路径返回视图，最后DispatcherServlet将模型传至视图进行渲染。
  * 渲染技术：渲染，即逻辑结构化与数据访问页面，JSP一般使用[JSTL](http://www.runoob.com/jsp/jsp-jstl.html)+JSP标签库（表单绑定标签库+通用标签库）|[EL表达式](https://blog.csdn.net/goskalrie/article/details/51315397)
    * 表单绑定标签库：绑定模型，取模型属性填充标签值（value）
      * 标签：
      [![20180330203951.png](https://i.loli.net/2018/03/30/5abe304440832.png)](https://i.loli.net/2018/03/30/5abe304440832.png)
      * 适用场景：表单提交
      ```
      视图（JSP）
      ```
      ```
      <%@ page language="java" contentType="text/html; charset=utf-8" pageEncoding="utf-8"%>
      <%@ taglib uri="http://www.springframework.org/tags/form" prefix="sf" %>
      <%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
      <html>
      <body>
          <h2>表单绑定标签库</h2>
          <c:if test="${params!=null}">
          <sf:form action="http://192.168.23.5:8080/Spring/home/getFormParamsByFormBindTagRespo" method="POST" commandName="params">
              id:<sf:input path="id"/></br>
              message:<sf:input path="message"/></br>
              time:<sf:input path="time"/></br>
              <input type="submit" value="commit" />
          </sf:form>
          </c:if>
      </body>
      </html>
      ```
      ```
      控制器
      ```
      ```
      @RequestMapping(value={"/showFormbindtagRespo"},method=RequestMethod.GET)
      public String showFormBindTagRespoPage(Map model){
        model.put("params", new Data("","",""));
        return "formbindtagrespo";
      }
      @RequestMapping(value={"/getFormParamsByFormBindTagRespo"},method=RequestMethod.POST)
      public String getFormParamsByFormBindTagRespo(Map model,@Valid Data data,Errors errors){
        System.out.println(errors.hasErrors());
        if(errors.hasErrors()){
          System.out.print("----------");
          return "index";
        }
        model.put("params",data);
        return "formbindtagrespo";
      }
      ```
    * 通用标签库
      * 标签：
      [![20180330214049.png](https://i.loli.net/2018/03/30/5abe3e75b2a71.png)](https://i.loli.net/2018/03/30/5abe3e75b2a71.png)
      * 适用场景：
        * 国际化信息：使用标签<s:message>
        ```
        配置国际化信息源
        WebConfig.java
        ```
        ```
        @Bean
        public MessageSource messageSource(){    /*国际化信息配置*/
          ReloadableResourceBundleMessageSource messageSource =
          new ReloadableResourceBundleMessageSource();
          messageSource.setBasename("classpath:/language");  /*属性文件基本名称，如language_zh.properties*/
          messageSource.setCacheSeconds(10);
          return messageSource;
        }
        ```
        ```
        国际化信息属性文件
        language_zh.properties
        ```
        ```
        spring4.username=\u7528\u6237\u540D
        ```
        ```
        视图（JSP）
        ```
        ```
        <%@ page language="java" contentType="text/html; charset=utf-8" pageEncoding="utf-8"%>
        <%@ taglib uri="http://www.springframework.org/tags" prefix="s" %>
        <%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <h2>通用标签库</h2>
            <h3>国际化信息应用</h3>
            <s:message code="spring4.username"/>
        </body>
        </html>
        ```
        * 创建URL:使用标签<s:url>，任务是创建URL，赋值到变量或直接渲染到响应中。
        ```
        视图（JSP）
        ```
        ```
        <%@ page language="java" contentType="text/html; charset=utf-8" pageEncoding="utf-8"%>
        <%@ taglib uri="http://www.springframework.org/tags" prefix="s" %>
        <%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
        <h2>通用标签库</h2>
        <h3>创建URL应用</h3>
            <a href="<s:url value="/home/show" />">直接渲染响应跳转至home.jsp</a></br>
            <s:url value="/home/show" var="jumpHome"/>
            <a href="${jumpHome}">先赋值变量再渲染响应跳转至home.jsp</a></br>
            <s:url value="/home/getQueryParams" var="jumpHomeByQueryParams">
                <s:param name="max" value="10" />
                <s:param name="count" value="10" />
            </s:url>
            <a href="${jumpHomeByQueryParams}">通过查询参数跳转值home.jsp</a></br>
            <s:url value="/home/getPathParams/{max}/{count}" var="jumpHomeByPathParams">
                <s:param name="max" value="11" />
                <s:param name="count" value="11" />
            </s:url>
            <a href="${jumpHomeByPathParams}">通过路径参数跳转值home.jsp</a></br>
            <span>将URL转义成html字符串输出<s:url value="/home/getFormParams" htmlEscape="true" /></span></br>
        </body>
        </html>
        ```
        * 转义内容:使用标签<s:escapebody>，包含内容即转义，属性htmlEscape转义成html字符输出，javaScriptEscape转义成js字符输出
        ```
        <%@ page language="java" contentType="text/html; charset=utf-8" pageEncoding="utf-8"%>
        <%@ taglib uri="http://www.springframework.org/tags" prefix="s" %>
        <%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <s:url value="/home/getFormParams" javaScriptEscape="true" var="jsEscape"/>
            <button id="jsEscapeBtn" type="submit" onclick="show()">将URL转义成js字符串弹框输出</button></br>
        <script type="text/javascript">
            function show(){
              var jsEscape = "${jsEscape}";
              alert("${jsEscape}");
            }
        </script>
        <h3>转义内容应用</h3>
        <s:escapeBody htmlEscape="true">
        <span>将URL转义成html字符串输出</span>
        </s:escapeBody></br>
        <s:escapeBody javaScriptEscape="true">
            <span>将URL转义成js字符串弹框输出</span>
        </s:escapeBody>
        </body>
        </html>
        ```

* TilesViewResolver:
  * 配置：
  ```
  //JavaConfig
  @Bean
  public ViewResolver viewResolver(){    /*配置Tiles视图解析器*/
    return new TilesViewResolver();
  }
  @Bean
  public TilesConfigurer tilesConfigurer(){    /*配置解析tiles定义*/
    TilesConfigurer tiles = new TilesConfigurer();
    tiles.setDefinitions(new String[]{"WEB-INF/layout/tiles.xml"});
    tiles.setCheckRefresh(true);
    return tiles;
  }
  ```
  ```
  <!-- XML -->
  <bean id="viewResolver" class=
      "org.springframework.web.servlet.view.tiles3.TilesViewResolver" />
  <bean id="tilesConfigurer" class=
    "org.springframework.web.servlet.view.tiles3.TilesConfigurer">
      <property name="definitions">
          <list>
              <value>/WEB-INF/layout/tiles.xml.xml</value>
          </list>
      </property>
  </bean>
  ```
  ```
  定义Tiles
  ```
  ```
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE tiles-definitions PUBLIC
          "-//Apache Software Foundation//DTD Tiles Configuration 3.0//EN"
          "http://tiles.apache.org/dtds/tiles-config_3_0.dtd">
  <tiles-definitions>
      <definition name="home" template="/WEB-INF/jsp/page.jsp">
          <put-attribute name="header" value="/WEB-INF/jsp/header.jsp" />
          <put-attribute name="body" value="/WEB-INF/jsp/home.jsp"/>
          <put-attribute name="footer" value="/WEB-INF/jsp/footer.jsp"/>
      </definition>
  </tiles-definitions>
  ```
  * 解析过程：视图解析器将逻辑视图名称与所有tiles定义文件中的definition的name相匹配，返回相应的视图模板，最后DispatcherServlet将模型传至视图模板进行渲染。
  * 渲染技术：使用标签<t>将多个模板组合成一个视图（可做模板，可使用extends属性扩展模板）
  ```
  <%@ page language="java" contentType="text/html; charset=utf-8"
    pageEncoding="utf-8"%>
  <%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
  <%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="t"%>
  <html>
  <body>
      <h2>Hello World! -- page.jsp</h2>
      <div><t:insertAttribute name="header"/></div>
      <div><t:insertAttribute name="body"/></div>
      <div><t:insertAttribute name="footer"/></div>
  </body>
  </html>
  ```
* ThymeleafViewResolver:
  * 配置：
  ```
  //JavaConfig
  @Bean
  public ViewResolver viewResolver(
    SpringTemplateEngine templateEngine) {    /*配置Thymeleaf视图解析器*/
      ThymeleafViewResolver viewResolver = new ThymeleafViewResolver();
      viewResolver.setTemplateEngine(templateEngine);
      viewResolver.setCharacterEncoding("utf-8");
      return viewResolver;
    }
  @Bean
  public SpringTemplateEngine templateEngine(
    TemplateResolver templateResolver) {    /*配置模板引擎*/
      SpringTemplateEngine templateEngine = new SpringTemplateEngine();
      templateEngine.setTemplateResolver(templateResolver);
      return templateEngine;
    }
  @Bean
  public TemplateResolver templateResolver() {    /*配置模板解析器*/
    TemplateResolver templateResolver = new ServletContextTemplateResolver();
    templateResolver.setPrefix("/WEB-INF/html/");
    templateResolver.setSuffix(".html");
    templateResolver.setTemplateMode("HTML5");
    templateResolver.setCharacterEncoding("utf-8");
    return templateResolver;
  }
  ```
  ```
  <!-- XML -->
  <bean id="viewResolver"
      class="org.thymeleaf.spring3.view.ThymeleafViewResolver"
      p:templateEngine-ref="templateEngine"
      p:characterEncoding="UTF-8"/>
  <bean id="templateEngine"
      class="org.thymeleaf.spring3.SpringTemplateEngine"
      p:templateResolver-ref="templateResolver" />
  <bean id="templateResolver"
      class="org.thymeleaf.templateresolver.ServletContextTemplateResolver"
      p:prefix="/WEB-INF/html/"
      p:suffix=".html"
      p:templateMode="HTML5" />
  ```
  * 解析过程：视图解析器将逻辑视图名称与设定前后缀拼接成web内部资源路径，从该路径返回视图，最后DispatcherServlet将模型传至视图进行渲染（启动模板引擎使用模板解析器解析）。
  * 渲染：
  ```
  <html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:th="http://www.thymeleaf.org">
  <head>
  <title>Thymeleaf应用</title>
  </head>
  <body>
      <h1>Thymeleaf应用</h1>
      <a th:href="@{/home/showTestPage}" >跳转至测试页面</a>
      <form th:action="@{/home/getFormParams}" method="POST" th:object="${params}">
             id:<input type="text" th:field="*{id}" /><br/>
             message:<input type="text" th:field="*{message}"  /><br/>
             time:<input type="text" th:field="*{time}"  /><br/>
             <input type="submit" value="commit" />
      </form>
  </body>
  </html>
  ```
  * Jsp与Thymeleaf区别
    * Jsp并不是真正的HTML，Jsp标签库的使用造成HTML代码污染，而Thymeleaf支持原生HTML元素，使用命名空间方式加以支持。
    * Jsp依赖Servlet，而Thymeleaf能够独立于Servlet使用。
    * 使用[Thymeleaf](https://www.thymeleaf.org/index.html)需要学习[Sring方言](https://blog.csdn.net/zrk1000/article/details/72667478)。
