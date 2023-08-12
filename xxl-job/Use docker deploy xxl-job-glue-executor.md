## 使用 docker 部署 xxl-job-glue-executor

> 使用自定义镜像部署（本人制作^^）

* 拉取镜像

  ```bash
  docker pull garden12138/xxl-job-glue-executor:2.4.0
  ```

* 运行容器

  ```bash
  docker run --name xxl-job-glue-executor --restart=always -d -e PARAMS="xxl.job.admin.addresses=${XXL_JOB_ADMIN_ADDRESSES} xxl.job.accessToken=${XXL_JOB_ACCESSTOKEN} xxl.job.executor.appname=${XXL_JOB_EXECUTOR_APPNAME} xl.job.executor.ip=${XXL_JOB_EXECUTOR_IP} xxl.job.executor.port=${XXL_JOB_EXECUTOR_PORT}" -p ${XXL_JOB_EXECUTOR_PORT}:${XXL_JOB_EXECUTOR_PORT} garden12138/xxl-job-glue-executor:2.4.0
  ```

  环境变量```${XXL_JOB_ADMIN_ADDRESSES}```为```xxl-job-admin```可访问地址，如```http://114.132.78.39:18081/xxl-job-admin```；环境变量```XXL_JOB_ACCESSTOKEN```为访问```xxl-job-admin```所使用的```token```，如```CsjnD0xFU4JfDjQR23UB7YxGoYVcaRx```；环境变量```${XXL_JOB_EXECUTOR_APPNAME}```为执行器名称，如```xxl-job-glue-executor```；环境变量```XXL_JOB_EXECUTOR_IP```为执行器本身可访问```IP```，如```114.132.78.39```；环境变量```XXL_JOB_EXECUTOR_PORT```为执行器本身可访问端口，如```9999```。

> 在xxl-job-admin上创建且执行执行器的Glue任务

* Java

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-27-49.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-28-32.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-33-35.png)

* Shell

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-38-30.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-39-14.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-39-43.png)

* Python2

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-42-10.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-43-34.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-44-02.png)

* Python3

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-45-25.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-46-19.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-47-02.png)

* PHP

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-49-04.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-51-41.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-52-28.png)

* Nodejs
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-54-09.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-54-47.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-56-25.png)

* PowerShell

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-58-01.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-58-35.png)
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-08-11_15-59-01.png) 

> 注意事项

* [本文所使用的执行器依赖于支持自动注册的```xxl-job-admin```](https://gitee.com/FSDGarden/learn-note/blob/master/xxl-job/Use%20docker%20deploy%20xxl-job-admin.md)，[这是镜像地址](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)。

* 本文所使用的自定义镜像所包含以下开发环境：
  
  * ```JDK 1.8.0_372```
  * ```Python 2.7.5```
  * ```Python3 3.6.8```
  * ```PHP 7.4.33```
  * ```NODEJS v16.20.1```
  * ```PowerShell 7.3.6```  

> 参考文献

* [官方文档](https://www.xuxueli.com/xxl-job/)