## Maven in action
#### 仓库
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
    * 1）检查依赖范围，若依赖范围为system时，Maven直接从指定路径的文件系统解析构件。
    * 2）根据依赖坐标计算仓库路径，尝试从本地仓库寻找构件，如果发现构件则解析成功。
    * 3）若在本地仓库查找不到相应构件，检查依赖版本是否为显示发布版本（如1.0.0），若是则遍历所有远程仓库，查找下载并解析使用。
    * 4）若检查依赖版本为RELEASE或LATEST，则基于更新策略读取所有远程仓库的元数据（groupId/artifacrId/maven-metadata.xml）,将于本地仓库的对应元数据合并之后，计算出RELEASE或LATEST真实值，最后根据真实值检查本地仓库和远程仓库。
    * 5）若检查依赖版本为SNAPSHOT，则基于更新策略读取所有远程仓库的元数据（groupId/artifacrId/version/maven-metadata.xml），将于本地仓库的对应元数据合并之后，计算最新快照版本值，最后根据真实值检查本地仓库和远程仓库。
    * 6）若检查依赖版本为时间戳格式（2.0-20200202.202020-20），则替换为非时间戳格式SNAPSHOT。
      
      ![Maven依赖解析机制.jpg](https://i.loli.net/2020/02/12/XoxyR15u9tFOr8A.png)

  * 镜像
    * 仓库X可提供仓库Y存储的所有内容，则X为Y的一个镜像。常见Maven使用者会使用稳定快速的镜像源代替中央远程仓库，或组织内使用私服进行项目开发，会将私服作为组织内Maven使用者的镜像。
    * 稳定快速的镜像源代替中央远程仓库，在settings.xml文件中添加镜像配置。
      ```
      <mirrors>
        <mirror>
          <!-- 镜像唯一ID，阿里云Maven中央仓库 -->
          <id>alimaven-central</id>
          <!-- 作为中央远程仓库的镜像，中央远程仓库请求转发至该镜像 -->
          <mirrorOf>central</mirrorOf>
          <!-- 镜像名称，阿里云Maven -->
          <name>aliyun maven</name>
          <!-- 镜像URL，阿里云Maven仓库地址 -->
          <url>http://maven.aliyun.com/nexus/content/repositories/central/</url>
        </mirror>
      <mirrors>  
      ```
    * 将私服作为组织内Maven使用者的镜像，在settings.xml文件中添加镜像配置
      ```
      <mirrors>
        <mirror>
          <!-- 镜像唯一ID，私服仓库 -->
          <id>internal-repository</id>
          <!-- 作为中央远程仓库的镜像，所有远程仓库请求转发至该镜像 -->
          <mirrorOf>*</mirrorOf>
          <!-- 镜像名称，私服Maven -->
          <name>internal Repository Manager</name>
          <!-- 镜像URL，私服Maven仓库地址 -->
          <url>http://39.108.168.201/maven2</url>
        </mirror>
      <mirrors>
      ```
    * mirrorOf元素用法
      ```
      ## 匹配所有远程仓库
      <mirrorOf>*</mirrorOf>
      ## 匹配所有远程仓库，本地远程仓库除外
      <mirrorOf>external:*</mirrorOf>
      ## 匹配仓库repo1，仓库repo2，使用逗号分隔多个远程仓库
      <mirrorOf>repo1,repo2</mirrorOf>
      ## 匹配所有远程仓库，仓库repo1除外，使用感叹号将仓库从匹配中排除
      <mirrorOf>*,!repo1</mirrorOf>
      ```
  * 仓库搜索服务
    * 使用Maven进行日常开发会遇到寻找依赖的问题，此时需要一些仓库搜索服务帮助开发搜索定位依赖坐标。
    * 常见的仓库搜索服务
      * [MVNRepository](https://mvnrepository.com/)
      * [SonaType Nexus](https://repository.sonatype.org/)  