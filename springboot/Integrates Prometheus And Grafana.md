## 集成 Prometheus 以及 Grafana

> 前期准备

* [```SpringBoot``` 集成 ```Actuator```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Actuator.md)

* [部署 ```Prometheus Server```](https://gitee.com/FSDGarden/learn-note/blob/master/prometheus/Use%20docker%20deploy%20prometheus%20server.md)

* [部署 ```Grafana```](https://gitee.com/FSDGarden/learn-note/blob/master/grafana/Use%20docker%20deploy%20grafana.md)

* [部署 ```Altermanger```](https://gitee.com/FSDGarden/learn-note/blob/master/altermanager/Use%20docker%20deploy%20altermanager.md)

> SpringBoot 集成 Prometheus
  
  * 添加 ```micrometer prometheus registry```依赖：
    
    ```bash
    <dependency>
        <groupId>io.micrometer</groupId>
        <artifactId>micrometer-registry-prometheus</artifactId>
    </dependency>
    ```

> Prometheus Server 注册 SpringBoot Server
  
  * 编辑```Prometheus Server```的配置文件```/data/prometheus/prometheus.yml```，添加```SpringBoot Server```作业配置如```consumer```：
    
    ```bash
    # A scrape configuration containing exactly one endpoint to scrape:
    # Here it's Prometheus itself.
    scrape_configs:
      # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
      - job_name: "prometheus"

        # metrics_path defaults to '/metrics'
        # scheme defaults to 'http'.

        static_configs:
          - targets: ["localhost:9090"]

      # demo job like consumer
      -  job_name: 'consumer' # 作业名称
         metrics_path: '/exporter/prometheus' # 指标获取路径
         scrape_interval: 5s # 时间间隔
         basic_auth: # Spring Security basic auth 
           username: ${ss.username} # Spring Security basic auth username
           password: ${ss.password} # Spring Security basic auth password 
         static_configs:
           - targets: ['host.docker.internal:8763'] # 应用实例的地址，默认的协议是http，docker容器访问宿主机使用host.docker.internal域名
    ```

  * 配置文件保存更新后，执行```curl -X POST http://${ip}:9090/-/reload```热更新```Prometheus Server```。

> Grafana 连接 Prometheus Server

  * 登录```Grafana```可访问地址```http://${ip}:3000/dashboards```，初始账号密码为```admin/admin```，首次登录成功后会要求更新密码。

  * 点击菜单```Toggle menu -> Connections -> DataSouce -> Add new data Souce```，搜索选择```Prometheus```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_14-45-19.png)

> 实践

* 创建监控 ```Grafana Dashboard```：
  
  * 登录```Grafana```可访问地址```http://${ip}:3000/dashboards```，点击菜单```Toggle menu -> Dashboards -> New dashboard -> Add visualization```，选择```Prometheus```数据源。

  * 添加查询语句：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_14-45-40.png)

* 引入监控 ```Grafana Dashboard```市场

  * ```Dashboard```市场存在开箱即用、通用型的```Dashboard```模版。目前比较常用的有[```JVM (Micrometer)```](https://grafana.com/grafana/dashboards/4701-jvm-micrometer/)以及[```Spring Boot Statistics```](https://grafana.com/grafana/dashboards/6756-spring-boot-statistics/)。以```JVM (Micrometer)```为例，导入步骤如下：
    
    进入[```Grafana Dashboard市场```](https://grafana.com/grafana/dashboards/)，输入关键词搜索指定```Dashboard```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_15-33-20.png)

    选择指定```Dashboard```，拷贝```ID```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_15-33-46.png)

    在```Grafana```选择```Import dashboard```，输入```ID```后点击```load```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_15-36-08.png)

    选择```Prometheus```数据源：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_15-50-28.png)

    最后在```Dashboard```页面可查看到导入的```Dashboard```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-08_15-36-46.png)

