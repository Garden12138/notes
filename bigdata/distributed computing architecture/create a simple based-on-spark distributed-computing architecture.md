# 分布式计算平台简单搭建

## 预备知识

由于涉及概念比较多，可以先了解以下内容

| 名词、概念                            | 备注 |
| ------------------------------------- | ---- |
| 分布式存储                            |      |
| 调度                                  |      |
| MapReduce                             |      |
| GFS（Google File System）             |      |
| 批处理                                |      |
| 流式处理                              |      |
| RDD（Resilient Distributed Datasets） |      |



## 什么是Hadoop

Hadoop是由Apache基金会所发布的开源的分布式计算框架，主要用于处理大规模的数据集的处理和分析。它基于Google的MapReduce算法和Google文件系统（GFS）的思想，提供了一个可靠，高效，可扩展的分布式计算平台。

相关内容：

https://apache.github.io/hadoop/index.html



### 什么是HDFS

HDFS，全称Hadoop Distribute File System（Hadoop分布式文件系统），Hadoop核心组件之一，是一个分布式存储服务。

相关内容：

https://apache.github.io/hadoop/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html



### 什么是YARN

Apache Hadoop YARN （Yet Another Resource Negotiator，另一种资源协调者），Hadoop核心组件之一，是一个通用资源管理系统，可为上层应用提供统一的资源管理和调度

相关内容：

https://hadoop.apache.org/docs/r2.7.1/hadoop-yarn/hadoop-yarn-site/YARN.html



## 什么是Spark

Spark是一个**基于内存计算**的大数据并行计算框架，可用于构建大型的、低延迟的数据分析应用程序。

相关内容：

https://spark.apache.org/docs/latest/

https://www.w3cschool.cn/spark/



## 基础架构

![](img\架构.png)



## 工作原理

![](img\简化工作原理.png)

上述示意图是经过简化的，实际步骤会更复杂一点，参考Yarn的工作流程

https://apache.github.io/hadoop/hadoop-yarn/hadoop-yarn-site/YARN.html

https://www.cnblogs.com/ssqq5200936/p/14093635.html



## 名词解释

| 名词              | 备注                                                         |
| ----------------- | ------------------------------------------------------------ |
| NameNode          | hdfs命名节点（管理节点），负责管理DataNode，不参与操作数据，以下简称nn |
| DataNode          | hdfs数据节点，负责直接操作数据，以下简称dn                   |
| SecondaryNameNode | hdfs第二命名节点，命名节点的后备节点，以下简称snn            |
| ResourceManager   | yarn资源管理器，负责管理NodeManager，以下简称rm              |
| NodeManager       | yarn节点管理器，负责执行任务，以下简称nm                     |
| JobHistoryServer  | hadoop历史服务（日志记录），以下简称jhs                      |
| 资源              | 这里的资源主要指，CPU核数、内存大小、磁盘空间大小等          |
| 任务资源          | 一般指，计算程序、计算程序的依赖包、计算所依赖的上下文数据等 |



## 准备工作

### 服务器规划

准备至少3台服务器

| 域名设置 | 内存   | 硬盘    | 角色划分    |
| -------- | ------ | ------- | ----------- |
| node1    | 至少2G | 至少40G | nn、rm、jhs |
| node2    | 至少2G | 至少40G | dn、nm      |
| node3    | 至少2G | 至少40G | dn、nm、snn |

### 环境\依赖

| **依赖项** | **版本**          | **备注**                                          |
| ---------- | ----------------- | ------------------------------------------------- |
| Linux      | CentOS 7.4        |                                                   |
| Java       | OpenJDK 1.8.0_362 |                                                   |
| Hadoop     | 2.x/3.x           | 3.x版本，要求JDK版本必须8以上（包括JDK8）         |
| Spark      | 2.x/3.x           | 3.x版本，要求JDK版本必须8以上（包括JDK8）且小于12 |

### 关闭防火墙

```shell
#停止firewalld进程
systemctl stop firewalld
#禁用firewalldjingg
systemctl disable firewalld
```



