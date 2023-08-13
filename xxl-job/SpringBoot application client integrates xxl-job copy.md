## SpringBoot 应用客户端集成 xxl-job

> 引入 xxl-job-core maven 依赖

* 引入官方依赖，可根据需求选择对应版本，如2.4.0：

  ```bash
  <dependency>
    <groupId>com.xuxueli</groupId>
    <artifactId>xxl-job-core</artifactId>
    <version>2.4.0</version>
  </dependency>
  ```

* 引入自定义依赖，若需实现执行器组的动态更新且```xxl-job-admin```使用自定义镜像，则可选择引入，目前只支持```2.4.0```：
  
  ```bash
  <dependency>
    <groupId>com.garden</groupId>
    <artifactId>xxl-job-core</artifactId>
    <version>2.4.0</version>
  </dependency>

  <profiles>
    <profile>
      <id>garden-tencent-cloud-114</id>
      <repositories>
        <repository>
          <id>maven-releases</id>
          <name>maven-releases</name>
          <url>http://114.132.78.39:18082/repository/maven-releases/</url>
        </repository>
      </repositories>
    </profile>
  </profiles>
  ```

  或仓库失效，则可[下载```jar```包](https://gitee.com/FSDGarden/xxl-job-executor/tree/frameless/lib)，将```jar```包放置项目根目录的```lib```下（若无则新建），```maven```引入依赖为：

  ```bash
  <dependency>
    <groupId>com.garden</groupId>
    <artifactId>xxl-job-core</artifactId>
    <version>2.4.0</version>
    <scope>system</scope>
    <systemPath>${project.basedir}/lib/xxl-job-core-2.4.0.jar</systemPath>
  </dependency>
  ```

  此时需修改```maven```打包配置，将第三方包（```lib```目标下的```jar```）合并打包，推荐使用```assembly```插件：

  ```bash
  <build>
    <plugins>
      <plugin>
        <artifactId>maven-assembly-plugin</artifactId>
        <configuration>
          <archive>
            <manifest>
                <mainClass>${MAIN_CLASSPATH}</mainClass>
            </manifest>
            <manifestEntries>
                <Class-Path>.</Class-Path>
            </manifestEntries>
          </archive>
        </configuration>
        <executions>
          <execution>
            <id>make-assembly</id>
            <phase>package</phase>
            <goals>
                <goal>single</goal>
            </goals>
            <!-- 增加配置 -->
            <configuration>
                <!-- assembly.xml文件路径 -->
                <descriptors>
                    <descriptor>${project.basedir}/assembly.xml</descriptor>
                </descriptors>
            </configuration>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
  ```

  需要新增```assembly.xml```配置文件，具体配置打包方式：

  ```bash
  <assembly>
    <id>all</id>
    <formats>
        <format>jar</format>
    </formats>
    <includeBaseDirectory>false</includeBaseDirectory>
    <dependencySets>
        <!-- 默认的配置 -->
        <dependencySet>
            <outputDirectory>/</outputDirectory>
            <useProjectArtifact>true</useProjectArtifact>
            <unpack>true</unpack>
            <scope>runtime</scope>
        </dependencySet>
        <!-- 增加scope类型为system的配置 -->
        <dependencySet>
            <outputDirectory>/</outputDirectory>
            <useProjectArtifact>true</useProjectArtifact>
            <unpack>true</unpack>
            <scope>system</scope>
        </dependencySet>
    </dependencySets>
  </assembly>
  ```

> 编写任务

* ```Glue```类型任务，使用方式可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/xxl-job/Use%20docker%20deploy%20xxl-job-glue-executor.md)或[官方文档](https://www.xuxueli.com/xxl-job/)。

* ```Bean```类型任务。如新建使用注解```@Component```声明的```Bean```类```SampleXxlJob```，新建任务方法```demoJobHandler```并使用注解```@XxlJob```修饰，编写任务执行逻辑：

  ```bash
  @Component
  public class SampleXxlJob {

    @XxlJob("demoJobHandler")
    public void demoJobHandler() throws Exception {
        XxlJobHelper.log("XXL-JOB, Hello World.");

        for (int i = 0; i < 5; i++) {
            XxlJobHelper.log("beat at:" + i);
            TimeUnit.SECONDS.sleep(2);
        }
        // default success
    }

  }
  ```

> 新增配置文件 xxl-job-executor.properties 并设置
  
  ```bash
  ### xxl-job-admin address list, such as "http://address" or "http://address01,http://address02"
  xxl.job.admin.addresses=http://127.0.0.1:8080/xxl-job-admin
  ### xxl-job-admin access token
  xxl.job.accessToken=
  ### xxl-job-executor appname
  xxl.job.executor.appname=xxl-job-executor-${APP_NAME}
  ### xxl-job-executor registry-address: default use address to registry , otherwise use ip:port if address is null
  xxl.job.executor.address=
  ### xxl-job-executor server-info
  xxl.job.executor.ip=
  xxl.job.executor.port=9998
  ### xxl-job-executor log-path
  xxl.job.executor.logpath=
  ### xxl-job-executor log-retention-days
  xxl.job.executor.logretentiondays=30
  ```
  
  配置```xxl.job.admin.addresses```为设置```xxl-job-admin```可访问地址，可设置多个地址，使用英文```,```分割；配置```xxl.job.accessToken```为设置访问```xxl-job-admin```所需```token```；配置```xxl.job.executor.appname```为设置应用作为执行器的名称；配置```xxl.job.executor.address```为设置应用的可访问地址，提供给```xxl-job-admin```用于任务调度，若为空，则需设置```xxl.job.executor.ip```以及```xxl.job.executor.port```，代表应用的```ip```端口可访问方式；```xxl.job.executor.logpath```为设置执行任务的日志保存路径；配置```xxl.job.executor.logretentiondays```为设置行任务的日志保存时长。

> 新增配置类 XxlJobConfig

  ```bash
  @Configuration
  public class XxlJobConfig {
    private Logger logger = LoggerFactory.getLogger(XxlJobConfig.class);

    @Value("${xxl.job.admin.addresses}")
    private String adminAddresses;

    @Value("${xxl.job.accessToken}")
    private String accessToken;

    @Value("${xxl.job.executor.appname}")
    private String appname;

    @Value("${xxl.job.executor.address}")
    private String address;

    @Value("${xxl.job.executor.ip}")
    private String ip;

    @Value("${xxl.job.executor.port}")
    private int port;

    @Value("${xxl.job.executor.logpath}")
    private String logPath;

    @Value("${xxl.job.executor.logretentiondays}")
    private int logRetentionDays;


    @Bean
    public XxlJobSpringExecutor xxlJobExecutor() {
        logger.info(">>>>>>>>>>> xxl-job config init.");
        XxlJobSpringExecutor xxlJobSpringExecutor = new XxlJobSpringExecutor();
        xxlJobSpringExecutor.setAdminAddresses(adminAddresses);
        xxlJobSpringExecutor.setAppname(appname);
        xxlJobSpringExecutor.setAddress(address);
        xxlJobSpringExecutor.setIp(ip);
        xxlJobSpringExecutor.setPort(port);
        xxlJobSpringExecutor.setAccessToken(accessToken);
        xxlJobSpringExecutor.setLogPath(logPath);
        xxlJobSpringExecutor.setLogRetentionDays(logRetentionDays);

        return xxlJobSpringExecutor;
    }

    /**
     * 针对多网卡、容器内部署等情况，可借助 "spring-cloud-commons" 提供的 "InetUtils" 组件灵活定制注册IP；
     *
     *      1、引入依赖：
     *          <dependency>
     *             <groupId>org.springframework.cloud</groupId>
     *             <artifactId>spring-cloud-commons</artifactId>
     *             <version>${version}</version>
     *         </dependency>
     *
     *      2、配置文件，或者容器启动变量
     *          spring.cloud.inetutils.preferred-networks: 'xxx.xxx.xxx.'
     *
     *      3、获取IP
     *          String ip_ = inetUtils.findFirstNonLoopbackHostInfo().getIpAddress();
     */


  }
  ```

> 注意事项

* 本文所指的```xxl-job-admin```自定义镜像[在这](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)

* 示例可参考[官方](https://github.com/xuxueli/xxl-job/tree/2.4.0/xxl-job-executor-samples/xxl-job-executor-sample-springboot)或[这里](https://gitee.com/FSDGarden/xxl-job-executor/tree/springboot/)