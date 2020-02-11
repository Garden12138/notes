## Maven in action
> 什么是Maven
  * Maven是一跨平台的项目管理工具，主要服务于Java平台的项目信息管理，依赖管理以及项目构建（源代码编译，单元测试运行，文档生成，打包部署这些流水线示软件步骤为构建）。
  * Maven可作为构建工具，抽象构建过程，提供构建实现，可跨平台的实现自动化构建。
  * Maven可作为依赖管理工具，可通过坐标定位类库并引入。
  * Maven可作为项目信息管理工具，可管理项目描述，开发者列表，版本控制系统地址，许可证，缺陷管理系统地址等。还可获取项目文档，测试报告，静态分析报告，源码版本日志报告。
> Maven安装与配置
  * Window
    ```
    # 检查JDK，如果不存在则需优先安装JDK，Maven运行依赖JDK
    java -version
    # 下载Maven，前往官网下载对应操作系统压缩包
    http://maven.apache.org/download.html
    # 本地安装，将安装文件解压至指定目录，新增系统环境变量M2_HOME，赋值Maven解压安装目录，更新系统环境变量Path，在变量值最末尾添加%M2_HOME%\bin;
    # 检查Maven安装是否成功
    mvn -v
    # 升级Maven，下载安装新版本Maven，系统环境变量值更改为最新版本Maven安装目录
    ```
  * Unix
    ```
    # 检查JDK
    java -version
    # 下载Maven
    cd /usr/local
    mkdir maven
    wget https://mirrors.tuna.tsinghua.edu.cn/apache-maven-3.6.3-bin.tar.gz
    # 本地安装
    tar -zxvf apache-maven-3.6.3-bin.tar.gz -C .
    vim /etc/profile
    MAVEN_HOME=/usr/local/maven/apache-maven-3.6.3
    export MAVEN_HOME
    PATH=$MAVEN_HOME/bin:$PATH
    export PATH
    source /etc/profile
    # 检查Maven安装是否成功
    mvn -v
    # 升级Maven，与Windows原理一致
    ```
> 安装目录分析
  * bin
    ```
    mvn: 基于Unix的shell脚本，配置Java命令，准备classpath和Java系统属性后执行Java命令。
    mvn.cmd: 基于Windows的cmd脚本，作用同mvn。
    mvnDebug: 基于Unix的shell脚本，使用Debug模式配置Java命令，准备classpath和Java系统属性后执行Java命令。
    mvnDebug.cmd: 基于Windows的cmd脚本，作用同mvnDebug。
    m2.conf: classworlds的配置文件。
    mvnyjp: shell脚本，用于分析Maven构建过程。
    ```
  * boot
    ```
    plexus-classworlds: 是一个类加载器框架，Maven使用该框架加载自己的类型。详细参考http://classworlds.codehanus.org/
    ```
  * conf
    ```
    settins.xml: 直接修改该文件，在机器上全局定制Maven行为。一般情况下，更倾向Copy该文件至~/.m2/repository/，然后修改该文件，在用户范围内全局定制Maven行为。
    ```
  * lib
    ```
    该目录包含所有Maven运行时需要的Java类型。
    ```
  * LICENSE
    ```
    该文件记录了Maven使用的软件许可证Apache License Version 2.0
    ```
  * NOTICE
    ```
    该文件记录了Maven包含的第三方软件。
    ```
  * README.txt
    ```
    该文件包含了Maven的简要介绍，包括安装需求及如何安装的简要指令等。
    ```
  * ~/.m2
    ```
    该目录包含repository目录，放置Maven本地仓库，所有的Maven构件都存储在该仓库。
    ```
> maven安装最佳实践  
  * 设置MAVEN_OPTS环境变量
    ```
    设置MAVEN_OPTS的值为 -Xms128m -Xmx512m，该环境变量可解决Maven在运行时可能出现的内存溢出的问题（mvn命令实质是java命令）。
    ```
  * 配置用户范围settings.xml
    ```
    $M2_HOME/conf/settings.xml为整台机器的所有用户范围内的Maven行为配置，~/.m2/settings.xml为当前用户范围内的Maven行为配置。推荐使用用户范围内的Maven行为可避免无意识地影响到系统中的其他用户且便于升级。
    ```
  * 不使用IDE内嵌Maven
    ```
    内嵌Maven一般为最新Maven，最新版本Maven容易存在不稳定因素，并且最新内嵌Maven与本地Maven在使用命令行时可能由于版本不一致容易造成构建行为不一致的情况。
    ```