### 关闭SELinux

```shell
#临时关闭,设置SELinux成为permissive模式
setenforce 0

#永久关闭,修改配置项
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
```



### 免密登陆

```shell
#生成密钥(执行命令后,若无特殊设置,直接按"回车"就可以了)
#最终会在用户目录(~)下生成.ssh目录
#若没有该命令,则需要安装openssh
ssh-keygen -t rsa

#将公钥添加到 authorzied_keys文件中(自己对自己免密登陆)
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

#将公钥分发给远程主机(需要提供远程主机的登陆密码)
ssh-copy-id [remote_host]
```



### 时间同步

```shell
#安装ntpdate
yum -y install ntpdate

#使用crontab自动同步时钟
crontab -e 
#在编辑框输入以下内容
#每30秒执行ntpdate命令,与阿里云NTP服务器同步时间
*/30 * * * * /usr/sbin/ntpdate time1.aliyun.com
```



### 环境变量

```shell
#编辑/etc/profile文件
vi etc/profile

#添加以下内容
#JAVA_HOME(以实际的根目录为准,以下仅作为参考)
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.362.b08-1.el7_9.x86_64
export CLASSPATH=.:$JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib/tools.jar:$JAVA_HOME/jre/lib/rt.jar
export PATH=$PATH:$JAVA_HOME/bin

#保存后,执行source命令
source /etc/profile
```



## 部署Hadoop

### 下载安装包

```shell
#下载Hadoop安装包
wget --no-check-certificate https://mirrors.tuna.tsinghua.edu.cn/apache/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz

```



### 环境变量

```shell
#编辑/etc/profile
vi etc/profile

#添加以下内容
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin

#保存后,执行source命令
source /etc/profile
```



### 修改配置

进入配置目录

```shell
cd ~/hadoop/etc
```

![](D:\自由研究\[IP]大数据平台实践\img\配置目录.png)



#### hadoop-env.sh

```shell
#在该脚本最下面,加上JAVA根目录(以实际的根目录为准,以下仅作为参考)
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.362.b08-1.el7_9.x86_64

export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root
export HADOOP_PID_DIR=/data/hadoop/pids
export HADOOP_LOG_DIR=/data/hadoop/logs
```



#### core-site.xml

```xml
<!-- hdfs nameNode -->
<property>
    <name>fs.defaultFS</name>
    <value>hdfs://node1:8020</value>
</property>

<property>
    <name>hadoop.tmp.dir</name>
    <value>/data/hadoop_workspace</value>
</property>

<!-- 设置HDFS web UI用户身份 -->
<property>
    <name>hadoop.http.staticuser.user</name>
    <value>root</value>
</property>

<!-- 整合hive 用户代理设置 -->
<property>
    <name>hadoop.proxyuser.root.hosts</name>
    <value>*</value>
</property>

<property>
    <name>hadoop.proxyuser.root.groups</name>
    <value>*</value>
</property>

<!-- 文件系统垃圾桶保存时间 -->
<property>
    <name>fs.trash.interval</name>
    <value>1440</value>
</property>
```



#### hdfs-site.xml

```xml
<!-- 配置  主结点的web控制台地址-->
<property>
    <name>dfs.namenode.http-address</name>
    <value>node1:9870</value>
</property>

<!-- 配置  从结点的web控制台地址-->
<property>
    <name>dfs.namenode.secondary.http-address</name>
    <value>node3:9868</value>
</property>
```



#### yarn-site.xml

