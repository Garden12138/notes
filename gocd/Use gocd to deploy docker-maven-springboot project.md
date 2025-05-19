## 使用 gocd 部署 docker-maven 打包方式的 springboot 工程

> 准备工作

* [```docker-maven```打包方式的```springboot```工程](https://gitee.com/FSDGarden/elasticjob-lite-backend.git)

> 创建工程构建管道

* 设置材料配置

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_20-51-42.png)

* 设置管道配置

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_20-59-10.png)

> 创建构建阶段
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-02-59.png)

> 创建打包与推送工作
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-12-44.png)

* 创建打包任务

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-17-51.png)

* 创建登录镜像仓库以及推送镜像任务

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/WechatIMG108.png)


> 创建部署阶段
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-27-10.png)
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-28-06.png)

> 创建拉取与运行工作

* 创建拉取工程镜像任务

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-32-34.png)

* 创建运行工程容器任务

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-33-25.png)

> 注意事项

* 设置环境变量。管道、阶段以及工作皆可设置环境变量，本文所使用环境变量设置于管道中，文本信息设置在```Plain Text Variables```中，密码等敏感信息设置在```Secure Variables```中：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-38-46.png)

* 设置任务配置。本文所使用的任务类型包含初始的客户端命令以及安装的插件命令：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-09_21-44-44.png)
 
> 参考文献

* [GoCD 整行记（三）：创建流水线](https://www.jianshu.com/p/4711f9781aa1)

* [GoCD 整行记（四）：配置流水线](https://www.jianshu.com/p/27cb772dd35f)

* [GoCD 整行记（五）：部署应用](https://www.jianshu.com/p/79e829fdb2a1)

* [Step-by-step guide to your first pipeline](https://www.gocd.org/getting-started/part-1/)

* [script-executor-task](https://github.com/gocd-contrib/script-executor-task)