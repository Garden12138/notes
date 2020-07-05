## Maven in action
#### Nexus
> Nexus
  * Nexus简介
    * 背景，在实际开发中，可通过建立私服，可以降低中央仓库负荷，节省外网带宽，加速Maven构建，部署自定义构件等，最常使用Maven仓库管理软件Nexus建立私服。
    * Nexus开源版本特性
      * 较小内存占用
      * 基于ExtJS的友好界面
      * 基于Restlet的完全REST API
      * **支持代理仓库，宿主仓库和仓库组**
      * **基于文件系统，不需数据库**
      * **支持仓库索引和搜索**
      * **支持从界面上传Maven构件**
      * 细粒度的安全控制
  * 安装Nexus
    * Nexus是Java Web应用，有两种安装包分别是包含Jetty容器的Bundle包和不包含Web容器的war包。
    * 下载Nexus
      * [官网下载Bundle包或war包](https://www.sonatype.com/nexus-repository-oss)
    * Bundle方式安装Nexus
      * 解压压缩包至目标目录
      * 执行nexus-webapp-x.x.x/目录下的启动脚本
    * war方式安装Nexus
      * 解压压缩包至目标目录
      * 将解压后文件放至Tomcat的webapp下，启动Tomcat
    * [docker方式安装Nexus](https://hub.docker.com/r/sonatype/nexus3)
      * 拉取sonatype/nexus3镜像
        ```
        docker pull sonatype/nexus3
        ```
      * 运行nexus容器
        ```
        docker run -d -p 8081:8081 --name nexus sonatype/nexus3
        ```
    * 验证安装
      ```
      ## Bundle方式
      http://localhost:8081/nexus/
      ## war方式
      http://localhost:8080/nexus/
      ```  
  * Nexus的仓库与仓库组
    * Nexus内置的仓库
      * 点击界面Repositories列表将展示所有类型的Nexus仓库，Name表示仓库名称，Type表示仓库类型(proxy为代理，hosted为宿主，group为仓库组)，Format表示仓库格式，Policy为策略(Release表示发布版本仓库，Snapshot表示快照版本)，Status表示状态，URL表示路径。
    * Nexus仓库分类概念
      
      ![各种类型的Nexus仓库.png](https://i.loli.net/2020/03/19/PgoT7JLEFWeabZ3.png)

      Maven可直接从宿主仓库下载构件；Maven也可以从代理仓库下载构件，代理仓库会间接从远程仓库下载并缓存构件；Maven可以从仓库组下载构件，仓库组没有实际内容，它会转向其包含的宿主仓库或者代理仓库获得实际构件的内容。

    * 创建Nexus宿主仓库
      * 点击Repositories，选择Create Repository maven2(hosted)
      * 设置仓库名称Name
      * 设置版本策略Version policy
      * 设置部署策略Deployment policy

      ![SonaType Nexus Repository Manager Create Hosted Repo.png](https://i.loli.net/2020/03/19/cDtP8IH2VYerQJv.png)
      
    * 创建Nexus代理仓库
      * 点击Repositories，选择Create Repository maven2(proxy)
      * 设置仓库名称Name
      * 设置版本策略Version policy
      * 设置代理配置Proxy

      ![SonaType Nexus Repository Manager Create Proxy Repo.png](https://i.loli.net/2020/03/19/mH647PC5gElA1uT.png)

    * 创建Nexus仓库组
      * 点击Repositories，选择Create Repository maven2(proxy)
      * 设置仓库名称Name
      * 设置组配置Group

      ![SonaType Nexus Repository Manager Create Group Repo.png](https://i.loli.net/2020/03/19/u6Xr8ckdgTRGLVe.png)

  * Nexus的索引与构建搜索
  * 配置Maven从Nexus下载构件
    * 当前项目从Nexus下载构件

      ```
      # 在当前项目POM文件中配置仓库和插件仓库
      <project>
      ...
          <repositories>
              <repository>
                  <id>garden-public</id>
                  <name>garden-public</name>
                  <url>http://localhost:9091/repository/garden-public/</url>
                  <releases><enable>true</enable></releases>
                  <snapshots><enable>true</enable></snapshots>
              </repository>
          </repositories>
          <pluginRepositories>
              <pluginRepository>
                  <id>garden-public</id>
                  <name>garden-public</name>
                  <url>http://localhost:9091/repository/garden-public/</url>
                  <releases><enable>true</enable></releases>
                  <snapshots><enable>true</enable></snapshots>
              </pluginRepository>
          </pluginRepositories>
      ...
      </project>
      ```

    * 全局项目从Nexus下载构件

      ```
      # 在Maven的settings文件里的profile属性配置仓库和插件仓库
      <settings>
      ...
          <profiles>
              <profile>
                  <id>garden-public</id>
                  <repositories>
                  <repository>
                      <id>garden-public</id>
                      <name>garden-public</name>
                      <url>http://localhost:9091/repository/garden-public/</url>
                      <releases><enable>true</enable></releases>
                      <snapshots><enable>true</enable></snapshots>
                  </repository>
                  </repositories>
                  <pluginRepositories>
                  <pluginRepository>
                      <id>garden-public</id>
                      <name>garden-public</name>
                      <url>http://localhost:9091/repository/garden-public/</url>
                      <releases><enable>true</enable></releases>
                      <snapshots><enable>true</enable></snapshots>
                  </pluginRepository>
                  </pluginRepositories>
              </profile>
          </profiles>
          <activeProfiles>
              <activeProfile>garden-public</activeProfile>
          </activeProfiles>
      ...
      </settings>
      # 配置私服镜像，将对所有仓库的下载构件请求转移至私服Nexus，避免请求绕过私服，请求其他仓库
      <settings>
      ...
      <mirrors>
          <mirror>
              <id>garden-public-mirror</id>
              <mirrorOf>*<mirrorOf>
              <url>http://localhost:9091/repository/garden-public/</url>
          </mirror>
      </mirrors>
      ...
      </settings>
      ```

  * 部署构件至Nexus
    * 使用Maven部署构件

      ```
      # 项目POM文件声明私有仓库地址
      <distributionManagement>
		  <!-- 声明私有仓库 快照版本-->
		      <repository>
              <!-- 与settings.xml文件的 server id 保持一致 -->
			        <id>garden-snapshots</id>
			        <name>garden-snapshots</name>
			        <url>http://localhost:9091/repository/garden-snapshots/</url>
		      </repository>
	    </distributionManagement>
      # Maven配置文件settings.xml声明私有仓库地址
      <servers>
          <server>
              <id>garden-snapshots</id>
              <username>admin</username>
              <password>gardem520</password>
          </server>
      </servers>
      # 执行Maven命令 部署构件
      mvn clean deploy -Dmaven.test.skip=true
      ```

    * WEB端部署构件

      ```
      # 执行Maven打包命令 打包构件
      mvn clean install -Dmaven.test.skip=true
      # 使用WEB端Upload功能上传构件
      ```
      
      ![Snipaste_2020-07-05_14-07-19.png](https://i.loli.net/2020/07/05/5nKNgaQIWom3rPZ.png)

  * Nexus的权限管理
  * Nexus的调度任务
  * 其他私服软件