> Maven使用入门
  * 编写POM，POM（Project Object Model，项目对象模型）定义了项目的基本信息，声明项目依赖，描述项目如何构建。
    ```
    ## 指定XML文档的版本以及编码方式
    <?xml version="1.0" encoding="UTF-8"?>
    ## 声明project元素且POM相关命名空间以及xsd元素。project元素为pom.xml的根元素，使用POM相关命名空间以及xsd元素可让IDE快速编辑POM。
    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"><project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    </project>
    ## 声明当前POM模型版本，maven2.0以及maven3.0只能使用4.0.0 
    <modelVersion>4.0.0</modelVersion>
    ## 声明项目所在的组织或公司
    <groupId>com.garden</groupId>
    ## 声明当前POM唯一ID，一般为项目名称
    <artifactId>hello-world</artifactId>
    ## 声明当前项目版本
    <version>0.0.1-SNAPSHOT</version>
    ## 声明当前项目名称
    <name>hello-world</name>
    ## 声明当前项目描述
    <description>hello-world project demo</description>     
    ```
  * 编写主代码
    ```
    ## 在默认目录src/main/java下创建目录com/garden/helloworld，编写启动类（主类）Application
    package com.garden.helloworld;
    public class Application{
      public String sayHello(){
        return "Hello World";
      }
      public static void main(String[] agrs){
        Application application = new Application();
        System.out.println(application.sayHello());
      }
    }
    ## 在项目根目录下运行命令mvn clean compile（clean插件先清理输出目录target/后再使用resources插件加载项目资源，最后使用compiler插件将项目主代码即src/main/java目录下代码编译至target/classes目录）
    mvn clean compile
    ```
  * 编写测试代码
    ```
    ## 添加测试代码中使用的JUnit依赖，在项目POM文件添加dependencies元素，该元素可包含多个dependency，其中groupId，artifactId，version指定JUnit坐标，scope元素指定依赖作用范围为测试代码生效，默认为compile即主代码以及测试代码都生效。
    <dependencies>
      <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.7</version>
        <scope>test</scope>
      </dependency>
    </dependencies>
    ## 设置compiler插件支持的JDK版本，默认只支持JDK1.3
    <project>
      <build>
        <plugins>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-compiler-plugin</artifactId>
          <configuration>
            <source>1.8</source>
            <target>1.8</target>
          </configuration>
        </plugins>
      </build>
    </project>
    ## 在默认目录src/main/test下创建目录com/garden/helloworld，编写测试类Test。单元测试包含准备测试类及数据，执行测试行为以及验证测试结果三个步骤。
    package com.garden.helloworld;
    import static org.junit.Assert.assertEquals;
    import org.junit.Test;
    public class Test{
      @Test
      public void testSayHello(){
        Application application = new Application();
        String result = application.sayHello();
        assertEquals("Hello World",result);
      }
    }
    ## 在项目根目录下运行命令mvn clean test（先执行主代码资源处理以及主代码编译后再执行测试代码资源处理以及测试代码编译，执行过程为clean:clean resources:resources compiler:compile resources:testResources compiler:testCompile）
    mvn clean test 
    ```
  * 打包和运行
    ```
    ## 配置maven-shade-plugin插件，生成可执行jar文件
    <project>
      <build>
        <plugins>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-shade-plugin</artifactId>
          <version>1.2.1</version>
          <executions>
            <execution>
              <phase>package</phase>
              <goals>
                <goal>shade</goal>
              </goals>
              <configuration>
                <transformers>
                  <transformer implementation="org.apache.maven.plugins.shade.resource.MainfestResourceTransformer">
                    <mainClass>com.garden.helloworld.Application
                  </transformer>
                </transformers>
              </configuration>
            </execution>
          </executions>
        </plugins>
      </build>
    </project>
    ## 打包未包含其他maven模块的项目，在target目录下生成以artifact-version.jar规则的jar包。
    mvn clean package
    ## 打包包含其他maven模块的项目，执行package操作之后（执行test操作前会执行compile，执行package操作前会执行test，执行install操作前会执行package操作，compile->test->package-install存在覆盖执行即会执行之前的操作）将jar安装至本地仓库。
    mvn clean install
    ## 使用java命令运行
    java -jar target/hello-world-1.0-SNAPSHOT.jar
    ```
  * 使用Archetype生成项目骨架
    ```
    mvn archetype:generate
    ```
