## Maven in action
#### 聚合与继承
> 聚合与继承
  * 概念
    * 随着应用程序复杂度逐渐提高，开发常使用分模块的方式降低程序复杂性，Maven项目在实际应用中也可划分模块，Maven利用能够将各模块聚合在一起构建的聚合特性和能够抽取各模块相同构建统一配置的继承特性实现项目模块化的功能。
  * 聚合
    * 通过创建一个打包方式为pom以及使用module元素声明任意数量模块的聚合模块来实现聚合。
      ```
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      <groupId>com.garden</groupId>
      <artifactId>platform</artifactId>
      <version>1.0-SNAPSHOT</version>
      <packaging>pom</packaging>

      <name>platform</name>

      <modules>
        <!-- 相对于当前POM文件的各子模块的POM文件路径 -->
        <module>platform-dependency</module>
        <module>platform-register</module>
        <module>platform-business</module>
        <module>platform-banner</module>
        <module>platform-sdk</module>
      </modules>
      </project>
      ```
    * 聚合构建的原理
      * 首先解析聚合模块POM，分析要构建的模块，并计算出一个反应堆（所有模块组成的一个构建结构）构建顺序，然后根据这个顺序构建各个模块。
  * 继承
    * 通过创建一个打包方式为pom，声明各可继承的POM元素的模块以及各个继承模块子POM声明被继承模块父POM的方式实现继承。实现继承既可以各个模块相同配置的重复编写也可以实现项目中各个模块的版本控制。
      ```
      <!-- 父POM -->
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      <!-- 继承项目根POM -->
      <parent>
        <groupId>com.garden</groupId>
        <artifactId>platform-root</artifactId>
        <version>1.0-SNAPSHOT</version>
        <relativePath>../pom.xml</relativePath>
      </parent>
      
      <artifactId>dependency-center</artifactId>
      <version>1.0-SNAPSHOT</version>
      <packaging>pom</packaging>
      
      <name>dependency-center</name>
      
      </project>
      <!-- 子POM -->
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      <!-- 继承项目依赖中心模块POM -->
      <parent>
        <groupId>com.garden</groupId>
        <artifactId>dependency-center</artifactId>
        <version>1.0-SNAPSHOT</version>
        <relativePath>../dependency-center/pom.xml</relativePath>
      </parent>

      <artifactId>register-center</artifactId>

      <version>1.0-SNAPSHOT</version>
      <packaging>jar</packaging>

      <name>register-center</name>

      </project>
      ```
    * 可继承的POM元素
      * groupId，项目组ID，项目坐标的核心元素。
      * version，项目版本，项目坐标的核心元素。
      * description，项目的描述信息。
      * organization，项目的组织信息。
      * inception Year，项目的创始年份。
      * url，项目的URL地址。
      * developers，项目的开发者信息。
      * contributors，项目的贡献者信息。
      * distributionManagement，项目的部署配置。
      * issueManagement，项目的缺陷跟踪系统信息。
      * scm，项目的版本控制系统信息。
      * maillingLists，项目的邮件列表信息。
      * **properties**，自定的Maven属性（Java环境属性）。
      * **dependencies**，项目的依赖配置，父POM以及子POM都会引入依赖。
      * **dependencyManagement**，项目的依赖管理配置，父POM不会引入依赖，子POM可根据实际需要进行声明将依赖引入。
      * **repositories**，项目的仓库配置。
      * **build**，包括项目的源码目录配置，输出目录配置，**插件配置**，**插件管理配置**等。
      * reporting，包括项目的报告输出目录配置，报告插件配置等。
    * 依赖管理元素
      * 为了保证各个子POM的灵活性（不强制各个子POM都继承父POM的依赖）以及各个子POM的依赖版本统一控制，推荐在父POM中使用dependencyManagement元素。 
        ```
        <!-- 父POM -->
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

        <modelVersion>4.0.0</modelVersion>

        <!-- 继承项目根POM -->
        <parent>
          <groupId>com.garden</groupId>
          <artifactId>platform-root</artifactId>
          <version>1.0-SNAPSHOT</version>
          <relativePath>../pom.xml</relativePath>
        </parent>
      
        <artifactId>dependency-center</artifactId>
        <version>1.0-SNAPSHOT</version>
        <packaging>pom</packaging>
      
        <name>dependency-center</name>
        
        <properties>
          <spring-boot.version>2.1.6.RELEASE</spring-boot.version>
        </properties>

        <dependencyManagement>
        <dependencies>
            <!--spring boot 依赖包版本控制-->
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring-boot.version}</version>
                <!-- 类型为pom以及依赖范围为import表示 -->
                <!-- 将spring-boot-dependencies的pom的dependencyManagement导入并合并 -->
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
        </dependencyManagement>

        </project>
        <!-- 子POM -->
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

        <modelVersion>4.0.0</modelVersion>

        <!-- 继承项目依赖中心模块POM -->
        <parent>
          <groupId>com.garden</groupId>
          <artifactId>dependency-center</artifactId>
          <version>1.0-SNAPSHOT</version>
          <relativePath>../dependency-center/pom.xml</relativePath>
        </parent>

        <artifactId>register-center</artifactId>

        <version>1.0-SNAPSHOT</version>
        <packaging>jar</packaging>

        <name>register-center</name>

        <!-- 使用groupId与artifactId声明引入父类Spring Security -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>

        </project>
        ```
    * 插件管理元素
      * 该元素（pluginManagement）在父POM中配置的插件不会造成实际的插件调用行为，当在子POM中使用groupId与artifactId声明插件时才会影响实际的插件行为。
      * 为了保证各个子POM的灵活性（不强制各个子POM都继承父POM的插件）以及各个子POM的插件版本统一控制，推荐在父POM中使用pluginManagement元素。 
        ```
        <!-- 父POM -->
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

        <modelVersion>4.0.0</modelVersion>

        <!-- 继承项目根POM -->
        <parent>
          <groupId>com.garden</groupId>
          <artifactId>platform-root</artifactId>
          <version>1.0-SNAPSHOT</version>
          <relativePath>../pom.xml</relativePath>
        </parent>
      
        <artifactId>dependency-center</artifactId>
        <version>1.0-SNAPSHOT</version>
        <packaging>pom</packaging>
      
        <name>dependency-center</name>
        
        <build>
          <pluginManagement>
            <plugins>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-source-plugin<artifactId>
                <version>2.1.1</version>
                <executions>
                  <execution>
                    <id>attach-source</id>
                    <phase>verify</phase>
                    <goals>
                      <goal>jar-no-fork</goal>
                    </goals>
                  </execution>
                </executions>
              <plugin>
            </plugins>
          </pluginManagement>
        </build>

        </project>
        <!-- 子POM -->
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

        <modelVersion>4.0.0</modelVersion>

        <!-- 继承项目依赖中心模块POM -->
        <parent>
          <groupId>com.garden</groupId>
          <artifactId>dependency-center</artifactId>
          <version>1.0-SNAPSHOT</version>
          <relativePath>../dependency-center/pom.xml</relativePath>
        </parent>

        <artifactId>register-center</artifactId>

        <version>1.0-SNAPSHOT</version>
        <packaging>jar</packaging>

        <name>register-center</name>

        <build>
          <plugins>
            <plugin>
              <groupId>org.apache.maven.plugins</groupId>
              <artifactId>maven-source-plugin<artifactId>
            <plugin>
          </plugins>
        </build>

        </project>
        ```
  * 聚合与继承的关系
    * 聚合是为了方便快速构建项目，继承是为了消除重复配置，两者之间没有必然联系，实际Maven开发中可以将聚合模块与父POM模块结合一起，这样可以解决聚合时子模块不知聚合模块以及继承时父POM不知子POM的问题。
      ```
      <!-- 聚合模块（父POM） -->
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      
      <artifactId>platform-root-dependency</artifactId>
      <version>1.0-SNAPSHOT</version>
      <packaging>pom</packaging>
      
      <name>platform-root-dependency</name>
      
      <!-- 聚合的模块 -->
      <modules>
        <!-- 相对于当前POM文件的各子模块的POM文件路径 -->
        <module>platform-dependency</module>
        <module>platform-register</module>
        <module>platform-business</module>
        <module>platform-banner</module>
        <module>platform-sdk</module>
      </modules>

      <!-- 继承的元素  -->  
      <properties>
        <spring-boot.version>2.1.6.RELEASE</spring-boot.version>
      </properties>

      <dependencyManagement>
      <dependencies>
          <!--spring boot 依赖包版本控制-->
          <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-dependencies</artifactId>
              <version>${spring-boot.version}</version>
              <!-- 类型为pom以及依赖范围为import表示 -->
              <!-- 将spring-boot-dependencies的pom的dependencyManagement导入并合并 -->
              <type>pom</type>
              <scope>import</scope>
          </dependency>
      </dependencies>
      </dependencyManagement>

      </project>
      <!-- 子模块（子POM） -->
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      <!-- 继承聚合模块POM -->
      <parent>
        <groupId>com.garden</groupId>
        <artifactId>platform-root-dependency</artifactId>
        <version>1.0-SNAPSHOT</version>
        <!-- 可以不指定 默认相对路径为../pom.xml -->
        <relativePath>../pom.xml</relativePath>
      </parent>

      <artifactId>register-center</artifactId>

      <version>1.0-SNAPSHOT</version>
      <packaging>jar</packaging>

      <name>register-center</name>

      <!-- 使用groupId与artifactId声明引入父类Spring Security -->
      <dependency>
          <groupId>org.springframework.boot</groupId>
          <artifactId>spring-boot-starter-security</artifactId>
      </dependency>

      </project>
      ```
  * 约定优于配置
    * 约定优于配置是Maven最核心的设计理念之一。Maven用户遵循约定，可减少开发重复配置。
    * Maven约定体现在超级POM，所有POM必须继承超级POM，超级POM约定规则其子POM继承并使用其约定。对于Maven3，超级POM位于$MAVEN_HOME/lib/maven-model-builder-x.x.x.jar中的org/apache/maven/model/pom-4.0.0.xml路径下。
      * 超级POM约定依赖和插件远程仓库

        ![超级POM约定依赖和插件远程仓库.png](https://i.loli.net/2020/03/02/i1QTJXhO57ANjEH.png)

      * 超级POM约定插件
      
        ![超级POM约定插件.png](https://i.loli.net/2020/03/02/2lTWxv9NmX63PRg.png)
      
  * 反应堆
    * 在多模块项目中，反应堆是所有模块组成的一个构建结构.
    * 反应堆构建顺序
      * 以根POM声明的模块顺序为准,若遇到模块中存在继承或者依赖关系,由先构建被继承或者被依赖模块。
      
        ![反应堆优先构建被继承或被依赖模块.png](https://i.loli.net/2020/03/02/W4SqwzlFifkNoCK.png)

    * 剪裁反应堆
      * 为了解决完整反应堆构建中只需构建某个模块的需求，Maven提供了裁剪反应堆的命令行实现。以如下完整的反应堆为例：
          
          ![完整的反应堆例子.png](https://i.loli.net/2020/03/02/ARd6gphEwWXNZfQ.png)
        
        * 使用-pl选项指定构建某几个模块
          ```
          $ mvn clean install -pl account-email,account-persist
          ```

          ![使用-pl选项指定构建某几个模块.png](https://i.loli.net/2020/03/02/Eubio2O81LfU3Pt.png)

        * 使用-am选项同时构建所列模块的依赖模块
          ```
          $ mvn clean install -pl account-email -am
          ```
          
          ![使用-am选项同时构建所列模块的依赖模块.png](https://i.loli.net/2020/03/02/HMJbrzEpFnUOxjL.png)

        * 使用-amd选项同时构建依赖于所列模块的模块 
          ```
          $ mvn clean install -pl account-parent -amd
          ```
          ![使用-amd选项同时构建依赖于所列模块的模块.png](https://i.loli.net/2020/03/02/Fr7hbmsdk6Ey8gf.png)

        * 使用-rf选项可以在完整的反应堆构建顺序基础上指定从哪个模块开始构建
          ```
          $ mvn clean install -rf account-email
          ```
          
          ![使用-rf选项可以在完整的反应堆构建顺序基础上指定从哪个模块开始构建.png](https://i.loli.net/2020/03/02/yojsGPDtdquvfiV.png)
        
        * 四个选项可复合使用。
        * 一般用于庞大的，特别多模块的项目构建。







