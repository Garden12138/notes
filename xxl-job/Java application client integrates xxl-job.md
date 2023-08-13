## Java应用客户端集成 xxl-job

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

* ```Bean```类型任务。

> 新增配置文件 xxl-job-executor.properties 并设置

> 新增配置累 XxlJobConfig

> main 方法编写启动 xxl-job-executor 逻辑

> 注意事项

* 本文所指的```xxl-job-admin```自定义镜像[在这](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)