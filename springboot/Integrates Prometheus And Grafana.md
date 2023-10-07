## 集成 Prometheus 以及 Grafana

> 前期准备

* [```SpringBoot``` 集成 ```Actuator```](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Actuator.md)

* [部署 ```Prometheus Server```](https://gitee.com/FSDGarden/learn-note/blob/master/prometheus/Use%20docker%20deploy%20prometheus%20server.md)

* [部署 ```Grafana```](https://gitee.com/FSDGarden/learn-note/blob/master/grafana/Use%20docker%20deploy%20grafana.md)

* [部署 ```Altermanger```](https://gitee.com/FSDGarden/learn-note/blob/master/altermanager/Use%20docker%20deploy%20altermanager.md)

> SpringBoot 集成 Prometheus
  
  * 添加 ```micrometer prometheus registry```依赖
    
    ```bash
    <dependency>
        <groupId>io.micrometer</groupId>
        <artifactId>micrometer-registry-prometheus</artifactId>
    </dependency>
    ```

> Prometheus Server 注册 SpringBoot Server

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