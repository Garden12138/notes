## SpringCloud 集成 seata client

> 创建业务表

```bash
-- account service
DROP SCHEMA IF EXISTS seata_account;
CREATE SCHEMA seata_account;
USE seata_account;

CREATE TABLE `account_tbl`
(
    `id`      INT(11) NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(255) DEFAULT NULL,
    `money`   INT(11) DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

INSERT INTO account_tbl (id, user_id, money)
VALUES (1, '1001', 10000);
INSERT INTO account_tbl (id, user_id, money)
VALUES (2, '1002', 10000);

CREATE TABLE `undo_log`
(
    `id`            bigint(20) NOT NULL AUTO_INCREMENT,
    `branch_id`     bigint(20) NOT NULL,
    `xid`           varchar(100) NOT NULL,
    `context`       varchar(128) NOT NULL,
    `rollback_info` longblob     NOT NULL,
    `log_status`    int(11) NOT NULL,
    `log_created` timestamp NULL DEFAULT NULL,
    `log_modified` timestamp NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ux_undo_log` (`xid`,`branch_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

```bash
-- order service
DROP SCHEMA IF EXISTS seata_order;
CREATE SCHEMA seata_order;
USE seata_order;

CREATE TABLE `order_tbl`
(
    `id`             INT(11) NOT NULL AUTO_INCREMENT,
    `user_id`        VARCHAR(255) DEFAULT NULL,
    `commodity_code` VARCHAR(255) DEFAULT NULL,
    `count`          INT(11) DEFAULT '0',
    `money`          INT(11) DEFAULT '0',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

CREATE TABLE `undo_log`
(
    `id`            bigint(20) NOT NULL AUTO_INCREMENT,
    `branch_id`     bigint(20) NOT NULL,
    `xid`           varchar(100) NOT NULL,
    `context`       varchar(128) NOT NULL,
    `rollback_info` longblob     NOT NULL,
    `log_status`    int(11) NOT NULL,
    `log_created` timestamp NULL DEFAULT NULL,
    `log_modified` timestamp NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ux_undo_log` (`xid`,`branch_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

```bash
-- stock service
DROP SCHEMA IF EXISTS seata_stock;
CREATE SCHEMA seata_stock;
USE seata_stock;

CREATE TABLE `stock_tbl`
(
    `id`             INT(11) NOT NULL AUTO_INCREMENT,
    `commodity_code` VARCHAR(255) DEFAULT NULL,
    `count`          INT(11) DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `commodity_code` (`commodity_code`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

INSERT INTO stock_tbl (id, commodity_code, count)
VALUES (1, '2001', 1000);

CREATE TABLE `undo_log`
(
    `id`            bigint(20) NOT NULL AUTO_INCREMENT,
    `branch_id`     bigint(20) NOT NULL,
    `xid`           varchar(100) NOT NULL,
    `context`       varchar(128) NOT NULL,
    `rollback_info` longblob     NOT NULL,
    `log_status`    int(11) NOT NULL,
    `log_created` timestamp NULL DEFAULT NULL,
    `log_modified` timestamp NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ux_undo_log` (`xid`,`branch_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

> 创建业务模块

> 集成持久化框架

> 完成业务接口

> 参考文献

* [你为Spring Cloud整合Seata、Nacos实现分布式事务案例跑不起来苦恼过吗（巨细排坑版）](https://developer.aliyun.com/article/1058275#slide-26)