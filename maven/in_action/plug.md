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
  * 获取插件信息
  * 从命令行调用插件
  * 插件解析机制