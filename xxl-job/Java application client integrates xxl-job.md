## Java应用客户端集成 xxl-job

> 引入 xxl-job-core maven 依赖

* 引入官方依赖，可根据需求选择对应版本。

* 引入自定义依赖，若需实现执行器组的动态更新且```xxl-job-admin```使用自定义镜像，则可选择引入，目前只支持```2.4.0```。

> 编写任务

* ```Glue```类型任务，使用方式可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/xxl-job/Use%20docker%20deploy%20xxl-job-glue-executor.md)或[官方文档](https://www.xuxueli.com/xxl-job/)。

* ```Bean```类型任务。

> 新增配置文件 xxl-job-executor.properties 并设置

> 新增配置累 XxlJobConfig

> main 方法编写启动 xxl-job-executor 逻辑

> 注意事项

* 本文所指的```xxl-job-admin```自定义镜像[在这](https://hub.docker.com/repository/docker/garden12138/xxl-job-admin/general)