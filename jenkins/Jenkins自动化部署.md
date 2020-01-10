## 安装Jenkins
> **本文使用的是Docker版本的Jenkins**
* 拉取Docker仓库的Jenkins镜像
  ```
  docker pull jenkins/jenkins
  ```
* 运行Jenkins容器
  ```
  docker run -d -u root -p 9999:8080 -v /var/jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock -v "$HOME":/home -v /etc/localtime:/etc/localtime --name jenkins jenkins/jenkins
  ```
* 浏览器输入Jenkins应用地址（IP为示例服务器IP）
  ```
  http://39.108.168.201:9999
  ```
* 获取管理员初始化密码，输入登录页面中
  ```
  tail /var/jenkins_home/secrets/initialAdminPassword
  ```
* 安装推荐插件（需翻墙安装）
* 创建管理员账户
* 配置全局安全配置，取消勾选跨站请求伪造保护
  ![Snipaste_2019-12-30_10-36-00.png](https://i.loli.net/2019/12/30/Z3OgFabAIzYrNfe.png)
  ![Snipaste_2019-12-30_10-38-13.png](https://i.loli.net/2019/12/30/V1nQGarJxwWZKvF.png)

## Docker发布SpringBoot应用
* 插件管理
  * 安装mvn插件
    ![Snipaste_2019-12-30_10-47-07.png](https://i.loli.net/2019/12/30/fgJ3ABt2KsDSWzP.png)
* 全局工具配置
  * Maven配置，优先在宿主机对应Jenkins容器挂载的文件目录下，安装Maven
    ```
    # 进入挂载文件目录
    cd /var/jenkins_home/maven
    # 下载Maven压缩包
    wget https://mirrors.tuna.tsinghua.edu.cn/apache-maven-3.6.3-bin.tar.gz
    # 解压Maven压缩包
    tar -zxvf apache-maven-3.6.3-bin.tar.gz -C .
    # 宿主机配置Maven环境变量【可不配置】
    vim /etc/profile
    MAVEN_HOME=/var/jenkins_home/maven/apache-maven-3.6.3
    export MAVEN_HOME
    PATH=$MAVEN_HOME/bin:$PATH
    export PATH
    source /etc/profile
    # Jenkis配置Maven环境变量，由于Jenkins在使用mvn时候是no-login方式，所以source刷新环境变量不生效，解决这个问题可以在获取官方Jenkins镜像的基础上指定Maven环境构建新的镜像或者在Jenkin上指定全局变量值（下面采用这种方式）
    # docker -exec -it jenkins /bin/bash
    # apt-get update
    # apt-get install vim
    # vim /etc/profile
    # MAVEN_HOME=/var/jenkins_home/maven/apache-maven-3.6.3
    # export MAVEN_HOME
    # PATH=$MAVEN_HOME/bin:$PATH
    # export PATH
    # source /etc/profile
    ```
    ![Snipaste_2019-12-30_10-52-11.png](https://i.loli.net/2019/12/30/Xo86CJtgnUE59ms.png)
    ![Snipaste_2019-12-30_11-12-56.png](https://i.loli.net/2019/12/30/pGxTRZQAY7cVtmz.png)
  * JDK配置，选择自动安装方式
    ![Snipaste_2019-12-30_11-17-59.png](https://i.loli.net/2019/12/30/L8WDamdco9Qikgr.png)
  * Git配置，选择自动安装方式
    ![Snipaste_2019-12-30_11-20-14.png](https://i.loli.net/2019/12/30/xlH5SGFLAt4EkaK.png)
* 系统管理
  * 设置maven全局属性
    ![Snipaste_2019-12-30_13-32-06.png](https://i.loli.net/2019/12/30/KUg2OE7FbvLfH4P.png)
  * 设置SSH服务器配置
    ![Snipaste_2019-12-30_13-36-00.png](https://i.loli.net/2019/12/30/Ir2mSM5OXl4KnEJ.png)
* 新建任务
  * 创建流水线
    ![Snipaste_2019-12-30_13-38-08.png](https://i.loli.net/2019/12/30/sSo915TbJECdQkI.png)
  * 配置流水线
    ![Snipaste_2019-12-30_13-51-58.png](https://i.loli.net/2019/12/30/5IrhUZXWVd8DGT6.png)
    ![Snipaste_2019-12-30_13-53-11.png](https://i.loli.net/2019/12/30/k4XGAn2IetK31PD.png)
* SpringBoot项目/build/pro/目录下编写JenkinsFile
  ```
  pipeline {
  agent any
  stages {
    stage('compile') {
      steps {
        sh 'mvn clean package -Ppro -Dmaven.test.skip=true'
      }
    }
    
    stage('package') {
      steps {
        sh 'cp target/springboot-0.0.1-SNAPSHOT.jar build/pro/'
      }
    }
    
    stage('node1-deploy') {
      steps {
        sshPublisher(
          continueOnError: false, failOnError: true,
          publishers: [
            sshPublisherDesc(
              configName: "Server1",
              transfers: [
                sshTransfer(
                  sourceFiles: "build/pro/*",
                  removePrefix: "build/pro/",
                  remoteDirectory: "dockerfile/springboot/",
                  execCommand: "cd /data/dockerfile/springboot && chmod a+x run.sh && ./run.sh"
                )
	          ],
	          usePromotionTimestamp: false,
              useWorkspaceInPromotion: false,
              verbose: false
            )
	      ]
	    )
	  }
    }
  } 
  }
  ```
* SpringBoot项目/build/pro/目录下编写DockerFile
  ```
  FROM java:8
  RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
  ADD springboot-0.0.1-SNAPSHOT.jar /app.jar
  EXPOSE 8081
  ENTRYPOINT ["/usr/bin/java","-jar", "-Xmx4g", "-Xms4g", "-Xmn1536m", "-Dspring.profiles.active=pro","app.jar"]
  ```
* SpringBoot项目/build/pro/目录下编写run.sh
* 发布SpringBoot应用
  ![Snipaste_2019-12-30_14-10-22.png](https://i.loli.net/2019/12/30/xEad4lBD9grfmYj.png)

## Nginx发布前端应用
* jenkins安装nodejs插件
  ![Snipaste_2020-01-10_14-14-41.png](https://i.loli.net/2020/01/10/cp3VtzOkaSwQqdA.png)
* jenkins配置nodejs全局工具
  ![Snipaste_2020-01-10_14-14-41.png](https://i.loli.net/2020/01/10/2rHOkZbxiMluRSC.png)
* jenkins系统配置SSH Server
  ![Snipaste_2020-01-10_14-26-20.png](https://i.loli.net/2020/01/10/374qLVZ9vnbyEHe.png)
* 编写jenkins任务
  * 创建自由风格软件项目
    ![Snipaste_2020-01-10_14-30-22.png](https://i.loli.net/2020/01/10/XmlCtFYS5HiTIvQ.png)
  * General设置
    ![General.png](https://i.loli.net/2020/01/10/fhuzkUgmOeG791d.png)
  * 源码管理设置
    ![源码管理.png](https://i.loli.net/2020/01/10/z2NMmVa3FyZixPu.png)
  * 构建环境设置
    ![构建环境.png](https://i.loli.net/2020/01/10/j26Zu8fYtNiKxAW.png)
  * 构建设置
    ![构建.png](https://i.loli.net/2020/01/10/brZx13BSVYdG2eH.png)
  * 构建后操作设置
    ![构建后操作.png](https://i.loli.net/2020/01/10/nhBlDotXPm7Ncax.png)
* 编写nginx转发配置
  * 编写nginx.conf配置文件
    ```
    vim /etc/nginx/nginx.conf
    server {
        listen       3000;
        server_name  front_server_vue-cli-demo;
        index        index.html;
        root         /data/nginxfile/vue-cli-demo;

        location / {
        }
    }
    ```
  * 刷新nginx.conf配置文件
    ```
    nginx -s reload
    ```
  * 重启nginx
    ```
    service nginx restart
    ```
* 浏览器打开前端地址，如http://39.108.168.201:3000/
  ![Snipaste_2020-01-10_14-45-33.png](https://i.loli.net/2020/01/10/hb6NOvPWoC5JsZd.png)