```xml
<!-- 设置YARN集群主角色运行机器位置 -->
<property>
    <name>yarn.resourcemanager.hostname</name>
    <value>node1</value>
</property>

<!-- 指定MR走shuffle -->
<property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
</property>

<!-- 是否将对容器实施物理内存限制 -->
<property>
    <name>yarn.nodemanager.pmem-check-enabled</name>
    <value>false</value>
</property>

<!-- 是否将对容器实施虚拟内存限制。 -->
<property>
    <name>yarn.nodemanager.vmem-check-enabled</name>
    <value>false</value>
</property>

<!-- 开启日志聚集 -->
<property>
  <name>yarn.log-aggregation-enable</name>
  <value>true</value>
</property>

<!-- 设置yarn历史服务器地址 -->
<property>
    <name>yarn.log.server.url</name>
    <value>http://node1:19888/jobhistory/logs</value>
</property>

<!-- 历史日志保存的时间 7天 -->
<property>
  <name>yarn.log-aggregation.retain-seconds</name>
  <value>604800</value>
</property>

<!-- NodeMananger提供默认内存:8G -->
<property>
  <name>yarn.nodemanager.resource.memory-mb</name>
  <value>8192</value>
</property>

<!-- NodeMananger提供虚拟内核数:8 -->
<property>
  <name>yarn.nodemanager.resource.cpu-vcores</name>
  <value>8</value>
</property>
```





#### mapred-site.xml

```xml
<!-- 设置MR程序默认运行模式： yarn集群模式 local本地模式 -->
<property>
  <name>mapreduce.framework.name</name>
  <value>yarn</value>
</property>

<!-- MR程序历史服务地址 -->
<property>
  <name>mapreduce.jobhistory.address</name>
  <value>node1:10020</value>
</property>

<!-- MR程序历史服务器web端地址 -->
<property>
  <name>mapreduce.jobhistory.webapp.address</name>
  <value>node1:19888</value>
</property>

<property>
  <name>yarn.app.mapreduce.am.env</name>
  <value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value>
</property>

<property>
  <name>mapreduce.map.env</name>
  <value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value>
</property>

<property>
  <name>mapreduce.reduce.env</name>
  <value>HADOOP_MAPRED_HOME=${HADOOP_HOME}</value>
</property>
```





### 同步到其他服务器

将node1服务器的hadoop目录同步到node2、node3服务器

远程拷贝

```shell
#这里将hadoop目录放到了/opt目录下,以安装目录为准
cd /opt
#执行远程拷贝,将hadoop目录拷贝到远程主机的/opt目录下
scp -r hadoop root@node2:$PWD
scp -r hadoop root@node3:$PWD
```

修改环境变量

```shell
#编辑/etc/profile
vi etc/profile

#添加以下内容
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export PATH=$PATH:$HADOOP_HOME/sbin

#保存后,执行source命令
source /etc/profile
```



### 启动

```shell
#hdfs初始化(仅在第一次启动时执行)
hdfs namenode -format

#启动hdfs
start-dfs.sh
#启动yarn
start-yarn.sh
#启动JobHistoryServer服务
$ mapred --daemon start historyserver
```

### 验证

```
#执行jps命令查看进程
jps
```

node1

![](img\node1.png)

node2

![](img\node2.png)

node3

![](img\node3.png)

访问控制台

访问hadoop控制台 http://node1:8088

![](img\yarn-console.png)



访问hdfs控制台 http://node1:9870

![](img\hdfs-console.png)



## 整合Spark

采用Spark-on-Yarn的方式整合

Spark-on-Yarn：https://blog.csdn.net/bocai8058/article/details/119300198

### 准备安装包

使用国内的镜像仓库下载，访问https://mirrors.tuna.tsinghua.edu.cn/apache/spark/

![](img\download_spark.png)

```shell
#下载安装包，这里现在-without-hadoop版本的，因为上面已经部署hadoop了
wget --no-check-certificate https://mirrors.tuna.tsinghua.edu.cn/apache/spark/spark-3.3.2/spark-3.3.2-bin-without-hadoop.tgz

#解压
tar -zxvf spark-3.3.2-bin-without-hadoop.tgz
```



### 配置环境变量

```shell
#在/etc/profile中增加以下配置
export SPARK_HOME=/opt/spark-2.2.0
export PATH=${SPARK_HOME}/bin:${SPARK_HOME}/sbin:$PATH

#保存后执行source命令
source /etc/profile
```



### 配置文件

#### spark-env.sh

