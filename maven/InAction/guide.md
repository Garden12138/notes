## Maven in action
#### Maven使用入门
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