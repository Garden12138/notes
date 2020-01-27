## Maven in action
> 什么是Maven
  * Maven是一跨平台的项目管理工具，主要服务于Java平台的项目信息管理，依赖管理以及项目构建（源代码编译，单元测试运行，文档生成，打包部署这些流水线示软件步骤为构建）。
  * Maven可作为构建工具，抽象构建过程，提供构建实现，可跨平台的实现自动化构建。
  * Maven可作为依赖管理工具，可通过坐标定位类库并引入。
  * Maven可作为项目信息管理工具，可管理项目描述，开发者列表，版本控制系统地址，许可证，缺陷管理系统地址等。还可获取项目文档，测试报告，静态分析报告，源码版本日志报告。
> Maven安装与配置
  * Window
    ```
    # 检查JDK，如果不存在则需优先安装JDK，Maven运行依赖JDK
    java -version
    # 下载Maven，前往官网下载对应操作系统压缩包
    http://maven.apache.org/download.html
    # 本地安装，将安装文件解压至指定目录，新增系统环境变量M2_HOME，赋值Maven解压安装目录，更新系统环境变量Path，在变量值最末尾添加%M2_HOME%\bin;
    # 检查Maven安装是否成功
    mvn -v
    # 升级Maven，下载安装新版本Maven，系统环境变量值更改为最新版本Maven安装目录
    ```
  * Unix
    ```
    # 检查JDK
    java -version
    # 下载Maven
    cd /usr/local
    mkdir maven
    wget https://mirrors.tuna.tsinghua.edu.cn/apache-maven-3.6.3-bin.tar.gz
    # 本地安装
    tar -zxvf apache-maven-3.6.3-bin.tar.gz -C .
    vim /etc/profile
    MAVEN_HOME=/usr/local/maven/apache-maven-3.6.3
    export MAVEN_HOME
    PATH=$MAVEN_HOME/bin:$PATH
    export PATH
    source /etc/profile
    # 检查Maven安装是否成功
    mvn -v
    # 升级Maven，与Windows原理一致
    ```
> 安装目录分析
  * bin
    ```
    mvn: 基于Unix的shell脚本，配置Java命令，准备classpath和Java系统属性后执行Java命令。
    mvn.cmd: 基于Windows的cmd脚本，作用同mvn。
    mvnDebug: 基于Unix的shell脚本，使用Debug模式配置Java命令，准备classpath和Java系统属性后执行Java命令。
    mvnDebug.cmd: 基于Windows的cmd脚本，作用同mvnDebug。
    m2.conf: classworlds的配置文件。
    mvnyjp: shell脚本，用于分析Maven构建过程。
    ```
  * boot
    ```
    plexus-classworlds: 是一个类加载器框架，Maven使用该框架加载自己的类型。详细参考http://classworlds.codehanus.org/
    ```
  * conf
    ```
    settins.xml: 直接修改该文件，在机器上全局定制Maven行为。一般情况下，更倾向Copy该文件至~/.m2/repository/，然后修改该文件，在用户范围内全局定制Maven行为。
    ```
  * lib
    ```
    该目录包含所有Maven运行时需要的Java类型。
    ```
  * LICENSE
    ```
    该文件记录了Maven使用的软件许可证Apache License Version 2.0
    ```
  * NOTICE
    ```
    该文件记录了Maven包含的第三方软件。
    ```
  * README.txt
    ```
    该文件包含了Maven的简要介绍，包括安装需求及如何安装的简要指令等。
    ```
  * ~/.m2
    ```
    该目录包含repository目录，放置Maven本地仓库，所有的Maven构件都存储在该仓库。
    ```