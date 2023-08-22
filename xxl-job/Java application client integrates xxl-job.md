## Java 应用客户端集成 xxl-job

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

* ```Bean```类型任务。如新建任务类```SampleXxlJob```，新建任务方法并使用注解```@XxlJob```修饰，编写任务执行逻辑：

  ```bash
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

  在一个任务类中，可新建多个使用注解```@XxlJob```修饰的任务方法。每添加完一个任务类，需在配置类（```XxlJobConfig```）的初始化方法中（```initXxlJobExecutor```）中，手动添加```bean```注册：

  ```bash
  xlJobExecutor.setXxlJobBeanList(Arrays.<Object>asList(...));
  ```

  若需执行分片广播任务，任务创建方式如：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-21_17-16-47.png)

  对应任务执行方法如：

  ```bash
  @XxlJob("shardingJobHandler")
    public void shardingJobHandler() throws Exception {

        // 分片参数
        int shardIndex = XxlJobHelper.getShardIndex();
        int shardTotal = XxlJobHelper.getShardTotal();

        XxlJobHelper.log("分片参数：当前分片序号 = {}, 总分片数 = {}", shardIndex, shardTotal);

        // 业务逻辑
        for (int i = 0; i < shardTotal; i++) {
            if (i == shardIndex) {
                XxlJobHelper.log("第 {} 片, 命中分片开始处理", i);
            } else {
                XxlJobHelper.log("第 {} 片, 忽略", i);
            }
        }

  }
  ```

  若需执行命令行任务，任务创建方式如：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-21_18-05-23.png)

  对应任务执行方法如：

  ```bash
  @XxlJob("commandJobHandler")
    public void commandJobHandler() throws Exception {
        String command = XxlJobHelper.getJobParam();
        int exitValue = -1;

        BufferedReader bufferedReader = null;
        try {
            // command process
            ProcessBuilder processBuilder = new ProcessBuilder();
            processBuilder.command(command);
            processBuilder.redirectErrorStream(true);

            Process process = processBuilder.start();
            //Process process = Runtime.getRuntime().exec(command); windows env

            BufferedInputStream bufferedInputStream = new BufferedInputStream(process.getInputStream());
            bufferedReader = new BufferedReader(new InputStreamReader(bufferedInputStream));

            // command log
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                XxlJobHelper.log(line);
            }

            // command exit
            process.waitFor();
            exitValue = process.exitValue();
        } catch (Exception e) {
            XxlJobHelper.log(e);
        } finally {
            if (bufferedReader != null) {
                bufferedReader.close();
            }
        }

        if (exitValue == 0) {
            // default success
        } else {
            XxlJobHelper.handleFail("command exit value(" + exitValue + ") is failed");
        }

  }
  ```

  若需执行跨平台```http```任务，任务创建方式如：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-21_18-06-26.png)

  对应任务执行方法如：

  ```bash
  @XxlJob("httpJobHandler")
  public void httpJobHandler() throws Exception {

        // param parse
        String param = XxlJobHelper.getJobParam();
        if (param == null || param.trim().length() == 0) {
            XxlJobHelper.log("param[" + param + "] invalid.");

            XxlJobHelper.handleFail();
            return;
        }

        String[] httpParams = param.split("\n");
        String url = null;
        String method = null;
        String data = null;
        for (String httpParam : httpParams) {
            if (httpParam.startsWith("url:")) {
                url = httpParam.substring(httpParam.indexOf("url:") + 4).trim();
            }
            if (httpParam.startsWith("method:")) {
                method = httpParam.substring(httpParam.indexOf("method:") + 7).trim().toUpperCase();
            }
            if (httpParam.startsWith("data:")) {
                data = httpParam.substring(httpParam.indexOf("data:") + 5).trim();
            }
        }

        // param valid
        if (url == null || url.trim().length() == 0) {
            XxlJobHelper.log("url[" + url + "] invalid.");

            XxlJobHelper.handleFail();
            return;
        }
        if (method == null || !Arrays.asList("GET", "POST").contains(method)) {
            XxlJobHelper.log("method[" + method + "] invalid.");

            XxlJobHelper.handleFail();
            return;
        }
        boolean isPostMethod = method.equals("POST");

        // request
        HttpURLConnection connection = null;
        BufferedReader bufferedReader = null;
        try {
            // connection
            URL realUrl = new URL(url);
            connection = (HttpURLConnection) realUrl.openConnection();

            // connection setting
            connection.setRequestMethod(method);
            connection.setDoOutput(isPostMethod);
            connection.setDoInput(true);
            connection.setUseCaches(false);
            connection.setReadTimeout(5 * 1000);
            connection.setConnectTimeout(3 * 1000);
            connection.setRequestProperty("connection", "Keep-Alive");
            connection.setRequestProperty("Content-Type", "application/json;charset=UTF-8");
            connection.setRequestProperty("Accept-Charset", "application/json;charset=UTF-8");

            // do connection
            connection.connect();

            // data
            if (isPostMethod && data != null && data.trim().length() > 0) {
                DataOutputStream dataOutputStream = new DataOutputStream(connection.getOutputStream());
                dataOutputStream.write(data.getBytes("UTF-8"));
                dataOutputStream.flush();
                dataOutputStream.close();
            }

            // valid StatusCode
            int statusCode = connection.getResponseCode();
            if (statusCode != 200) {
                throw new RuntimeException("Http Request StatusCode(" + statusCode + ") Invalid.");
            }

            // result
            bufferedReader = new BufferedReader(new InputStreamReader(connection.getInputStream(), "UTF-8"));
            StringBuilder result = new StringBuilder();
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                result.append(line);
            }
            String responseMsg = result.toString();

            XxlJobHelper.log(responseMsg);

            return;
        } catch (Exception e) {
            XxlJobHelper.log(e);

            XxlJobHelper.handleFail();
            return;
        } finally {
            try {
                if (bufferedReader != null) {
                    bufferedReader.close();
                }
                if (connection != null) {
                    connection.disconnect();
                }
            } catch (Exception e2) {
                XxlJobHelper.log(e2);
            }
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
  public class XxlJobConfig {
    private static Logger logger = LoggerFactory.getLogger(XxlJobConfig.class);


    private static XxlJobConfig instance = new XxlJobConfig();

    public static XxlJobConfig getInstance() {
        return instance;
    }


    private XxlJobSimpleExecutor xxlJobExecutor = null;

    /**
     * init
     */
    public void initXxlJobExecutor(String[] args) {

        // load executor prop from args
        Properties propFromArgs = loadArgs(args);
        // load executor prop from properties
        Properties propFromProperties = loadProperties("xxl-job-executor.properties");
        // init executor
        xxlJobExecutor = new XxlJobSimpleExecutor();
        xxlJobExecutor.setAdminAddresses(null == propFromArgs.getProperty("xxl.job.admin.addresses") ? propFromProperties.getProperty("xxl.job.admin.addresses") : propFromArgs.getProperty("xxl.job.admin.addresses"));
        xxlJobExecutor.setAccessToken(null == propFromArgs.getProperty("xxl.job.accessToken") ? propFromProperties.getProperty("xxl.job.accessToken") : propFromArgs.getProperty("xxl.job.accessToken") );
        xxlJobExecutor.setAppname(null == propFromArgs.getProperty("xxl.job.executor.appname") ? propFromProperties.getProperty("xxl.job.executor.appname") : propFromArgs.getProperty("xxl.job.executor.appname"));
        xxlJobExecutor.setAddress(null == propFromArgs.getProperty("xxl.job.executor.address") ? propFromProperties.getProperty("xxl.job.executor.address") : propFromArgs.getProperty("xxl.job.executor.address"));
        xxlJobExecutor.setIp(null == propFromArgs.getProperty("xxl.job.executor.ip") ? propFromProperties.getProperty("xxl.job.executor.ip") : propFromArgs.getProperty("xxl.job.executor.ip"));
        xxlJobExecutor.setPort(null == propFromArgs.getProperty("xxl.job.executor.port") ? Integer.valueOf(propFromProperties.getProperty("xxl.job.executor.port")) : Integer.valueOf(propFromArgs.getProperty("xxl.job.executor.port")));
        xxlJobExecutor.setLogPath(null == propFromArgs.getProperty("xxl.job.executor.logpath") ? propFromProperties.getProperty("xxl.job.executor.logpath") : propFromArgs.getProperty("xxl.job.executor.logpath"));
        xxlJobExecutor.setLogRetentionDays(null == propFromArgs.getProperty("xxl.job.executor.logretentiondays") ? Integer.valueOf(propFromProperties.getProperty("xxl.job.executor.logretentiondays")) : Integer.valueOf(propFromArgs.getProperty("xxl.job.executor.logretentiondays")));
        // registry job bean
        xxlJobExecutor.setXxlJobBeanList(Arrays.<Object>asList(new StartXxlJob()));
        // start executor
        try {
            xxlJobExecutor.start();
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
    }

    /**
     * destroy
     */
    public void destroyXxlJobExecutor() {
        if (xxlJobExecutor != null) {
            xxlJobExecutor.destroy();
        }
    }


    public static Properties loadProperties(String propertyFileName) {
        InputStreamReader in = null;
        try {
            ClassLoader loder = Thread.currentThread().getContextClassLoader();

            in = new InputStreamReader(loder.getResourceAsStream(propertyFileName), "UTF-8");
            ;
            if (in != null) {
                Properties prop = new Properties();
                prop.load(in);
                return prop;
            }
        } catch (IOException e) {
            logger.error("load {} error!", propertyFileName);
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (IOException e) {
                    logger.error("close {} error!", propertyFileName);
                }
            }
        }
        return null;
    }

    public static Properties loadArgs(String[] args) {
        Properties prop = new Properties();
        for (String arg : args) {
            int eqIndex = arg.indexOf("=");
            prop.setProperty(arg.substring(0, eqIndex), arg.substring(eqIndex + 1));
        }
        logger.info(prop.toString());
        return prop;
    }

  }
  ```

> main 方法编写启动 xxl-job-executor 逻辑

  ```bash
  public static void main(String[] args) {

    try {
        // start
        XxlJobConfig.getInstance().initXxlJobExecutor(args);

        // Blocks until interrupted
        while (true) {
            try {
                TimeUnit.HOURS.sleep(1);
            } catch (InterruptedException e) {
                break;
            }
        }
    } catch (Exception e) {
        logger.error(e.getMessage(), e);
    } finally {
        // destroy
        XxlJobConfig.getInstance().destroyXxlJobExecutor();
    }

  }
  ```

> 注意事项

* 本文所指的```xxl-job-admin```自定义镜像[在这](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)

* 示例可参考[官方](https://github.com/xuxueli/xxl-job/tree/2.4.0/xxl-job-executor-samples/xxl-job-executor-sample-frameless)或[这里](https://gitee.com/FSDGarden/xxl-job-executor/tree/frameless/)