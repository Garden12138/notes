## Maven in action
#### 坐标和依赖
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