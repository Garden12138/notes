## 使用 docker 部署 elasticjob-lite

> 部署注册中心zookeeper
  
* 拉取镜像：

  ```bash
  docker pull zookeeper:latest
  ```

* 运行容器：

  ```bash
  docker run --name zookeeper --restart always -p 2181:2181 -d zookeeper:latest
  ```

> 部署管理端面板elasticjob-lite-ui

* 拉取镜像：
  
  ```bash
  docker pull apache/shardingsphere-elasticjob-lite-ui:latest
  ```

* 运行容器：
  
  ```bash
  docker run --name elasticjob-lite-ui --restart always -p 8088:8088 -d apache/shardingsphere-elasticjob-lite-ui:latest
  ```

> 搭建elasticjob-lite后端服务

* 初始化```SpringBoot```工程项目
 
* 集成```elasticjob-lite```
  
  * ```pom.xml```添加依赖：

    ```bash
    <properties>
        ...
        <elasticjob-lite.version>3.0.1</elasticjob-lite.version>
    </properties>

    <dependencies>
        ...
        <!-- elasticjob-lite-spring-boot 依赖 -->
        <dependency>
            <groupId>org.apache.shardingsphere.elasticjob</groupId>
            <artifactId>elasticjob-lite-spring-boot-starter</artifactId>
            <version>${elasticjob-lite.version}</version>
        </dependency>
    </dependencies>
    ```
  
  * ```application.yamll```配置```elasticjob-lite```数据库类型、注册中心地址包括命名空间：

    ```bash
    elasticjob:
      tracing:
        type: RDB
      reg-center:
        server-lists: ${ZK_HOST:}:${ZK_PORT:}
        namespace: ${ZK_NAMESPACE}
    ```

* 编写定时任务
  
  * 编写实现```SimpleJob```接口的指定任务类：

    ```bash
    @Component
    public class DemoJob implements SimpleJob {

        private final Logger logger = LoggerFactory.getLogger(DemoJob.class);

        @Override
        public void execute(ShardingContext shardingContext) {
            logger.info("[DemoJob] 调度任务开始...");
            try {
                logger.info("[DemoJob] 调度任务：正在执行调度任务...");
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                logger.error("[DemoJob] 调度出现异常... 信息：{}", e.toString());
            } 
            logger.info("[DemoJob] 调度任务结束...");
        }
    }
    ```

  * ```application.yaml```配置指定定时任务：

    ```bash
    elasticjob:
      jobs:
        demoJob: ## 指定定时任务名称
          elasticJobClass: com.garden.jobs.DemoJob ## 指定定时任务的全限定类名
          cron: 0 0 1 * * ?  ## 定时cron表达式
          shardingTotalCount: 1 ## 分片数量
          disabled: true ## 是否启动时生效
          overwrite: false ## 是否可覆盖
    ```

* 集成```docker-maven```打包

  * ```.m2/setting.xml```文件添加```spotify```插件组：

    ```bash
    ...
    <pluginGroups><pluginGroup>com.spotify</pluginGroup></pluginGroups>
    ```
  
  * ```pom.xml```排除默认的打包目标以及新增```docker-maven-plugin```：

    ```bash
    <properties>
        ...
        <dockerfile-maven-plugin.version>1.4.13</dockerfile-maven-plugin.version>
        <repository-name>garden12138</repository-name>
    </properties>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <mainClass>com.garden.JobsApplication</mainClass>
                </configuration>
                <executions>
                    <execution>
                        <goals>
                            <goal>repackage</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
            <!-- dockerfile-maven-plugin -->
            <plugin>
                <groupId>com.spotify</groupId>
                <artifactId>dockerfile-maven-plugin</artifactId>
                <version>${dockerfile-maven-plugin.version}</version>
                <executions>
                    <execution>
                        <id>default</id>
                        <goals>
                            <goal>build</goal>
                            <goal>push</goal>
                        </goals>
                    </execution>
                </executions>
                <configuration>
                    <!-- 设置镜像名称格式，由仓库项目名与构件ID组合 -->
                    <repository>${repository-name}/${artifactId}</repository>
                    <!-- 设置镜像版本号 -->
                    <tag>${project.version}</tag>
                    <!-- 设置镜像构件过程中的环境变量，如Jar文件名 -->
                    <buildArgs>
                        <JAR_FILE>${project.build.finalName}.jar</JAR_FILE>
                    </buildArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>
    ```

> 部署elasticjob-lite后端服务

* 编写```Dockerfile```：

  ```bash
  FROM java:8
  VOLUME /tmp
  ARG JAR_FILE
  ADD target/${JAR_FILE} app.jar
  ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "/app.jar"]
  ```

* 打包```elasticjob-lite```后端服务：

  ```bash
  mvn clean package dockerfile:build
  ```

* 运行```elasticjob-lite```后端服务：

  ```bash
  docker run --name ${CONTAINER_NAME} --restart=always -d -e ZK_HOST=$(docker inspect --format='{{(index (index .NetworkSettings.IPAddress))}}' ${ZK_NAME}) -e ZK_PORT=${ZK_PORT} ${IMG_NAME}:${IMG_VERSION}
  ```

> 使用elasticjob-lite

* 登录管理端面板：

  ```bash
  ## 访问地址：
  http://159.75.138.212:8088/index.html#/login
  ## 账号密码：
  root/root
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-14_11-37-11.png)

* 创建并链接注册中心：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-14_11-39-02.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-14_11-38-25.png)

* 设置定时任务生效:

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-14_11-39-30.png)

  若设置生效后处于分片待调整状态，可将```cron```表达式更新为当前可触发时间（如```* * * * *```）使状态变为正常，然后再将原本```cron```表达式更新：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-17_15-28-43.png)

> 参考文献

* [Running docker container : iptables: No chain/target/match by that name](https://stackoverflow.com/questions/31667160/running-docker-container-iptables-no-chain-target-match-by-that-name)
  
  ```bash
  sudo iptables -t filter -F
  sudo iptables -t filter -X
  systemctl restart docker
  ```

> 示例代码

* [elasticjob-lite-backend](https://gitee.com/FSDGarden/elasticjob-lite-backend.git)