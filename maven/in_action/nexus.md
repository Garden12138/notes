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
  * 部署构件至Nexus
  * Nexus的权限管理
  * Nexus的调度任务
  * 其他私服软件