## Maven in action
#### 插件
> 插件
  * 插件目标
    * 对于插件本身，为了能够完成多个任务实现了多个功能，这些功能聚集在一个插件里，每个功能就是一个插件目标。
    * 插件目标的表示方式为插件前缀名:插件目标，如dependency:analyze，dependency:tree，dependency:list为maven-dependency-plugin插件的多个目标。
  * 插件绑定
    * Maven的生命周期的阶段与插件互相绑定，用以完成实际的构建任务。例如项目编译任务，对应default生命周期的compile这阶段，maven-compiler-plugin这一插件的compile目标能够完成该任务。
      ![Snipaste_2020-02-15_18-35-30.png](https://i.loli.net/2020/02/15/wsYalUr6W1kCRuq.png)
    * 内置绑定，为了能让用户几乎不用任何配置就能构建Maven项目，Maven在核心为一些主要的生命周期阶段绑定了核心插件的目标，当用户通过命令行调用生命周期阶段时，对应的插件就会执行完成相应任务。
      * clean生命周期各阶段的内置绑定。

        ![clean生命周期各阶段的内置绑定.png](https://i.loli.net/2020/02/16/rZhaMvGDjAS1Y65.png)、

      * default生命周期各阶段的内置绑定（如JAR打包类型），由于不同打包类型其default生命周期各阶段也各不一样，故该内置绑定与打包类型相关。

        ![default生命周期各阶段的内置绑定（如JAR打包类型）.png](https://i.loli.net/2020/02/16/78M2hYgsJSBWCGE.png)

      * site生命周期各阶段的内置绑定。

        ![site生命周期各阶段的内置绑定.png](https://i.loli.net/2020/02/16/R2dKjMfN8Uq56vB.png)

    * 自定义绑定，除了内置绑定外，用户可选择将某个插件目标绑定到生命周期的某个阶段完成某个任务。例如，打包项目源码jar包。
      ```
      ### 打包项目源码jar包
      <build>
        <plugins>
          <plugin>
            <!-- 插件（构件）坐标 -->
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-source-plugin</artifactId>
            <version>2.1.1</version>
            <executions>
              <execution>
                <!-- 插件目标任务id -->
                <id>attach-sources</id>
                <!-- 生命周期阶段名称，可不指定，大多数插件目标默认绑定生命周期阶段 -->
                <!-- 可使用maven-help-plugin查看插件详细信息 -->
                <phase>verify</phase>
                <!-- 插件目标名称 -->
                <goals>
                  <goal>jar-no-fork</goal>
                </goals>
              </execution>
            </executions>
          </plugin>
        </plugins>
      </build>
      ```
  * 插件配置
    * 用户可通过设置插件参数，调整插件目标所执行的任务。插件参数配置可通过命令行输入和POM文件配置的方式实现。
    * 命令行输入，适用于常变化的参数设置，用户可通过Maven命令带上-Dkey=value格式设置，如下载项目输出构件时跳过测试阶段
      ```
      ## 参数-D为Java自带参数，其设置一个Java系统属性，Maven在准备插件时检查系统属性并使用该属性设置插件跳过测试阶段。
      mvn install -Dmaven.test.skip=true
      ```
    * POM文件配置，适用于不常变化的参数设置，用户可通过在POM文件编辑plugin元素及其子元素设置，可分为全局配置与特定配置，全局配置如配置maven-compiler-plugin使用JDK1.8，特定配置如为validate，verify阶段添加特定任务。
      ```
      ## 配置maven-compiler-plugin使用JDK1.8
      <build>
        <plugins>
          <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>2.1</version>
            <configuration>
              <source>1.8</source>
              <target>1.8</target>
            </configuration>
          </plugin>
        </plugins>
      </build>
      ## 为validate，verify阶段添加特定任务
      <build>
        <plugins>
          <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-antrun-plugin</artifactId>
            <version>1.3</version>
            <executions>
              <execution>
                <id>ant-validate</id>
                <phase>validate</phase>
                <goals>
                  <goal>run</goal>
                </goals>
                <configuration>
                  <tasks>
                    <echo>starting validate...</echo>
                  </tasks>
                </configuration>
              </execution>
              <execution>
                <id>ant-verify</id>
                <phase>verify</phase>
                <goals>
                  <goal>run</goal>
                </goals>
                <configuration>
                  <tasks>
                    <echo>starting verify...</echo>
                  </tasks>
                </configuration>
              </execution>
            </executions>
          </plugin>
        </plugins>
      </build>
      ```
  * 获取插件信息
    * 寻找合适的插件可正确配置插件，寻找插件的方式主要为在线查找插件信息或者使用maven-help-plugin插件查找插件描述。
    * 在线查找插件信息
      * [稳定的Apache官方插件](https://maven.apache.org/plugins/index.html)
    * 使用maven-help-plugin查找插件描述
      * 命令格式为mvn help: describe-Dplugin = groupId: artifactId: version
        ```
        ## 获取maven-compiler-plugin2.1版本的信息
        mvn help: describe-Dplugin = org.apache.maven.plugins: maven-compiler-plugin: 2.1
        ## 获取maven-compiler-plugin最新版本的信息
        mvn help: describe-Dplugin = org.apache.maven.plugins: maven-compiler-plugin
        ## 使用目标前缀获取maven-compiler-plugin最新版本的信息
        mvn help: describe-Dplugin = compiler
        ## 使用目标前缀获取maven-compiler-plugin最新版本compile目标的信息
        mvn help: describe-Dplugin = compiler -Dgoal = compile
        ## 使用目标前缀获取maven-compiler-plugin最新版本compile目标的x详细信息
        mvn help: describe-Dplugin = compiler -Dgoal = compile -Ddetail
        ```
  * 从命令行调用插件
  * 插件解析机制