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

    * 配置文件保存更新后，执行```curl -X POST http://${host}/-/reload```热更新```Prometheus Server```，其中```${host}```为```Prometheus Server```的可访问地址。

> Grafana 连接 Prometheus Server

> 实践

* 创建监控 ```Grafana Dashboard```

* 引入监控 ```Grafana Dashboard```市场

* 自定义业务监控指标

* 添加监控警告

> 参考文献

* [Spring Boot (十九)：使用 Spring Boot Actuator 监控应用](http://www.ityouknow.com/springboot/2018/02/06/spring-boot-actuator.html)
* [Spring Boot 微服务应用集成Prometheus + Grafana 实现监控告警](https://juejin.cn/post/6844904052417904653)
* [【玩转Docker】使用Docker部署alertmanager并配置prometheus告警](https://cloud.tencent.com/developer/article/2211153)
* [prometheus installation](https://prometheus.io/docs/prometheus/latest/installation/)