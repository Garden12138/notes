## 集成 Mysql 分布式锁

> 实现原理

  * 排他锁：```FOR UPDATE```是一种行级锁，用户对某行加锁，该用户可以查询也可以更新加锁的数据行，而其他用户只能查询不能更新。该锁是永久独占的，只有当事务提交或回滚、退出数据库或程序停止运行时才会释放锁。

  * 整体流程：创建一个数据库表用于记录系统分布式锁信息（包含业务含义信息），在业务需获取分布式锁处（使用```@Transactional```注解管理事务），通过```SELECT FOR UPDATE```语句获取锁，并判断是否获取成功，如果获取成功则执行业务（执行完成后由事务提交或回滚释放锁），否则等待（等待其他线程释放锁）。

> 特点：

  * 互斥性
  * 公平性
  * 可重入性
  * 高可用，```TTL```机制，```MySQL```本地管理客户端会话。如果客户端由于机器故障或网络故障而断开连接，```MySQL```将自动释放行级锁，不会一直死锁。
  * 高性能，释放锁时，```MySQL```只会通知队列中等待的下一个客户端，而不是一次性通知所有客户端，避免雷群问题。

> 适用场景：

  * 适用于并发量不大的业务场景，因为排他锁是一种悲观锁，会导致大量的线程等待（可通过超时机制解决），降低系统的并发能力，且行锁时间过长会降低数据库性能（业务处理时间长导致占有锁时间长，可通过合理设计解耦业务缓解）。

