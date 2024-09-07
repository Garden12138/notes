# Spring4

## 构建Spring Web应用程序

#### 了解Spring的SpringMVC框架

* 跟踪Spring MVC的请求：Spring将请求在调度Servlet，处理器映射，控制器以及视图解析器之间移动。
[![05fig01.jpg](https://i.loli.net/2018/03/26/5ab852f0cb58d.jpg)](https://i.loli.net/2018/03/26/5ab852f0cb58d.jpg)
  * DispatcherServlet：前端控制器，是一个单例的调度Servlet。任务是接收用户请求并将请求发送至相应的控制器（发送请求至控制器前先进入HandlerMapping确认具体控制器）。
  * HandlerMapping：处理器映射，任务是根据请求所携带的URL信息进行决策，确认具体的控制器。
  * Controller：控制器，处理请求信息（请求到达控制器后会卸下信息并等待控制器返回信息），完成业务逻辑（实际业务逻辑委托给服务对象处理），返回信息（即模型model，由请求携带）和视图名称（veiwname）至DispatcherServlet。
  * ViewResolver：视图解析器，将视图名匹配为一个特定的视图实现（即存放视图的web路径）。
  * View：视图，将模型渲染入视图并通过响应返回用户。

#### 搭建SpringMVC框架

* 配置DispatcherServlet
  * web.xml配置
  ```
  <!-- 通过ContextLoaderListener加载应用程序servlet上下文 -->
  <context-param>
      <param-name>contextConfigLocation</param-name>
      <param-value>classpath:SpringDataSource.xml,classpath:config.xml</param-value>
  </context-param>
  <listener>
    <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
  </listener>
  <!-- 通过DispatcherServlet，加载Spring应用上下文 -->
  <servlet>
      <servlet-name>springMVC</servlet-name>
      <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
      <init-param>
          <param-name>contextConfigLocation</param-name>
          <param-value>classpath:SpringMVC.xml,classpath:config.xml</param-value>
      </init-param>
      <load-on-startup>1</load-on-startup>
  </servlet>
  <servlet-mapping>
      <servlet-name>springMVC</servlet-name>
      <url-pattern>/</url-pattern>
  </servlet-mapping>
  ```
  * JavaConfig配置
  ```
  package com.web.spring4.config;
  import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;
  public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer{
    /*加载ContextLoaderListener 数据层组件（bean，数据源等）*/
    @Override
    protected Class<?>[] getRootConfigClasses() {
      // TODO Auto-generated method stub
      return new Class<?>[] {RootConfig.class};
    }
    /*加载DispatcherServlet web组件（bean，映射处理器，控制器，视图解析器）*/
    @Override
    protected Class<?>[] getServletConfigClasses() {
      // TODO Auto-generated method stub
      return new Class<?>[] {WebConfig.class};
    }
    /*将DispatcherServlet映射到'/'*/
    @Override
    protected String[] getServletMappings() {
      // TODO Auto-generated method stub
      return new String[] {"/"};
    }
  }
  ```
  * PS
    * AbstractAnnotationConfigDispatcherServletInitializer的任意扩展类会自动配置DispatcherServlet和Spring应用上下文，Spring应用上下文位于应用程序的Servlet上下文之中。
    * getServletConfigClasses()方法返回带有@Configuration注解的类将来定义DispatcherServlet应用上下文的bean，getRootConfigClasses()方法返回带有@Configuration注解的类将来定义ContextLoaderListener应用上下文的bean。

* 启用SpringMVC
  * XML配置
  ```
  <?xml version="1.0" encoding="UTF-8"?>
  <beans xmlns="http://www.springframework.org/schema/beans"
         xmlns:context="http://www.springframework.org/schema/context" xmlns:p="http://www.springframework.org/schema/p"
         xmlns:mvc="http://www.springframework.org/schema/mvc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:tx="http://www.springframework.org/schema/tx" xmlns:task="http://www.springframework.org/schema/task"
         xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd  
         http://www.springframework.org/schema/context  
         http://www.springframework.org/schema/context/spring-context.xsd  
         http://www.springframework.org/schema/mvc  
         http://www.springframework.org/schema/mvc/spring-mvc-3.2.xsd
         http://www.springframework.org/schema/tx
         http://www.springframework.org/schema/tx/spring-tx-3.2.xsd
         http://www.springframework.org/schema/task
         http://www.springframework.org/schema/task/spring-task-3.2.xsd">
         <!-- 扫描业务逻辑包 -->
         <context:component-scan base-package="com.web.controller" />
         <!-- 静态资源配置 -->
         <mvc:resources location="/res/"  mapping="/res/**"  cache-period="31536000" />
         <!-- 配置Viewer-->
         <bean id="viewResolver" class="org.springframework.web.servlet.view.InternalResourceViewResolver">
             <property name="prefix" value="/jsp/"></property>
             <property name="suffix" value=".jsp"></property>
         </bean>
         <!-- 配置SpringMvc注解，启动SpringMvc -->
         <mvc:annotation-driven />
  </beans>
  ```

  * JavaConfig配置
  ```
  package com.web.spring4.config;
  import org.springframework.context.annotation.Bean;
  import org.springframework.context.annotation.ComponentScan;
  import org.springframework.context.annotation.Configuration;
  import org.springframework.context.annotation.Import;
  import org.springframework.web.servlet.ViewResolver;
  import org.springframework.web.servlet.config.annotation.DefaultServletHandlerConfigurer;
  import org.springframework.web.servlet.config.annotation.EnableWebMvc;
  import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
  import org.springframework.web.servlet.view.InternalResourceViewResolver;
  @Configuration
  @EnableWebMvc    /*启用Spring MVC*/
  @Import(ControllerConfig.class)    /*启动组件扫描，主要扫描控制器以及其他组件*/
  public class WebConfig extends WebMvcConfigurerAdapter{    /*继承抽象类，实现配置默认servlet拦截方法*/
    @Bean
    public ViewResolver viewResolver(){    /*配置JSP视图解析器*/
      InternalResourceViewResolver resolver = new InternalResourceViewResolver();
      resolver.setPrefix("/WEB-INF/jsp/");
      resolver.setSuffix(".jsp");
      resolver.setExposeContextBeansAsAttributes(true);
      return resolver;
    }
    @Override
    public void configureDefaultServletHandling(
      DefaultServletHandlerConfigurer configurer) {    /*配置静态资源的处理，将静态资源的请求转移至默认servlet*/
      configurer.enable();
    }
  }
  ```
  * PS：
    * @Controller注解里使用了@Component注解，故组件扫描@Controller注解的类时会创建候选的bean。

* 搭建控制器
  * 编写控制器：
    * 使用@Controller声明控制器，@RequestMapping声明请求，包括请求url（value属性），请求方式（method属性），返回类型（如，produces = "application/json;charset=UTF-8"表明返回json格式数据）。
    * 模型数据可以用Map，Model，request存放，最终由request携带。
    * 接收的参数：接收的参数类型均为String。查询参数可以使用@RequestParam；路径参数可以使用@PathVariable；表单参数可以使用封装的对象接收参数。
  ```
  package com.web.spring4.controller;
  import java.util.ArrayList;
  import java.util.Date;
  import java.util.List;
  import java.util.Map;
  import javax.servlet.http.HttpServletRequest;
  import javax.validation.Valid;
  import org.springframework.beans.factory.annotation.Autowired;
  import org.springframework.stereotype.Controller;
  import org.springframework.ui.Model;
  import org.springframework.validation.Errors;
  import org.springframework.web.bind.annotation.PathVariable;
  import org.springframework.web.bind.annotation.RequestBody;
  import org.springframework.web.bind.annotation.RequestMapping;
  import org.springframework.web.bind.annotation.RequestMethod;
  import org.springframework.web.bind.annotation.RequestParam;
  import com.web.spring4.pojo.Data;
  import com.web.spring4.repository.DataRepository;
  @Controller
  @RequestMapping(value={"/home"})
  public class HomeController {
    private DataRepository dataRepository;
    public DataRepository getDataRepository() {
      return dataRepository;
    }
    public void setDataRepository(DataRepository dataRepository) {
      this.dataRepository = dataRepository;
    }
    @RequestMapping(value={"/show"},method=RequestMethod.GET)
    public String showHomePage(){
      return "home";
    }
	  @RequestMapping(value={"/load"},method=RequestMethod.GET)
	  public String loadHomePage(Map model,Model res,HttpServletRequest request){
      //model.put("data", dataRepository.findData(Long.MAX_VALUE, 20));
      List<Data> expectData = new ArrayList<Data>();
		  for(long i = 0; i < 20; i++){
        expectData.add(new Data(String.valueOf(i),"data"+i,String.valueOf(new Date())));
      }
      //model.put("data", expectData);
		  //res.addAttribute("data", expectData);
      request.setAttribute("data", expectData); //模型
      //request.getSession().setAttribute("data", expectData);
      return "home";                            //视图名
    }
    @RequestMapping(value={"/getQueryParams"},method=RequestMethod.GET)
    public String getQueryParams(Map model,@RequestParam(value="max",defaultValue="20") long max,
			@RequestParam(value="count",defaultValue="20") int count){
        model.put("params","max="+max+"&"+"count="+count);
        return "home";
    }
    @RequestMapping(value={"/getPathParams/{max}/{count}"},method=RequestMethod.GET)
    public String getPathParams(Map model,@PathVariable long max,@PathVariable int count){
      model.put("params","max="+max+"&"+"count="+count);
		  return "home";
    }
	  @RequestMapping(value={"/getFormParams"},method=RequestMethod.POST)
	  public String getFormParams(Map model,@Valid Data data,Errors errors){
      System.out.println(errors.hasErrors());
      if(errors.hasErrors()){
        System.out.print("----------");
        return "index";
      }
      model.put("params",data);
      return "home";
    }
  }
  ```
  * 编写Mock测试
  ```
  package com.web.spring4.test;
  import static org.junit.Assert.*;
  import org.junit.Test;
  import org.junit.runner.RunWith;
  import com.web.spring4.config.ControllerConfig;
  import com.web.spring4.config.WebAppInitializer;
  import com.web.spring4.controller.HomeController;
  import com.web.spring4.pojo.Data;
  import com.web.spring4.repository.DataRepository;
  import org.springframework.beans.factory.annotation.Autowired;
  import org.springframework.test.context.ContextConfiguration;
  import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
  import org.springframework.test.web.servlet.MockMvc;
  import org.springframework.web.servlet.view.InternalResourceView;
  import static
       org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
  import static
       org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
  import static
       org.springframework.test.web.servlet.setup.MockMvcBuilders.*;
  import static org.hamcrest.Matchers.*;
  import static org.mockito.Mockito.*;
  import java.util.ArrayList;
  import java.util.Date;
  import java.util.List;
  @RunWith(SpringJUnit4ClassRunner.class)
  @ContextConfiguration(classes={WebAppInitializer.class,ControllerConfig.class})
  public class ControllerMockTest {
    @Autowired
	  HomeController hc;
	  @Test
	  public void homeControllerShowTest()  {
      System.out.println("homeControllerShowTest...");
		  MockMvc mockMvc = standaloneSetup(hc).setSingleView(
        new InternalResourceView("/WEB-INF/jsp/home.jsp")).build();
      try {
        mockMvc.perform(get("/home/show")).andExpect(view().name("home"));
      } catch (Throwable e) {
        // TODO Auto-generated catch block
			  System.out.println("failed..");
			  e.printStackTrace();
			  return;
      }
		  System.out.println("success");
    }
	  @Test
	  public void homeControllerLoadTest()  {
      System.out.println("homeControllerLoadTest...");
		  List<Data> expectData = new ArrayList<Data>();
		  for(long i = 0; i < 20; i++){
        expectData.add(new Data(String.valueOf(i),"data"+i,String.valueOf(new Date())));
      }
      DataRepository dataRepository = mock(DataRepository.class);
		  when(dataRepository.findData(Long.MAX_VALUE, 20)).thenReturn(expectData);
      hc.setDataRepository(dataRepository);
		  MockMvc mockMvc = standaloneSetup(hc).build();
      try {
        mockMvc.perform(get("/home/load"))
			       .andExpect(view().name("home"))
			       .andExpect(model().attributeExists("data"))
			       .andExpect(model().attribute("data", hasItems(expectData.toArray())));
		  } catch (Throwable e) {
        // TODO Auto-generated catch block
			  System.out.println("failed..");
			  e.printStackTrace();
			  return;
      }
      System.out.println("success");
    }
  }
  ```
