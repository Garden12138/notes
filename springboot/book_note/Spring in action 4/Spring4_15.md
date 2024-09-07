# Spring4
## Spring集成远程服务

#### 了解远程服务
* 远程调用：是客户端应用和服务端之间的会话。
[![远程调用.png](https://i.loli.net/2018/05/18/5afee70b15d25.png)](https://i.loli.net/2018/05/18/5afee70b15d25.png)
* 远程过程调用（remote procedure call）：RPC调用是执行流从一个应用传递给另一个应用，理论上另一个应用部署在跨网络的一台远程机器上。
* Spring通过多次远程调用技术支持RPC
```
RPC模型            适用场景
RMI                不考虑网络限制（防火墙），发布/访问基于Java服务
Hessian|Burlap     考虑网络限制（防火墙），通过HTTP发布/访问基于Java等服务（PHP，Python）。Hessian基于二进制，Burlap基于XML
Http Invoker       考虑网络限制（防火墙），并希望使用基于XML或专有的序列化机制实现Java序列化时，发布/访问基于Spring的服务
JAX-RPC|JAX-WS     发布/访问平台独立的，基于SOAP的WEB服务
```
  * 工作原理：

  [![Spring将服务装配至客户端应用.png](https://i.loli.net/2018/05/19/5afff0aaae476.png)](https://i.loli.net/2018/05/19/5afff0aaae476.png)

  [![Spring将管理的Bean发布为远程服务.png](https://i.loli.net/2018/05/19/5afff21d696e1.png)](https://i.loli.net/2018/05/19/5afff21d696e1.png)

#### 发布和访问RMI服务（Spring配置）
* 服务端发布RMI服务
  * 原理：

  [![服务端发布RMI服务.png](https://i.loli.net/2018/05/19/5b001c23e9083.png)](https://i.loli.net/2018/05/19/5b001c23e9083.png)

  * 配置：
  ```
  //配置RMI服务导出器
  @Bean
  public RmiServiceExporter spitterServiceExporter(SpitterService spitterService){
    RmiServiceExporter rmiServiceExporter = new RmiServiceExporter();
    rmiServiceExporter.setService(spitterService);/*注入具体服务Bean*/
    rmiServiceExporter.setServiceName("SpitterService");/*设置服务名称*/
    rmiServiceExporter.setServiceInterface(SpitterService.class);/*设置服务接口*/
    rmiServiceExporter.setRegistryHost("rmi.spitter.com");/*设置服务注册表Host*/
    rmiServiceExporter.setRegistryPort("1199");/*设置服务注册表端口号*/
    return rmiServiceExporter;
  }
  ```

* 客户端访问RMI服务
  * 原理：

  [![客户端访问RMI服务.png](https://i.loli.net/2018/05/20/5b010af711206.png)](https://i.loli.net/2018/05/20/5b010af711206.png)

  * 配置:
  ```
  //配置RMI服务代理
  @Bean
  public RmiProxyFactoryBean spitterService(){
    RmiProxyFactoryBean rmiProxy = new RmiProxyFactoryBean();
    rmiProxy.setServiceUrl("rmi://localhost/SpitterService");/*设置服务URL*/
    rmiProxy.setServiceInterface(SpitterService.class);/*设置服务接口（与服务端一致）*/
    return rmiProxy;
  }
  ```
  ```
  //注入服务
  @Autowired
  private SpitterService SpitterService;
  ```

#### 发布和访问Hessian和Burlap服务
* 服务端发布Hessian服务
  * 原理：

  [![服务端发布Hessian-Burlap服务.png](https://i.loli.net/2018/05/20/5b0129eaa6d9a.png)](https://i.loli.net/2018/05/20/5b0129eaa6d9a.png)

  * 配置
  ```
  //配置Hessian服务导出器
  @Bean
  public HessianServiceExporter spitterServiceExporter(SpitterService spitterService){
    HessianServiceExporter hessianServiceExporter = new HessianServiceExporter();
    hessianServiceExporter.setService(spitterService);
    hessianServiceExporter.setServiceInterface(SpitterService.class);
    return hessianServiceExporter;
  }
  ```
  ```
  //配置DispatcherServlet
  //web.xml配置
  <servlet-mapping>
      <servlet-name>spitter</servlet-name>
      <url-pattern>/</url-pattern>
      <url-pattern>*.service</url-pattern>
  </servlet-mapping>
  //实现WebApplicationInitializer配置
  ServletRegistration.Dynamic dispatcher = container.addServlet("appServlet",new DispatcherServlet(dispatcherServletContext));
  dispatcher.setLoadOnStartup(1);
  dispatcher.addMapping("/");
  dispatcher.addMapping("*.service");
  //扩展AbstractDispatcherServletInitializer|AbstractAnnotationConfigDispatcherServletInitializer配置
  @Override
  protected String[] getServletMappings(){
    return new String[]{"/","*.service"};
  }
  ```
  ```
  //配置URL处理器，将请求转发至相应服务
  @Bean
  public HandlerMapping hessianServiceHandlerMapping(){
    SimmpleUrlHandlerMapping mapping = new SimmpleUrlHandlerMapping();
    Properties mappings = new Properties();
    mappings.setProperty("/spitter.service","spitterServiceExporter");
    mapping.setMappings(mappings);
    return mapping;
  }
  ```
* 客户端访问Hessian服务
  * 原理：

  [![客户端访问Hessian-Burlap服务.png](https://i.loli.net/2018/05/20/5b0129516c075.png)](https://i.loli.net/2018/05/20/5b0129516c075.png)

  * 配置：
  ```
  //配置Hessian服务代理
  @Bean
  public HessianProxyFactoryBean spitterService(){
    HessianProxyFactoryBean hessianProxy = new HessianProxyFactoryBean();
    hessianProxy.setServiceUrl("http://localhost:8080/Spitter/spitter.service");
    hessianProxy.setServiceInterface(SpitterService.class);
    return hessianProxy;
  }
  ```
* 服务端发布Burlap服务
  * 原理：与上述服务端发布Hessian服务原理一致
  * 配置：除服务导出器之外，其他配置与上述服务端发布Hessian服务配置一致
  ```
  //配置Burlap服务导出器
  @Bean
  public BurlapServiceExporter spitterServiceExporter(SpitterService spitterService){
    BurlapServiceExporter burlapServiceExporter = new BurlapServiceExporter();
    burlapServiceExporter.setService(spitterService);
    burlapServiceExporter.setServiceInterface(SpitterService.class);
    return burlapServiceExporter;
  }
  ```
* 客户端访问Burlap服务
  * 原理：与上述客户端访问Hessian服务原理一致
  * 配置：
  ```
  //配置Burlap服务代理
  @Bean
  public BurlapProxyFactoryBean spitterService(){
    BurlapProxyFactoryBean burlapProxy = new BurlapProxyFactoryBean();
    burlapProxy.setServiceUrl("http://localhost:8080/Spitter/spitter.service");
    burlapProxy.setServiceInterface(SpitterService.class);
    return burlapProxy;
  }
  ```

#### 发布和访问Spring HttpInvoker服务
* 服务端发布HttpInvoker服务
  * 原理：与上述服务端发布Hessian服务原理一致
  * 配置：除服务导出器之外，其他配置与上述服务端发布Hessian服务配置一致
  ```
  //配置HttpInvoker服务导出器
  @Bean
  public HttpInvokerServiceExporter spitterServiceExporter(SpitterService spitterService){
    HttpInvokerServiceExporter httpInvokerServiceExporter = new HttpInvokerServiceExporter();
    httpInvokerServiceExporter.setService(spitterService);
    httpInvokerServiceExporter.setServiceInterface(SpitterService.class);
    return httpInvokerServiceExporter;
  }
  ```
* 客户端访问HttpInvoker服务
  * 原理：与上述客户端访问Hessian服务原理一致
  * 配置：
  ```
  //配置HttpInvoker服务代理
  @Bean
  public HttpInvokerProxyFactoryBean spitterService(){
    HttpInvokerProxyFactoryBean httpInvokerProxy = new HttpInvokerProxyFactoryBean();
    httpInvokerProxy.setServiceUrl("http://localhost:8080/Spitter/spitter.service");
    httpInvokerProxy.setServiceInterface(SpitterService.class);
    return httpInvokerProxy;
  }
  ```

#### 发布和访问Web服务
* 服务端发布Web服务
  * 原理：由服务导出器发布服务，使用注解声明JAX-WS端点（注入了服务接口的类）
  * 配置：
  ```
  //配置JAX-WS服务导出器
  @Bean
  public SimpleJaxWsServiceExporter spitterServiceExporter(SpitterService spitterService){
    SimpleJaxWsServiceExporter simpleJaxWsServiceExporter = new SimpleJaxWsServiceExporter();
    simpleJaxWsServiceExporter.setBaseAddress("http://localhost:8888/services/");
    return simpleJaxWsServiceExporter;
  }
  ```
  ```
  //配置JAX-WS端点
  @Component
  @WebService(serviceName="SpitterService")
  public clas SpitterServiceEndpoint{
    @Autowired
    private SpitterService spitterService;/*自动装配SpitterService*/
    @WebMethod
    public void addSpittle(Spittle spittle){
      spitterService.saveSpittle(spittle);/*委托给SpitterService*/
    }
  }
  ```
* 客户端访问Web服务
  * 原理：与上述客户端访问Hessian服务原理一致
  * 配置：
  ```
  //配置Web服务代理
  @Bean
  public JaxWsProxyFactoryBean spitterService(){
    JaxWsProxyFactoryBean JaxWsProxy = new JaxWsProxyFactoryBean();
    JaxWsProxy.setWsdlDocument("http://localhost:8080/services/SpitterService.wsdl");/*标识远程Web服务定义文件位置*/
    JaxWsProxy.setServiceName("SpitterService");/*标识远程Web服务定义文件的指定服务名称*/
    JaxWsProxy.setPortName("SpitterServiceHttpPort");/*标识远程Web服务定义文件的指定端口名称*/
    JaxWsProxy.setServiceInterface(SpitterService.class);
    JaxWsProxy.setNamespaceUri("http://spitter.com");/*标识远程Web服务定义文件的指定命名空间*/
    return JaxWsProxy;
  }
  ```
  ```
  <!-- 远程Web服务定义文件wsdl -->
  <wsdl:definitions targetNamespace="http://spitter.com">
  ...
      <wsdl:service name="SpitterService">
           <wsdl:port name="SpitterServiceHttpPort" binding="tns:spitterServiceHttpBinding">
           ...
      </wsdl:service>
  </wsdl:definitions>
  ```