> 实践

  * 创建系统分布式锁表：
    
    ```sql
    CREATE TABLE `t_sys_distributedlock` (
      `ID` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
      `LOCK_CODE` varchar(64) DEFAULT NULL COMMENT '锁编码',
      `CREATE_TIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `UPDATE_TIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`ID`) USING BTREE,
      UNIQUE KEY `UNIQ_lLOCK_CODE` (`LOCK_CODE`)
    ) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COMMENT='系统分布式锁表';
    ```

    ```LOCK_CODE```字段为分布式锁的唯一标识，一般定义为资源编码。创建表完成后，需根据实际业务整理资源编码，并初始化，例如：

    ```sql
    INSERT INTO `t_sys_distributedlock` (`LOCK_CODE`, `CREATE_TIME`, `UPDATE_TIME`) VALUES ('ORDER_NO_GENE', '2024-10-16 17:19:31', '2024-10-18 10:49:24');
    ```

  * 引入依赖：
    
    ```xml
    <dependency>
	    <groupId>org.springframework.boot</groupId>
		<artifactId>spring-boot-starter-web</artifactId>
	</dependency>
    <dependency>
	    <groupId>mysql</groupId>
		<artifactId>mysql-connector-java</artifactId>
		<scope>runtime</scope>
	</dependency>
	<dependency>
		<groupId>org.mybatis.spring.boot</groupId>
		<artifactId>mybatis-spring-boot-starter</artifactId>
		<version>2.0.0</version>
    <dependency>
		<groupId>com.baomidou</groupId>
		<artifactId>mybatis-plus-boot-starter</artifactId>
		<version>${mybatis-plus.version}</version>
	</dependency>
	</dependency>
    <dependency>
		<groupId>com.alibaba</groupId>
		<artifactId>druid-spring-boot-starter</artifactId>
		<version>1.1.10</version>
	</dependency>
    ```
  
  * 编写配置：
  
    ```yaml
    # Tomcat
      server:
        port: 8081
        servlet:
          context-path: /springboot
    # mybatis-plus      
      mybatis-plus:
        global-config:
          banner: false
          db-config:
            id-type: auto
            logic-delete-value: 1
            logic-not-delete-value: 0
        mapper-locations: classpath:/mapper/**/*.xml
        configuration:
          map-underscore-to-camel-case: true    
          cache-enabled: false
       type-aliases-package: com.garden.**.**.entity
       spring:
    # datasource
      datasource:
        url: ${MYSQL_URL:jdbc:mysql://${ip}:${port}/mysql_distributedlock?allowMultiQueries=true&useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai}
        username: ${MYSQL_USERNAME:root}
        password: ${MYSQL_PASSWORD:garden520}
        driver-class-name: com.mysql.jdbc.Driver
        type: com.alibaba.druid.pool.DruidDataSource
        initialSize: 5
        minIdle: 5
        maxActive: 20
        maxWait: 60000
        timeBetweenEvictionRunsMillis: 60000
        minEvictableIdleTimeMillis: 300000
        validationQuery: SELECT 1 FROM DUAL
        testWhileIdle: true
        testOnBorrow: false
        testOnReturn: false
        poolPreparedStatements: true
        maxPoolPreparedStatementPerConnectionSize: 20
        filters: stat,wall,slf4j
        connectionProperties: druid.stat.mergeSql=true;druid.stat.slowSqlMillis=5000
        useGlobalDataSourceStat: true
    # druid
      druid:
        console:
        loginUsername: admin
        loginPassword: oppein@123
        resetEnable: true
        sessionStatEnable: false
    ```

  * 创建系统分布式锁实体类：

    ```java
    @Data
    public class SysDistributedLock {

        private Long id;
        private String lockCode;
        private Date createTime;
        private Date updateTime;

    }
    ```

  * 编写系统分布式锁持久化层：

    ```java
    @Mapper
    public interface SysDistributedLockMapper {

        List<SysDistributedLock> getDistributedLock(@Param("lockCode") String lockCode);

    }
    ```

    ```xml
    <?xml version="1.0" encoding="UTF-8" ?>
    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd" >

    <mapper namespace="com.garden.mapper.SysDistributedLockMapper">

        <select id="getDistributedLock" resultType="com.garden.entity.SysDistributedLock">
            SELECT
            T.*
            FROM
            t_sys_distributedlock T
            <where>
                <if test="lockCode != null and lockCode != ''">
                    AND T.LOCK_CODE = #{lockCode}
                </if>
            </where>
            FOR UPDATE
        </select>

    </mapper>
    ```

  * 编写系统分布式锁业务层：
    
    ```java
    @Service
    public class SysDistributedLockService {

        @Autowired
        private SysDistributedLockMapper sysDistributedLockMapper;


        public boolean tryLock(String lockCode){
            List<SysDistributedLock> list = sysDistributedLockMapper.getDistributedLock(lockCode);
            return !CollectionUtils.isEmpty(list);
        }

    }
    ```

  * 编写测试用例业务层：

    ```java
    @Slf4j
    @Service
    public class BusinessService {

        @Autowired
        private SysDistributedLockService sysDistributedLockService;

        @Transactional(rollbackFor = Exception.class)
        public String doSomething() throws Exception {
            log.info("invoke doSomething()");
            if (sysDistributedLockService.tryLock("ORDER_NO_GENE")) {
                log.info("get distributed lock successful");
                log.info("generate order no: {}", UUID.randomUUID());
                Thread.sleep(15 * 1000);
            } else {
                log.info("get distributed lock failed");
                throw new Exception("doSomething failed");
            }
            return "success";
        }

    }
    ```

    ```@Transactional```注解管理整个业务方法的事务，在成功获取分布式锁后，业务执行成功则事务提交```commit```（释放锁），否则事务回滚```rollback```（释放锁）。

  * 编写测试用例控制层：

    ```java
    @RestController
    @RequestMapping("/business")
    public class BusinessController {


        @Autowired
        private BusinessService businessService;

        @GetMapping("/doSomething")
        public String doSomething() throws Exception {
            return businessService.doSomething();
        }

    }
    ```

  * 启用两个不同端口的实例：

    ```bash
    java -jar springboot-mysql-distributedlock-0.0.1-SNAPSHOT.jar --server.port=8081 &
    java -jar springboot-mysql-distributedlock-0.0.1-SNAPSHOT.jar --server.port=8082 &
    ```

    ```idea```中可配置```VM options```启用不同端口实例：

    ```bash
    -Dserver.port=8081
    -Dserver.port=8082
    ```

  * 同时调用两个实例：

    ```bash
    curl http://localhost:8081/business/doSomething
    curl http://localhost:8082/business/doSomething
    ```

    观察日志输出，可以看到两个实例分别获取分布式锁成功且生成订单号和等待获取锁，最后生成订单号：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2024-10-18_15-05-35.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/Snipaste_2024-10-18_15-06-38.png)

> 注意事项

  * 特点四所提及的，占有锁的客户端在未正常提交或回滚事务时，退出或断开连接，锁会自动释放，不会造成死锁：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/WechatIMG5586.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/springboot/WechatIMG5587.png)

> 参考文献

* [基于MySQL数据库排它锁（for update）实现的分布式锁](https://blog.csdn.net/hou_ge/article/details/112754366)
* [如何用MySQL设计一个分布式锁？](https://www.51cto.com/article/748261.html)