```shell
#使用spark的环境配置模板
cd $SPARK_HOME/conf
#拷贝env模板
cp spark-env.sh.template spark-env.sh

#增加配置参数
#JAVA_HOME以实际为准
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.362.b08-1.el7_9.x86_64
#HADOOP_HOME以实际为准
export HADOOP_HOME=/opt/hadoop
#HADOOP_CONF_DIR以实际为准
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export SPARK_MASTER_HOST=node1
export SPARK_MASTER_PORT=7077
export SPARK_DIST_CLASSPATH=$(/opt/hadoop/bin/hadoop classpath)
```



#### spark-default.conf

```shell
#使用spark的环境配置模板
cd $SPARK_HOME/conf
#拷贝env模板
cp spark-default.conf.template spark-default.conf

#添加以下参数
spark.master                     spark://node1:7077
spark.serializer                 org.apache.spark.serializer.KryoSerializer
spark.driver.memory              1g
spark.executor.memory            1g
#这里指向的是一个hdfs路径，用于共享spark-jars（详见上传任务资源）
spark.yarn.jars                  hdfs://node1:8020/spark-jars/*.jar
```



#### workers

```shell
#使用spark的环境配置模板
cd $SPARK_HOME/conf
#拷贝env模板
cp workers.template workers

#添加以下参数
node1
node2
node3
```

### 同步到其他服务器

远程拷贝

```shell
#使用scp命令
#这里将spark目录放到了/opt目录下,以安装目录为准
cd /opt
#执行远程拷贝,将spark目录拷贝到远程主机的/opt目录下
scp -r spark root@node2:$PWD
scp -r spark root@node3:$PWD
```

修改环境变量

```shell
#node2、node3的/etc/profile中添加以下配置
#SPARK_HOME以实际安装目录为准
export SPARK_HOME=/opt/spark-3.3.2
export PATH=${SPARK_HOME}/bin:${SPARK_HOME}/sbin:$PATH
```



### 上传任务资源

每次在spark运行时都会把yarn所需的spark jar打包上传至HDFS，然后分发到每个NM，为了节省时间我们可以将jar包提前上传至HDFS，那么spark在运行时就少了一步上传，可以直接从HDFS读取了

```shell
#在hdfs创建目录
hdfs dfs -mkdir /spark-jars

#上传jar包到hdfs目录
hdfs dfs -put spark-3.3.2-bin-without-hadoop/jars/* /spark-jars
```

在hdfs控制台查看上传的文件

![](img\hdfs-spark-jar.png)

### 验证

使用官方用例：计算圆周率

在node1服务器执行以下脚本

```shell
#提交任务
spark-submit \
--class org.apache.spark.examples.SparkPi \
--master yarn \
--deploy-mode cluster \
--driver-memory 1G \
--num-executors 2 \
--executor-memory 1G \
--executor-cores 1 \
/opt/spark-3.3.2/examples/jars/spark-examples_2.12-3.3.2.jar \
10

#参数说明
# spark-submit: 这是用于提交 Spark 任务的脚本。
# --master yarn: 指定 Spark 集群管理器为 YARN。
# --deploy-mode cluster: 这意味着 Spark 任务的 driver 程序将在NM中启动
# --driver-memory 1G: 分配给 driver 的内存为 1 GB。
# --num-executors 2: 指定 Spark 应使用 2 个 executor 进程。
# --executor-memory 1G: 每个 Spark executor 使用 1 GB 内存。
# --total-executor-cores 1: 指定所有 executors 合计可使用的 CPU 核心数为 1。
# /opt/spark-3.3.2/examples/jars/spark-examples_2.12-3.3.2.jar: 要运行的 Spark程序的路径。
# 10: 这是传递给Spark程序的一个参数。具体来说，这通常用于指定计算π值时的迭代次数或精度。 

```

执行测试脚本

![](img\spark-submit-execute.png)

执行过程中生成了一个application_id：application_1678869388656_0002

通过application_id，在控制台查看对应的application

![](img\application-console.png)

查看日志，输出结果直接打印在日志

![](img\application-log.png)