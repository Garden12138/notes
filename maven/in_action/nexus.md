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
    * 验证安装
      ```
      ## Bundle方式
      http://localhost:8081/nexus/
      ## war方式
      http://localhost:8080/nexus/
      ```  
  * Nexus的仓库与仓库组
  * Nexus的索引与构建搜索
  * 配置Maven从Nexus下载构件
  * 部署构件至Nexus
  * Nexus的权限管理
  * Nexus的调度任务
  * 其他私服软件