* 自定义业务监控指标

  * 对于业务指标（埋点），可实现自定义。如实现订单服务的统计订单总金额、创建10分钟内下单失败率的指标监控：

    * 订单服务新增普罗米修斯监控管理类，维护下单失败次数、下单总数以及下单累计金额指标：
      
      ```bash
      @Component
      public class PrometheusCusMonitor {

          /**
           * 下单失败次数
           */
          private Counter orderErrorCount;

          /**
           * 下单总数
           */
          private Counter orderCount;

          /**
           * 下单累计金额
           */
          private DistributionSummary orderAmountSum;

          private final MeterRegistry registry;

          @Autowired
          public PrometheusCusMonitor(MeterRegistry registry) {
              this.registry = registry;
          }

          @PostConstruct
          private void init() {
              orderErrorCount = registry.counter("order_error_count", "status", "error");
              orderCount = registry.counter("order_count", "order", "order_tpl");
              orderAmountSum = registry.summary("order_amount_sum", "order", "order_tpl");
          }

          public Counter getOrderErrorCount() {
              return orderErrorCount;
          }

          public Counter getOrderCount() {
              return orderCount;
          }

          public DistributionSummary getOrderAmountSum() {
              return orderAmountSum;
          }

      }
      ```
      
      ```init()```初始化方法中，如```registry.counter```调用方法的参数，第一个参数表示为指标名称，第二、三个参数表示为指标```label```及其值。

    * 订单服务中的创建订单接口，应用监控指标：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-20-05.png)

    * 启动订单服务，执行创建订单接口（包含失败）：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-31-02.png)

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-31-57.png)

    * 查看订单服务暴露的```prometheus```端点是否已包含自定义监控指标：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-35-05.png)

    * ```grafana```上创建```创建10分钟内下单失败率```以及```统计订单总金额```面板：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-47-01.png)

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-10_16-54-35.png)  

      其中创建10分钟内下单失败率指标为```sum(rate(order_error_count_total{status="error",}[10m])) / sum(rate(order_count_total{order="order_tpl",}[10m])) * 100```，统计订单总金额指标为```order_amount_sum_sum{order="order_tpl",}```
    
    * 上述的步骤前提为订单服务集成```prometheus```。

* 添加监控警告
  
  * 对于监控指标，可配置警告规则，当达到警告条件时触发警告。如添加10分钟内下单失败率大于10%的监控警告：

    * 在```/prometheus```目录下新建```/rules```子目录并在其目录下新增订单服务警告规则文件```order-service-alert-rule.yaml```：
      
      ```bash
      groups:
        - name: order-service-alert-rule # 警告分组名称
          rules:
            - alert: order-error-rate-high # 警告名称
              expr: sum(rate(order_error_count_total{status="error",}[10m])) / sum(rate(order_count_total{order="order_tpl",}[10m])) > 0.1 # 警告规则：10分钟内下单失败率大于10%
              for: 1m
              labels: # 自定义标签
                severity: major # 设置严重程度标签
                team: garden # 设置警告团队，用于匹配alertmanager接收邮箱设置
              annotations:
                summary: "订单服务响应异常！！" # 设置标题
                description: "10分钟订单错误率已经超过10% (当前值: {{ $value }} ！！！" # 设置内容描述

      ```

    * ```prometheus-server```新增```altermanager```连接配置：
      
      ```bash
      alerting:
        alertmanagers:
          - static_configs:
              - targets:
                  - host.docker.internal:9093 # altermanager地址，默认的协议是http，docker容器访问宿主机使用host.docker.internal域名
      ```

      以及新增警告规则文件路径配置：

      ```bash
      rule_files:
        - /prometheus/rules/*.yaml
      ```

      最后刷新```prometheus-server```配置（```curl -X POST http://${ip}:9090/-/reload```）

    * ```altermanager```路由配置新增子路由：
      
      ```bash
      routes: # 子路由，根据match路由
        - receiver: 'garden-mail-receiver'
          group_wait: 10s
          match: # 匹配自定义标签
          team: garden  
      ```

      以及新增告警接收者配置：
      
      ```bash
      receivers:
        - name: 'garden-mail-receiver'
          email_configs:
            - to: '847686279@qq.com'
      ```

      最后刷新```altermanager```配置（```curl -X POST http://${ip}:9093/-/reload```）

    * 订单服务模拟创建订单失败：
      
      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-14_23-01-04.png)

      此时10分钟内下单失败率为100%，大于10%。

    * 登录```altermanager dashboard```(```http://${ip}:9093```)可查看触发的警告：
      
      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-12_16-55-55.png)

      登录收件人邮箱可查看警告邮件：
      
      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2023-10-14_23-09-38.png)

> 参考文献

* [Spring Boot (十九)：使用 Spring Boot Actuator 监控应用](http://www.ityouknow.com/springboot/2018/02/06/spring-boot-actuator.html)
* [Spring Boot 微服务应用集成Prometheus + Grafana 实现监控告警](https://juejin.cn/post/6844904052417904653)
* [【玩转Docker】使用Docker部署alertmanager并配置prometheus告警](https://cloud.tencent.com/developer/article/2211153)
* [prometheus installation](https://prometheus.io/docs/prometheus/latest/installation/)