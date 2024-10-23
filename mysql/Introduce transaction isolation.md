## 介绍事务隔离级别

> 简单认识

* ```MySQL``` 事务的隔离级别有4种，分别是：
  * ```READ-UNCOMMITTED```（未提交读）：一个事务可以读取另一个未提交的事务的数据。此级别会导致脏读、不可重复读、幻读。
  * ```READ-COMMITTED```（提交读）：一个事务只能读取另一个事务已经提交的数据。此级别会导致不可重复读、幻读。
  * ```REPEATABLE-READ```（可重复读）：一个事务在同一个事务中多次读取同一行数据，结果是一样的。此级别会导致幻读。```InnoDB``` 默认的事务隔离级别就是 ```REPEATABLE-READ```。
  * ```SERIALIZABLE```（串行化）：一个事务完全串行化执行，保证了该事务在同一时间内看到的数据都是一致的。事务最高级别，强制事务排序使之不会冲突从而解决了脏读、不可重复读、幻读的问题，但执行效率低，故使用场景较少。

> 实践前准备

* 常用命令：

  ```sql
  -- 选择数据库DB
  USE DB_NAME;

  -- 查看MySQL版本
  SELECT VERSION();

  -- 查看数据库事务隔离级别以及当前会话的事务隔离级别
  -- 8.0版本之前
  SELECT @@global.tx_isolation,@@tx_isolation;
  -- 8.0版本之后
  SELECT @@global.transaction_isolation,@@transaction_isolation;

  -- 设置当前会话的事务隔离级别
  SET SESSION TRANSACTION ISOLATION LEVEL TRANSACTION_ISOLATION_LEVEL;

  -- 查看事务提交模式
  SHOW VARIABLES LIKE 'autocommit';

  -- 关闭事务自动提交模式（只对当前会话生效）
  SET autocommit = 0;

  -- 开启事务自动提交模式（只对当前会话生效）
  SET autocommit = 1;

  -- 开启事务
  START TRANSACTION;

  -- 提交事务
  COMMIT;

  -- 回滚事务
  ROLLBACK;
  ```

* 创建测试数据库表：

  ```sql
  -- 创建测试数据库
  DROP DATABASE IF EXISTS `transaction_isolation`;
  CREATE DATABASE `transaction_isolation` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
  USE `transaction_isolation`;

  -- 创建测试表
  CREATE TABLE `t_user` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `USER_NAME` varchar(64) NOT NULL DEFAULT '' COMMENT '用户名称',
  `AGE` int(3) NOT NULL DEFAULT '0' COMMENT '年龄',
  PRIMARY KEY (`ID`) USING BTREE
  ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

  -- 插入测试数据
  INSERT INTO `t_user` (`USER_NAME`, `AGE`) VALUES ('Garden', 19);
  ```

> 通过实践认识

* 读未提交-脏读：

  |步骤|client1|client2|说明|
  |:-|:-|:-|:-|
  |第1步||set session transaction isolation level read uncommitted;<br>start transaction;<br>select * from t_user;|设置当前会话事务隔离级别为读未提交;<br>开启事务;<br>查询用户表数据，发现用户id=2的年龄为19岁|
  |第2步|start transaction;<br>update t_user set age = age + 1 where id = 2;||开启事务;<br>更新用户表数据，将id=2的年龄+1|
  |第3步||select * from t_user;|查询用户表数据，其中用户id=2的年龄已经+1，为20岁|

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E8%AF%BB%E6%9C%AA%E6%8F%90%E4%BA%A4_%E8%84%8F%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E8%AF%BB%E6%9C%AA%E6%8F%90%E4%BA%A4_%E8%84%8F%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF1.png)

* 读已提交-不可重复读：

  |步骤|client1|client2|说明|
  |:-|:-|:-|:-|
  |第1步||set session transaction isolation level read committed;<br>start transaction;<br>select * from t_user;|设置当前会话事务隔离级别为读已提交;<br>开启事务;<br>查询用户表数据，发现用户id=2的年龄为20岁|
  |第2步|start transaction;<br>update t_user set age = age + 1 where id = 2;<br>commit;||开启事务;<br>更新用户表数据，将id=2的年龄+1;<br>提交事务|
  |第3步||select * from t_user;|查询用户表数据，其中用户id=2的年龄已经+1，为21岁|

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E8%AF%BB%E5%B7%B2%E6%8F%90%E4%BA%A4_%E4%B8%8D%E5%8F%AF%E9%87%8D%E5%A4%8D%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E8%AF%BB%E5%B7%B2%E6%8F%90%E4%BA%A4_%E4%B8%8D%E5%8F%AF%E9%87%8D%E5%A4%8D%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF1.png)

* 可重复读-幻读：

  |步骤|client1|client2|说明|
  |:-|:-|:-|:-|
  |第1步||set session transaction isolation level repeatable read;<br>start transaction;<br>select * from t_user where id = 3;|设置当前会话事务隔离级别为可重复读;<br>开启事务;<br>查询用户表id=3的数据，发现数据不存在|
  |第2步|start transaction;<br>insert into t_user (id, user_name, age) values (3, 'Daemon', 30);<br>commit;||开启事务;<br>插入用户表数据，插入id=3的数据，值为'Daemon'，年龄为30;<br>提交事务|
  |第3步||insert into t_user (id, user_name, age) values (3, 'Daemon', 30);|插入用户表数据，插入id=3的数据，值为'Daemon'，年龄为30，发现插入主键冲突报错|
  |第4步||select * from t_user where id = 3;|查询用户表id=3的数据，发现数据仍不存在|

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E5%8F%AF%E9%87%8D%E5%A4%8D%E8%AF%BB_%E5%B9%BB%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF2.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/mysql/%E5%8F%AF%E9%87%8D%E5%A4%8D%E8%AF%BB_%E5%B9%BB%E8%AF%BB_%E5%AE%A2%E6%88%B7%E7%AB%AF1.png)

> 注意事项

  * 脏读和不可重复读问题从效果上看，都是一个事务前后读取到的数据不一致，但脏读读取的数据是另一个事务未提交的修改数据，不可重复读读取的数据是另一个事务已提交的数据，前者强调的是读取未提交数据，而后者更强度提交完数据后前后读取不一致。

> 参考文献

* [保姆级教程，终于搞懂脏读、幻读和不可重复读了！](https://www.cnblogs.com/vipstone/p/15758962.html)