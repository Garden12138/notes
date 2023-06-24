## 使用 docker 部署 seata server

> 版本说明

* 本文使用的```seata```版本为1.3.0，适用于```spring-boot-2.4.2```、
```spring-cloud-2020.0.1```以及```spring-cloud-alibaba-2021.1```微服务框架体系，更多版本说明请参考[这里](https://github.com/alibaba/spring-cloud-alibaba/wiki/%E7%89%88%E6%9C%AC%E8%AF%B4%E6%98%8E)。

> seata配置方式说明

* 本文使用的注册中心以及配置中心均为```Nacos```。

> 前期准备

* [部署```Nacos```](https://gitee.com/FSDGarden/learn-note/blob/master/nacos/Use%20docker%20deploy%20nacos.md)
* [部署```MySQL```](https://gitee.com/FSDGarden/learn-note/blob/master/mysql/Use%20docker%20deploy%20mysql.md)

> 初始化seata_server scheme

* 初始化脚本来源于```https://github.com/seata/seata/blob/1.3.0/script/server/db/mysql.sql```：

  ```bash
  CREATE TABLE `global_table` (
  `xid` varchar(128) NOT NULL,
  `transaction_id` bigint(20) DEFAULT NULL,
  `status` tinyint(4) NOT NULL,
  `application_id` varchar(32) DEFAULT NULL,
  `transaction_service_group` varchar(32) DEFAULT NULL,
  `transaction_name` varchar(128) DEFAULT NULL,
  `timeout` int(11) DEFAULT NULL,
  `begin_time` bigint(20) DEFAULT NULL,
  `application_data` varchar(2000) DEFAULT NULL,
  `gmt_create` datetime DEFAULT NULL,
  `gmt_modified` datetime DEFAULT NULL,
  PRIMARY KEY (`xid`),
  KEY `idx_status_gmt_modified` (`status`,`gmt_modified`),
  KEY `idx_transaction_id` (`transaction_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

  ```bash
  CREATE TABLE `branch_table` (
  `branch_id` bigint(20) NOT NULL,
  `xid` varchar(128) NOT NULL,
  `transaction_id` bigint(20) DEFAULT NULL,
  `resource_group_id` varchar(32) DEFAULT NULL,
  `resource_id` varchar(256) DEFAULT NULL,
  `branch_type` varchar(8) DEFAULT NULL,
  `status` tinyint(4) DEFAULT NULL,
  `client_id` varchar(64) DEFAULT NULL,
  `application_data` varchar(2000) DEFAULT NULL,
  `gmt_create` datetime(6) DEFAULT NULL,
  `gmt_modified` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`branch_id`),
  KEY `idx_xid` (`xid`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

  ```bash
  CREATE TABLE `distributed_lock` (
  `lock_key` char(20) NOT NULL,
  `lock_value` varchar(20) NOT NULL,
  `expire` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`lock_key`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

  ```bash
  CREATE TABLE `lock_table` (
  `row_key` varchar(128) NOT NULL,
  `xid` varchar(128) DEFAULT NULL,
  `transaction_id` bigint(20) DEFAULT NULL,
  `branch_id` bigint(20) NOT NULL,
  `resource_id` varchar(256) DEFAULT NULL,
  `table_name` varchar(32) DEFAULT NULL,
  `pk` varchar(36) DEFAULT NULL,
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0:locked ,1:rollbacking',
  `gmt_create` datetime DEFAULT NULL,
  `gmt_modified` datetime DEFAULT NULL,
  PRIMARY KEY (`row_key`),
  KEY `idx_status` (`status`),
  KEY `idx_branch_id` (`branch_id`),
  KEY `idx_xid` (`xid`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

> 编写配置文件

* 创建配置目录：

  ```bash
  mkdir /data/seata-server/config
  ```

* 在配置目录下，编写注册中心与配置中心配置：
  
  ```bash
  vim registry.config
  ```

  ```bash
  registry {
    # 设置配置类型，如file 、nacos 、eureka、redis、zk、consul、etcd3、sofa
    type = "nacos"

    nacos {
      # 设置注册至nacos的app名称
      application = "seata-server"
      # 设置nacos访问地址
      serverAddr = "159.75.138.212:8848"
      # 设置nacos命名空间
      namespace = ""
      # 设置nacos分组，推荐与应用服务同一分组
      group = "SEATA_GROUP"
      # 设置注册至nacos的集群名称，必须与以下的config.txt配置的service.vgroupMapping.saint-trade-tx-group属性值一致
      cluster = "seata-server-sh"
      # 设置nacos访问账号密码
      username = "nacos"
      password = "garden520"
    }
  }

  config {
    # 设置配置类型，如file 、nacos 、eureka、redis、zk、consul、etcd3、sofa
    type = "nacos"

    nacos {
      # 设置nacos访问地址
      serverAddr = "159.75.138.212:8848"
      # 设置nacos命名空间
      namespace = ""
      # 设置nacos分组，推荐与应用服务同一分组
      group = "SEATA_GROUP"
      # 设置nacos访问账号密码
      username = "nacos"
      password = "garden520"
    }
  }
  ```

* 在配置目录下，编写用于同步至```nacos```配置中心的详细配置信息：

  ```bash
  vim config.txt
  transport.type=TCP
  transport.server=NIO
  transport.heartbeat=true
  transport.enableClientBatchSendRequest=false
  transport.threadFactory.bossThreadPrefix=NettyBoss
  transport.threadFactory.workerThreadPrefix=NettyServerNIOWorker
  transport.threadFactory.serverExecutorThreadPrefix=NettyServerBizHandler
  transport.threadFactory.shareBossWorker=false
  transport.threadFactory.clientSelectorThreadPrefix=NettyClientSelector
  transport.threadFactory.clientSelectorThreadSize=1
  transport.threadFactory.clientWorkerThreadPrefix=NettyClientWorkerThread
  transport.threadFactory.bossThreadSize=1
  transport.threadFactory.workerThreadSize=default
  transport.shutdown.wait=3
  # 设置事务分组名称
  service.vgroupMapping.saint-trade-tx-group=seata-server-sh
  # 设置事务分组对应seata-server实例地址，注意key为service.${service.vgroupMapping.saint-trade-tx-group}.grouplist格式
  service.seata-server-sh.grouplist=159.75.138.212:8091
  service.enableDegrade=false
  service.disableGlobalTransaction=false
  client.rm.asyncCommitBufferLimit=10000
  client.rm.lock.retryInterval=10
  client.rm.lock.retryTimes=30
  client.rm.lock.retryPolicyBranchRollbackOnConflict=true
  client.rm.reportRetryCount=5
  client.rm.tableMetaCheckEnable=false
  client.rm.sqlParserType=druid
  client.rm.reportSuccessEnable=false
  client.rm.sagaBranchRegisterEnable=false
  client.tm.commitRetryCount=5
  client.tm.rollbackRetryCount=5
  client.tm.degradeCheck=false
  client.tm.degradeCheckAllowTimes=10
  client.tm.degradeCheckPeriod=2000
  # 设置seata-server数据存储的db信息
  store.mode=db
  store.db.datasource=druid
  store.db.dbType=mysql
  store.db.driverClassName=com.mysql.cj.jdbc.Driver
  store.db.url=jdbc:mysql://159.75.138.212:13306/seata_server?useUnicode=true
  store.db.user=root
  store.db.password=garden520
  store.db.minConn=5
  store.db.maxConn=30
  store.db.globalTable=global_table
  store.db.branchTable=branch_table
  store.db.queryLimit=100
  store.db.lockTable=lock_table
  store.db.maxWait=5000
  server.recovery.committingRetryPeriod=1000
  server.recovery.asynCommittingRetryPeriod=1000
  server.recovery.rollbackingRetryPeriod=1000
  server.recovery.timeoutRetryPeriod=1000
  server.maxCommitRetryTimeout=-1
  server.maxRollbackRetryTimeout=-1
  server.rollbackRetryTimeoutUnlockEnable=false
  client.undo.dataValidation=true
  client.undo.logSerialization=jackson
  client.undo.onlyCareUpdateColumns=true
  server.undo.logSaveDays=7
  server.undo.logDeletePeriod=86400000
  client.undo.logTable=undo_log
  client.log.exceptionRate=100
  transport.serialization=seata
  transport.compressor=none
  metrics.enabled=false
  metrics.registryType=compact
  metrics.exporterList=prometheus
  metrics.exporterPrometheusPort=9898
  ```

  编写将配置详细信息同步至```nacos```的```shell```脚本：

  ```bash
  mkdir sh && vim sh/nacos-config.sh
  ```

  ```bash
  ## nacos-config.sh
  #!/usr/bin/env bash
  # Copyright 1999-2019 Seata.io Group.
  #
  # Licensed under the Apache License, Version 2.0 (the "License");
  # you may not use this file except in compliance with the License.
  # You may obtain a copy of the License at、
  #
  #      http://www.apache.org/licenses/LICENSE-2.0
  #
  # Unless required by applicable law or agreed to in writing, software
  # distributed under the License is distributed on an "AS IS" BASIS,
  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  # See the License for the specific language governing permissions and
  # limitations under the License.

  while getopts ":h:p:g:t:u:w:" opt
  do
    case $opt in
    h)
      host=$OPTARG
      ;;
    p)
      port=$OPTARG
      ;;
    g)
      group=$OPTARG
      ;;
    t)
      tenant=$OPTARG
      ;;
    u)
      username=$OPTARG
      ;;
    w)
      password=$OPTARG
      ;;
    ?)
      echo " USAGE OPTION: $0 [-h host] [-p port] [-g group] [-t tenant] [-u username] [-w password] "
      exit 1
      ;;
    esac
  done

  if [[ -z ${host} ]]; then
      host=localhost
  fi
  if [[ -z ${port} ]]; then
      port=8848
  fi
  if [[ -z ${group} ]]; then
      group="SEATA_GROUP"
  fi
  if [[ -z ${tenant} ]]; then
      tenant=""
  fi
  if [[ -z ${username} ]]; then
      username=""
  fi
  if [[ -z ${password} ]]; then
      password=""
  fi

  nacosAddr=$host:$port
  contentType="content-type:application/json;charset=UTF-8"

  echo "set nacosAddr=$nacosAddr"
  echo "set group=$group"

  failCount=0
  tempLog=$(mktemp -u)
  function addConfig() {
    curl -X POST -H "${contentType}" "http://$nacosAddr/nacos/v1/cs/configs?dataId=$1&group=$group&content=$2&tenant=$tenant&username=$username&password=$password" >"${tempLog}" 2>/dev/null
    if [[ -z $(cat "${tempLog}") ]]; then
      echo " Please check the cluster status. "
      exit 1
    fi
    if [[ $(cat "${tempLog}") =~ "true" ]]; then
      echo "Set $1=$2 successfully "
    else
      echo "Set $1=$2 failure "
      (( failCount++ ))
    fi
  }

  count=0
  for line in $(cat $(dirname "$PWD")/config.txt | sed s/[[:space:]]//g); do
    (( count++ ))
	  key=${line%%=*}
      value=${line#*=}
	  addConfig "${key}" "${value}"
  done

  echo "========================================================================="
  echo " Complete initialization parameters,  total-count:$count ,  failure-count:$failCount "
  echo "========================================================================="

  if [[ ${failCount} -eq 0 ]]; then
	  echo " Init nacos config finished, please start seata-server. "
  else
	  echo " init nacos config fail. "
  fi
  ```

  执行同步至```nacos```的```shell```脚本：

  ```bash
  sh sh/nacos-config.sh
  ```

> 拉取镜像

  ```bash
  docker pull seataio/seata-server:1.3.0
  ```

> 运行容器

  ```bash
  docker run --name seata-server --restart=always --privileged=true -d -p 8091:8091 -e SEATA_PORT=8091 -e SEATA_IP=159.75.138.212 -e SEATA_CONFIG_NAME=file:/root/seata-config/registry -v /data/seata/config:/root/seata-config seataio/seata-server:1.3.0
  ```
  
  环境变量```SEATA_IP```以及```SEATA_PORT```分别设置```seata-server```的可访问```IP```以及端口；环境变量```SEATA_CONFIG_NAME```设置容器内设置文件路径。

> 参考文献

* [dockerhub seataio/seata-server](https://hub.docker.com/r/seataio/seata-server)