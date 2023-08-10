## 使用 docker 部署 xxl-job-glue-executor

> 使用自定义镜像部署（本人制作^^）

* 拉取镜像

  ```bash
  docker pull garden12138/xxl-job-glue-executor:2.4.0
  ```

* 运行容器

  ```bash
  docker run --name xxl-job-glue-executor --restart=always -d -e PARAMS="xxl.job.admin.addresses=${XXL_JOB_ADMIN_ADDRESSES} xxl.job.accessToken=${XXL_JOB_ACCESSTOKEN} xxl.job.executor.ip=${XXL_JOB_EXECUTOR_IP} xxl.job.executor.port=${XXL_JOB_EXECUTOR_PORT}" garden12138/xxl-job-glue-executor:2.4.0
  ```

  环境变量```${XXL_JOB_ADMIN_ADDRESSES}```为```xxl-job-admin```可访问地址，如```http://114.132.78.39:18081/xxl-job-admin```；环境变量```XXL_JOB_ACCESSTOKEN```为访问```xxl-job-admin```所使用的```token```，如```CsjnD0xFU4JfDjQR23UB7YxGoYVcaRx```；环境变量```XXL_JOB_EXECUTOR_IP```为执行器本身可访问```IP```，如```114.132.78.39```；环境变量```XXL_JOB_EXECUTOR_PORT```为执行器本身可访问端口，如```9999```。

> 在xxl-job-admin上创建且执行执行器的Glue任务

* Java
* Shell
* Python
* PHP
* Nodejs
* PowerShell

> 注意事项

* [本文所使用的执行器依赖于支持自动注册的```xxl-job-admin```](https://gitee.com/FSDGarden/learn-note/blob/master/xxl-job/Use%20docker%20deploy%20xxl-job-admin.md)，[这是镜像地址](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)。

* 本文所使用的自定义镜像所包含以下开发环境：
  
  * ```DK 1.8.0_372```
  * ```Python 2.7.5```
  * ```Python3 3.6.8```
  * ```PHP 7.4.33```
  * ```NODEJS v16.20.1```
  * ```PowerShell 7.3.6```  

> 参考文献

* [官方文档](https://www.xuxueli.com/xxl-job/)