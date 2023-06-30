## SpringCloud 集成 skywalking agent

> IDEA开发环境配置skywalking java agent

* [下载```agent```代理包](https://archive.apache.org/dist/skywalking/8.7.0/apache-skywalking-apm-8.7.0.tar.gz)，其他版本可查看[官方归档](https://archive.apache.org/dist/skywalking/)，找到对应版本的.tar.gz后缀的包，进行下载。

* 通过命令或者软件进行解压：
  
  ```bash
  tar -zxvf apache-skywalking-apm-8.7.0.tar.gz
  ``` 

* ```IDEA```选择并右键点击业务```service```的```application```，选择```Edit Configuration```选项，在```Build and run```栏目点击设置参数```Modify options```，选择```Add VM options```，输入```javaagent```参数：

  ```bash
  -javaagent:${install_path}/apache-skywalking-apm-bin/agent/skywalking-agent.jar -Dskywalking.agent.service_name=${service_name} -Dskywalking.collector.backend_service=${skywalking_aop_address}
  ```

> 应用服务docker部署配置skywalking java agent

* 应用服务的```dockerfile```的```FROM```指令修改为集成```skywalling-agent8.7```的```openjdk8```父级镜像，如：
  
  ```bash
  FROM garden12138/sk-agent8.7-openjdk8:1.0.0
  ```

* 应用服务的```dockerfile```的```ENTRYPOINT```指令新增```java```的```javaagent```参数，如：
  
  ```bash
  ENTRYPOINT ["java", "-javaagent:/sk-bin/agent/skywalking-agent.jar", "-Dskywalking.agent.service_name=${service_name}", "-Dskywalking.collector.backend_service=${skywalking_aop_address}", "-Djava.security.egd=file:/dev/./urandom", "-jar", "/app.jar", "--spring.profiles.active=dev"]
  ```

> 配置日志收集功能

* 上述集成的```skywalking agent```只包含链路追踪功能，若需使用日志收集功能，应用服务必须集成```skywalking log```，日志框架选型可以为```logback```或```log4j2```，且```javaagent```参数需新增```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_host```以及```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_port```分别设置日志```grpc```请求```IP```以及端口。

* 配置```logback```日志收集功能
  
  * 引入```skywalking logback```依赖：

    ```bash
    <!-- skywalking logback 依赖 本文使用version为8.7.0-->
    <dependency>
        <groupId>org.apache.skywalking</groupId>
        <artifactId>apm-toolkit-logback-1.x</artifactId>
        <version>${skywalking-logback.version}</version>
    </dependency>
    ```

  * 新增```skywalking logback```配置文件（```logback-spring.xml```）：

    ```bash
    <?xml version="1.0" encoding="UTF-8"?>
    <configuration scan="true" scanPeriod="10 seconds">

    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

    <appender name="stdout" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.TraceIdPatternLogbackLayout">
                <Pattern>[%d{yyyy-MM-dd HH:mm:ss.SSS}] [${HOSTNAME}] [%X{tid}] [%thread] %level %logger{36}@%method:%line - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <appender name="grpc" class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.log.GRPCLogClientAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
                <Pattern>[%d{yyyy-MM-dd HH:mm:ss.SSS}] [${HOSTNAME}] [%X{tid}] [%thread] %level %logger{36}@%method:%line - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="stdout"/>
        <appender-ref ref="grpc"/>
    </root>

    </configuration>
    ```

  * ```IDEA```开发环境启动```VM```配置新增```javaagent```的参数```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_host```以及```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_port```：

    ```bash
    -javaagent:${install_path}/apache-skywalking-apm-bin/agent/skywalking-agent.jar -Dskywalking.agent.service_name=${service_name} -Dskywalking.collector.backend_service=${skywalking_aop_address} -Dskywalking.plugin.toolkit.log.grpc.reporter.server_host=${skywalking_aop_ip} -Dskywalking.plugin.toolkit.log.grpc.reporter.server_port=${skywalking_aop_port}
    ```
  
  * ```docker```部署环境的```dockerfile```配置的```ENTRYPOINT```指令新增```javaagent```的参数```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_host```以及```-Dskywalking.plugin.toolkit.log.grpc.reporter.server_port```：

    ```bash
    ENTRYPOINT ["java", "-javaagent:/sk-bin/agent/skywalking-agent.jar", "-Dskywalking.agent.service_name=${service_name}", "-Dskywalking.collector.backend_service=${skywalking_aop_address}", "-Dskywalking.plugin.toolkit.log.grpc.reporter.server_host=${skywalking_aop_ip}", "-Dskywalking.plugin.toolkit.log.grpc.reporter.server_port=${skywalking_aop_port}", "-Djava.security.egd=file:/dev/./urandom", "-jar", "/app.jar", "--spring.profiles.active=dev"]
    ```

> 说明：

* 本文所描述的```garden12138/sk-agent8.7-openjdk8:1.0.0```镜像为[作者自定义封装的镜像](https://hub.docker.com/repository/docker/garden12138/sk-agent8.7-openjdk8/general)

> 参考文献

* [Spring cloud 集成 SkyWalking 实现性能监控、链路追踪、日志收集](https://segmentfault.com/a/1190000041661631)
* [SpringCloud系列之接入SkyWalking进行链路追踪和日志收集](https://yelog.org/2021/09/26/spring-cloud-skywalking/)
* [Setup java agent](https://skywalking.apache.org/docs/skywalking-java/v8.8.0/en/setup/service-agent/java-agent/readme/)
* [从0开始DevOps实践](https://developer.aliyun.com/article/1058324)
* [[Bug] Skywalking local setup unable to configure for multiple services](https://github.com/apache/skywalking/discussions/8058) 