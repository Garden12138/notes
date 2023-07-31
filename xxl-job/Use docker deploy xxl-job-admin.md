## 使用 docker 部署 xxl-job-admin 调度中心

> 初始化调度中心数据库

* 需提前部署```MySQL```，可参考[使用 docker 部署 mysql](https://gitee.com/FSDGarden/learn-note/blob/master/mysql/Use%20docker%20deploy%20mysql.md)。

* 在[指定版本的源代码仓库](https://github.com/xuxueli/xxl-job)中，执行```/xxl-job/doc/db/tables_xxl_job.sql```目录下的```SQL```脚本，推荐在执行官方```SQL```脚本后，执行更新注册组表标题字段字符长度```SQL```（原字符长度较短）：

  ```bash
  ALTER TABLE `xxl_job_group` MODIFY title VARCHAR(128);
  ```

> 使用官方镜像部署

* 拉取镜像，如2.4.0版本

  ```bash
  docker pull xuxueli/xxl-job-admin:2.4.0
  ```

* 运行容器

  ```bash
  docker run --name xxl-job-admin --restart=always -d -p 18081:8080 -e PARAMS="--spring.datasource.url=jdbc:mysql://{mysql_domain}/xxl_job?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true&serverTimezone=Asia/Shanghai --spring.datasource.username=${mysql_username} --spring.datasource.password=${mysql_pwd} --xxl.job.accessToken=CsjnD0xFU4JfDjQR23UB7YxGoYVcaRx" -v /data/xxl-job/logs:/data/applogs xuxueli/xxl-job-admin:2.4.0
  ```
  
  环境变量```PARAMS```为```xxl-job-admin```的```properties```配置，值为```--{key1}=value1 --{key2}=value2```形式。必须配置调度中心数据库连接方式```spring.datasource.url```、```spring.datasource.username```以及```spring.datasource.password```；出于安全考虑，推荐使用随机生成的复杂密码作为访问```token```，此时需配置```xxl.job.accessToken```。

> 使用自定义镜像部署（支持执行器组的动态更新）

* 拉取镜像，如2.4.0版本

  ```bash
  docker pull garden12138/xxl-job-admin:2.4.0
  ```

* 运行容器

  ```bash
  docker run --name xxl-job-admin --restart=always -d -p 18081:8080 -e PARAMS="--spring.datasource.url=jdbc:mysql://{mysql_domain}/xxl_job?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true&serverTimezone=Asia/Shanghai --spring.datasource.username=${mysql_username} --spring.datasource.password=${mysql_pwd} --xxl.job.accessToken=CsjnD0xFU4JfDjQR23UB7YxGoYVcaRx" -v /data/xxl-job/logs:/data/applogs garden12138/xxl-job-admin:2.4.0
  ```

> 验证是否部署成功

* 使用默认账号```admin```密码```123456```登录可访问地址```http://{domain}/xxl-job-admin```，如```http://114.132.78.39:18081/xxl-job-admin```。

* 出于安全考虑，建议在登录成功后修改密码。

> 参考文献

* [官方文档](https://www.xuxueli.com/xxl-job/)

* [支持执行器组的动态更特性的issue](https://github.com/xuxueli/xxl-job/issues/3260)