> 坐标和依赖
  * 何为Maven坐标
    * 坐标是Maven管理项目依赖中唯一标记Java构件的标识，坐标元素包括groupId，artifactId，version，packaging，classifier。
  * 坐标详解
    * groupId：必须，定义当前Maven项目（模块）隶属的实际项目，如实际项目为SpringFramework，其对应的Maven项目（模块）包括spring-core，spring-context等。命名规则通常与域名反向一一对应，如groupId为org.sonatype.nexus，org.sonatype表示Sonatype公司建立的一个非盈利性组织，nexus表示Nexus这一实际项目，该groupId与域名nexus.sonatype.org反向一一对应。
    * artifactId：必须，定义实际项目中的一个Maven项目（模块）。命名规则为通常以实际项目名作为前缀，如artifactId为nexus-indexer，其中nexus为实际项目名。
    * version：必须，定义当前Maven项目（模块）所处版本。
    * packaging：可选，定义当前Maven项目（模块）打包方式，默认为jar。
    * classifier：帮助定义构建输出的一些附属构建（如nexus-indexer-2.0.0-javadoc.jar，nexus-indexer-2.0.0-sources.jar），不是项目直接默认生成，而是由附加插件帮助生成。
  * 依赖的配置
    * 一个依赖声明包含groupId，artifactId，version，type，scope，optional，exclusions元素。
    * groupId，artifactId，version为依赖的基本坐标。
    * type为依赖的类型，对应于项目定义的packaging。
    * scope为依赖的范围。
    * optional为标记依赖是否可选。
    * exclusions为用来排除传递性依赖。
    * 示例
      ```
      <project>
      ...
        <dependencies>
          <dependency>
            <groupId>...</groupId>
            <artifactId>...</artifactId>
            <version>...</version>
            <type>...</type>
            <scope>...</scope>
            <optional>...</optional>
            <exclusions>
              <exclusion>...</exclusion>
            </exclusions>
          </dependency>
        </dependencies>
      ...
      </project>
      ```
  * 依赖范围
    * 依赖范围用来控制依赖与三种classpath的关系，用元素scope表示，默认为compile。
    * 依赖范围与classpath的关系如下

      依赖范围（Scope） | 对于编译classpath | 对于测试classpath | 对于运行classpath | example 
      :-: | :-: | :-: | :-: | :-:
      compile | √ | √ | √ | spring-core 
      test | × | √ | × | JUnit |
      provided | √ | √ | × | servlet-api |
      runtime | × | √ | √ | JDBC驱动实现 |
      system | √ | √ | × | 本地依赖，Maven仓库之外的类库文件，可配合systemPath元素引用环境变量 |
      import | × | × | × |  |

  * 传递性依赖
    * 假设hello-world有一个compile范围的spring-core依赖，spring-core有一个compile范围的commons-logging依赖，那么commons-logging为hello-world的传递性依赖，spring-core为hello-world的第一直接依赖，commons-logging为hello-world的第二直接依赖。传递性依赖与依赖范围有关。
    * 依赖范围影响传递性依赖

      第一直接依赖范围\第二直接依赖范围 | compile | test | provided | runtime 
      :-: | :-: | :-: | :-: | :-:
      compile | compile | × | × | runtime
      test | test | × | × | test
      provided | provided | × | provided | provided 
      runtime | runtime | × | × | runtime
  * 依赖调解
    * 解决不同传递路径的相同传递依赖的版本冲突问题，如A->B->C->X(1.0)，X(1.0)为A的传递依赖，A->D->X(2.0)，X(2.0)为A的传递依赖，maven解析会出现依赖重复，故maven定义依赖调解原则解决这一问题。
    * 原则
      * 路径最近优先解析。
      * 路径长度相同，最先声明优先解析。
  * 可选依赖
    * 解决不同传递依赖特性互斥问题，如A->B->X，A->B->Y，X与Y依赖特性用于B，但在A中X与Y特性互斥，故maven定义可选依赖原则。
    * 原则
      * 将互斥的依赖设置为可选，设置为可选的依赖不会传递。
    * 注意事项
      * 不推荐使用可选依赖，使用可选依赖的原因是解决某一个项目多特性问题，在面向对象设计中违背单一职责原则，在面临多特性问题时最好的解决的办法拆分项目分离特性，如将含有X特性与Y特性的项目project拆分成project-x与project-y。
  * 最佳实践
    * 排除依赖
      * 解决由于传递依赖的不稳定性影响当前项目的问题，使用exclusion元素排除依赖。
        ```
        <dependency>
          ...
          <exclusions>
            <exclusion>
              <groupId>...</groupId>
              <artifactId>...<artifactId>
            </exclusion>
          </exclusions>
        </dependency>
        ```
    * 归类依赖
      * 解决由于依赖版本升级其子模块依赖版本升级难以维护问题，使用properties元素定义依赖版本号，后续该版本及其子模块版本在此维护。依赖声明中使用$符号获取版本号值。
        ```
        <properties>
          <springframework.version>2.5.6</springframework.version>
        </properties>
        <dependency>
          <groupId>org.springframework</groupId>
          <artifactId>spring-beans</artifactId>
          <version>${springframework.version}</version>
        </dependency>
        ```
    * 优化依赖
      * 对Maven依赖进行优化，去除多余依赖，显示地声明某些必要的依赖。
        ```
        ## 查看已解析依赖列表
        mvn dependency:list
        ## 查看已解析依赖树
        mvn dependency:tree
        ## 分析已解析依赖
        mvn dependency:analyze
        ```
