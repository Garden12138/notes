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

* 配置```log4j2```日志收集功能
  
  * 引入```skywalking log4j2```依赖，排除```springboot```自带的```logback```框架以及引入```log4j2```依赖：

    ```bash
    <!-- spring boot 依赖 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <exclusions>
            <exclusion>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-logging</artifactId>
            </exclusion>
        </exclusions>
    </dependency>
    <!-- skywalking log4j2 依赖 -->
    <dependency>
        <groupId>org.apache.skywalking</groupId>
        <artifactId>apm-toolkit-log4j-2.x</artifactId>
        <version>${skywalking-log4j2.version}</version>
    </dependency>
    <!-- log4j2 依赖 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-log4j2</artifactId>
    </dependency>
    ```
  
  * 新增```skywalking log4j2```配置文件（```log4j2-spring.xml```）：

    ```bash
    <?xml version="1.0" encoding="UTF-8"?>
    <Configuration>
    <!--<Configuration status="WARN" monitorInterval="30"> -->
    <properties>
        <!-- 设置日志文件路径，推荐格式为：${USER_HOME}/${APP_NAME}/logs 其中不同操作系统路径分割符不同：windows为\ linux为/ -->
        <property name="LOG_HOME">D:\logs</property>
        <property name="LOG_PATTERN">%d{yyyy-MM-dd HH:mm:ss.SSS} [%-5level] [%traceId] [%logger{50}.%M:%L] - %msg%n</property>
    </properties>
    <Appenders>
        <!--*********************控制台日志***********************-->
        <Console name="consoleAppender" target="SYSTEM_OUT">
            <!--设置日志格式-->
            <PatternLayout
                    pattern="${LOG_PATTERN}"
                    disableAnsi="false" noConsoleNoAnsi="false"/>
        </Console>

        <!--*********************文件日志***********************-->
        <!--all级别日志-->
        <RollingFile name="allFileAppender"
                     fileName="${LOG_HOME}/all.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/all-%d{yyyy-MM-dd}-%i.log.gz">
            <!--设置日志格式-->
            <PatternLayout pattern="${LOG_PATTERN}" />
            <Policies>
                <!-- 设置日志文件切分参数 -->
                <!--<OnStartupTriggeringPolicy/>-->
                <!--设置日志基础文件大小，超过该大小就触发日志文件滚动更新-->
                <SizeBasedTriggeringPolicy size="100 MB"/>
                <!--设置日志文件滚动更新的时间，依赖于文件命名filePattern的设置-->
                <TimeBasedTriggeringPolicy/>
            </Policies>
            <!--设置日志的文件个数上限，不设置默认为7个，超过大小后会被覆盖；依赖于filePattern中的%i-->
            <DefaultRolloverStrategy max="30"/>
        </RollingFile>

        <!--debug级别日志-->
        <RollingFile name="debugFileAppender"
                     fileName="${LOG_HOME}/debug.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/debug-%d{yyyy-MM-dd}-%i.log.gz">
            <Filters>
                <!--过滤掉info及更高级别日志-->
                <ThresholdFilter level="info" onMatch="DENY" onMismatch="NEUTRAL"/>
            </Filters>
            <!--设置日志格式-->
            <PatternLayout pattern="${LOG_PATTERN}" />
            <Policies>
                <!-- 设置日志文件切分参数 -->
                <!--<OnStartupTriggeringPolicy/>-->
                <!--设置日志基础文件大小，超过该大小就触发日志文件滚动更新-->
                <SizeBasedTriggeringPolicy size="100 MB"/>
                <!--设置日志文件滚动更新的时间，依赖于文件命名filePattern的设置-->
                <TimeBasedTriggeringPolicy/>
            </Policies>
            <!--设置日志的文件个数上限，不设置默认为7个，超过大小后会被覆盖；依赖于filePattern中的%i-->
            <DefaultRolloverStrategy max="30"/>
        </RollingFile>

        <!--info级别日志-->
        <RollingFile name="infoFileAppender"
                     fileName="${LOG_HOME}/info.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/info-%d{yyyy-MM-dd}-%i.log.gz">
            <Filters>
                <!--过滤掉warn及更高级别日志-->
                <ThresholdFilter level="warn" onMatch="DENY" onMismatch="NEUTRAL"/>
            </Filters>
            <!--设置日志格式-->
            <PatternLayout pattern="${LOG_PATTERN}" />
            <Policies>
            <!-- 设置日志文件切分参数 -->
            <!--<OnStartupTriggeringPolicy/>-->
            <!--设置日志基础文件大小，超过该大小就触发日志文件滚动更新-->
            <SizeBasedTriggeringPolicy size="100 MB"/>
            <!--设置日志文件滚动更新的时间（单位时），依赖于文件命名filePattern的设置-->
            <TimeBasedTriggeringPolicy interval="1" modulate="true" />
            </Policies>
            <!--设置日志的文件个数上限，不设置默认为7个，超过大小后会被覆盖；依赖于filePattern中的%i-->
            <DefaultRolloverStrategy max="30"/>
        </RollingFile>

        <!--warn级别日志-->
        <RollingFile name="warnFileAppender"
                     fileName="${LOG_HOME}/warn.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/warn-%d{yyyy-MM-dd}-%i.log.gz">
            <Filters>
                <!--过滤掉error及更高级别日志-->
                <ThresholdFilter level="error" onMatch="DENY" onMismatch="NEUTRAL"/>
            </Filters>
            <!--设置日志格式-->
            <PatternLayout pattern="${LOG_PATTERN}" />
            <Policies>
                <!-- 设置日志文件切分参数 -->
                <!--<OnStartupTriggeringPolicy/>-->
                <!--设置日志基础文件大小，超过该大小就触发日志文件滚动更新-->
                <SizeBasedTriggeringPolicy size="100 MB"/>
                <!--设置日志文件滚动更新的时间，依赖于文件命名filePattern的设置-->
                <TimeBasedTriggeringPolicy/>
            </Policies>
            <!--设置日志的文件个数上限，不设置默认为7个，超过大小后会被覆盖；依赖于filePattern中的%i-->
            <DefaultRolloverStrategy max="30"/>
        </RollingFile>

        <!--error及更高级别日志-->
        <RollingFile name="errorFileAppender"
                     fileName="${LOG_HOME}/error.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/error-%d{yyyy-MM-dd}-%i.log.gz">
            <!--设置日志格式-->
            <PatternLayout pattern="${LOG_PATTERN}" />
            <Policies>
                <!-- 设置日志文件切分参数 -->
                <!--<OnStartupTriggeringPolicy/>-->
                <!--设置日志基础文件大小，超过该大小就触发日志文件滚动更新-->
                <SizeBasedTriggeringPolicy size="100 MB"/>
                <!--设置日志文件滚动更新的时间，依赖于文件命名filePattern的设置-->
                <TimeBasedTriggeringPolicy/>
            </Policies>
            <!--设置日志的文件个数上限，不设置默认为7个，超过大小后会被覆盖；依赖于filePattern中的%i-->
            <DefaultRolloverStrategy max="30"/>
        </RollingFile>

        <!--json格式error级别日志-->
        <RollingFile name="errorJsonAppender"
                     fileName="${LOG_HOME}/error-json.log"
                     filePattern="${LOG_HOME}/error-json-%d{yyyy-MM-dd}-%i.log.gz">
            <JSONLayout compact="true" eventEol="true" locationInfo="true"/>
            <Policies>
                <SizeBasedTriggeringPolicy size="100 MB"/>
                <TimeBasedTriggeringPolicy interval="1" modulate="true"/>
            </Policies>
        </RollingFile>

        <!-- grpc日志 -->
        <GRPCLogClientAppender name="grpcLog">
            <PatternLayout pattern="${LOG_PATTERN}"/>
        </GRPCLogClientAppender>

    </Appenders>

    <Loggers>
        <!-- 根日志设置 -->
        <Root level="info">
            <AppenderRef ref="consoleAppender" level="debug"/>
            <AppenderRef ref="grpcLog"/>
        </Root>

    <!--        &lt;!&ndash;spring日志&ndash;&gt;-->
    <!--        <Logger name="org.springframework" level="debug"/>-->
    <!--        &lt;!&ndash;druid数据源日志&ndash;&gt;-->
    <!--        <Logger name="druid.sql.Statement" level="warn"/>-->
    <!--        &lt;!&ndash; mybatis日志 &ndash;&gt;-->
    <!--        <Logger name="com.mybatis" level="warn"/>-->
    <!--        &lt;!&ndash; hibernate日志 &ndash;&gt;-->
    <!--        <Logger name="org.hibernate" level="warn"/>-->
    </Loggers>

    </Configuration>
    ```
  
  * ```IDEA```开发环境与```docker```环境环境新增的配置同```logback```一致。