> 仓库
  * 何为Maven仓库
    * 在Maven中，任何一个依赖，插件和项目构建输出都称为构件。构件的逻辑表示方式为坐标和依赖，物理表示方式为仓库。Maven可以在某个位置统一存储所有Maven项目共享的构件，这个统一的位置成为仓库。
  * 仓库的布局
    * 任何一个构件都有唯一的坐标，根据这个坐标可以定义其在仓库中的唯一存储路径，这就是Maven的仓库布局方式。
    * 仓库的布局方式为groupId/artifactId/version/artifactId-version-classifier.packaging
  * 仓库的分类
    * 仓库分为本地仓库和远程仓库。当Maven根据坐标寻找构件的时候，Maven先检查本地仓库是否存在目标构件，若不存在则从远程仓库查找并下载构件至本地仓库使用。远程仓库默认为中央仓库，还可以为私服或者其他开源远程仓库。
    * 本地仓库，当Maven在执行编译或者测试时，如需要使用依赖文件，它总是基于坐标使用本地仓库的依赖文件。默认情况下，本地仓库路径为用户目录/.m2/repository，若需要修改本地仓库路径，只需编辑用户目录/.m2/repository/settings.xml（由Maven安装目录下的conf/settings.xml复制而来）的localRepository元素值为自定义本地仓库地址即可。
      ```
      <settings>
        <localRepository>/usr/local/maven/m2/repository</localRepository>
      </settings>
      ```
    * 远程仓库，当Maven无法从本地仓库找到需要的构件的时候，会从远程仓库下载构件至本地仓库。
      * 中央仓库，是默认的远程仓库。Maven安装文件中自带中央仓库的配置，打开$M2_HOME/lib/maven-model-builder-3.0.jar，访问路径org/apache/maven/pom-4.0.0.xml，可以看到配置：
        ```
        <repository>
          <repository>
            <!-- 中央仓库唯一标识 -->
            <id>central</id>
            <!-- 中央仓库名称 -->
            <name>Maven Repository Switchboard</name>
            <!-- 中央仓库地址 -->
            <url>http://repo1.maven.org/maven2</url>
            <!-- 中央仓库布局 -->
            <layout>default</layout>
            <!-- 是否从中央仓库下载快照版本的构件-->
            <snapshots>
              <enabled>false</enabled>
            </snapshots>
          </repository>
        </repository>
        ```
      * 私服，是架设在局域网内的仓库服务，代理广域网上的远程仓库，供局域网内的Maven用户使用。当Maven用户需要下载构件的时候，从私服请求，若私服不存在目标构件，则私服通过广域网从外部远程仓库下载，缓存到私服后再提供给局域网内的下载请求。搭建私服可以节省自己外网带宽，加速Maven构建，易部署第三方构件，提高稳定性增强控制以及降低中央仓库的负荷。

        ![Snipaste_2020-02-08_16-40-53.png](https://i.loli.net/2020/02/08/nS3YpgzbZt6rBJf.png)

  * 远程仓库的配置
    * 连接远程仓库，若默认的中央仓库无法满足项目要求，可能需要的构件在另外一个远程仓库，可在项目POM文件中配置另外一个远程仓库。在repositories元素下，可以用repository子元素声明一个或者多个远程仓库。
      ```
      <repositories>
        <repository>
          <!-- 指定仓库唯一标识 -->
          <id>jboss</id>
          <!-- 指定仓库名称 -->
          <name>JBoss Repository</name>
          <!-- 指定仓库地址 -->
          <url>http://repository.jboss.com/maven2/</url>
          <!-- 指定仓库布局，元素值为default表示仓库的布局为Maven2或Maven3的默认布局 -->
          <layout>default</layout>
          <!-- 指定是否从仓库下载快照版本的构件 -->
          <snapshots>
            <enabled>false</enabled>
            <!-- 指定从远程仓库检查更新频率 -->
            <!-- 默认值为daily表示每天一次检查更新，never表示从不检查更新 -->
            <!-- always表示每次构建检查更新，interval:X表示每隔X分钟检查更新 -->
            <updatePolicy>always</updatePolicy>
            <!-- 指定检查校验和文件的策略 -->
            <!-- 当构建部署至仓库中时会部署对应的校验和文件，在下载构建的时候Maven会验证校验和文件 -->
            <!-- 默认值为warn表示执行构建时候输出警告信息，fail表示遇到校验和错误让构建失败 -->
            <!-- ignore表示完全忽略校验和错误 -->
            <checksumPolicy>ignore</checksumPolicy>
          </snapshots>
          <!-- 指定是否从仓库下载发布版本的构件 -->
          <releases>
            <enabled>true</enabled>
          </releases>
        </repository>
      </repositories>
      ```
    * 认证远程仓库，出于安全考虑，远程仓库（如私服）会设置安全认证信息，为仓库的Maven使用者提供一组用户密码认证信息，maven使用者需在settings.xml中编辑认证信息。
      ```
      <settings>
      ...
        <servers>
          <server>
            <!-- 指定仓库唯一id -->
            <id>garden-repo</id>
            <!-- 设置用户密码认证信息 -->
            <username>garden</username>
            <password>garden</password>
          </server>
        </servers>
      ...
      </settings>
      ```
    * 部署远程仓库，私服的一大作用是部署第三方构件，包括组织内部生成的构件以及无法从外部仓库直接获取的构件。
      ```
      ## 编辑项目POM，配置部署的仓库信息
      <project>
        ...
        <distributionManagement>
          <!-- 配置发布版本仓库信息 -->
          <repository>
            <id>garden-repo</id>
            <name>Garden Release Repository</name>
            <url>http://http://39.108.168.201/content/repositories/garden-repo</url>
            <name></name>
          </repository>
          <!-- 配置快照版本仓库信息 -->
          <snapshotRepository>
            <id>garden-repo</id>
            <name>Garden Release Repository</name>
            <url>http://http://39.108.168.201/content/repositories/garden-repo</url>
            <name></name>
          </snapshotRepository>
        </distributionManagement>
      </project>
      ## 编辑本地settings.xml，配置远程仓库认证信息
      ## 执行mvn clean deploy，项目构建输出并部署
      mvn clean deploy
      ```
      
  * 快照版本
    * 在Maven中任何一个项目或者构件都有属于自己的版本，其中版本值为2.0-SNAPSHOT为不稳定的快照版本。快照版本用于解决组织内部项目或者模块间依赖使用版本更新问题。只需将项目或者模块版本设置如2.1-SNAPSHOT格式，在发布至私服过程中Maven会为构件打上时间戳，如2.0-20200202.202020-20表示2020年2月2日20时20分20秒第20次快照2.0版本包。
    * 快照版本用于组织内的项目或者模块的依赖使用，对于外部依赖统一使用稳定的发布版本。
  * 从仓库解析依赖的机制
  * 镜像
  * 仓库搜索服务        