> 说明：

* 本文所描述的```garden12138/sk-agent8.7-openjdk8:1.0.0```镜像为[作者自定义封装的镜像](https://hub.docker.com/repository/docker/garden12138/sk-agent8.7-openjdk8/general)

> 完整代码示例

* [feature/sc-2020.0.1-v2.0.1](https://gitee.com/FSDGarden/microservices-spring/tree/feature%2Fsc-2020.0.1-v2.0.1/)
* * [feature/sc-2020.0.1-v2.0.2](https://gitee.com/FSDGarden/microservices-spring/tree/feature%2Fsc-2020.0.1-v2.0.2/)

> 参考文献

* [Spring cloud 集成 SkyWalking 实现性能监控、链路追踪、日志收集](https://segmentfault.com/a/1190000041661631)
* [SpringCloud系列之接入SkyWalking进行链路追踪和日志收集](https://yelog.org/2021/09/26/spring-cloud-skywalking/)
* [Setup java agent](https://skywalking.apache.org/docs/skywalking-java/v8.8.0/en/setup/service-agent/java-agent/readme/)
* [从0开始DevOps实践](https://developer.aliyun.com/article/1058324)
* [[Bug] Skywalking local setup unable to configure for multiple services](https://github.com/apache/skywalking/discussions/8058) 