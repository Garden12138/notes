## SpringCloud 集成 seata client

> 业务服务数据库新增事务回滚日志表undo_log

```bash
CREATE TABLE `undo_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `branch_id` bigint(20) NOT NULL,
  `xid` varchar(100) NOT NULL,
  `context` varchar(128) NOT NULL,
  `rollback_info` longblob NOT NULL,
  `log_status` int(11) NOT NULL,
  `log_created` timestamp NULL DEFAULT NULL,
  `log_modified` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_undo_log` (`xid`,`branch_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8;
```

> 业务服务模块pom新增依赖

```bash
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-seata</artifactId>
</dependency>
```

> 业务服务模块application新增配置

```bash
seata:
  # 与seata-server的config.txt文件中的service.vgroupMapping后的值保持一致即，使nacos config中要存在dataId为service.vgroupMapping.saint-trade-tx-group的配置
  tx-service-group: saint-trade-tx-group
  # 采用nacos作为配置中心（与seata-server一致）
  config:
    type: nacos
    nacos:
      server-addr: ${NACOS_DISCOVERY_SERVERADDR:159.75.138.212:8848}
      group: SEATA_GROUP
  # 采用nacos作为注册中心（与seata-server一致）
  registry:
    type: nacos
    nacos:
      # seata-server应用名称
      application: seata-server
      # seata-server注册nacos服务地址
      server-addr: ${NACOS_DISCOVERY_SERVERADDR:159.75.138.212:8848}
      group: SEATA_GROUP
```

> 业务服务模块新增数据源配置（本文以mybatis为持久化框架）

```bash
@Configuration
public class DataSourceConfig {

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource")
    public DruidDataSource druidDataSource() {
        return new DruidDataSource();
    }

    /**
     * 需要将 DataSourceProxy 设置为主数据源，否则事务无法回滚
     *
     * @param druidDataSource The DruidDataSource
     * @return The default datasource
     */
    @Primary
    @Bean("dataSource")
    public DataSource dataSource(DruidDataSource druidDataSource) {
        return new DataSourceProxy(druidDataSource);
    }

   /**
     * mybatis为持久化框架需设置SqlSessionFactory为MybatisSqlSessionFactoryBean
     *
     * @param dataSource
     * @return
     * @throws Exception
     */
    @Bean
    public SqlSessionFactory sqlSessionFactoryBean(DataSource dataSource) throws Exception {
        MybatisSqlSessionFactoryBean sqlSessionFactoryBean = new MybatisSqlSessionFactoryBean ();
        sqlSessionFactoryBean.setDataSource(dataSource);
        return sqlSessionFactoryBean.getObject();
    }

}
```

> 另一业务服务模块的服务方法新增注解@GlobalTransactional开启全局分布式事务

```bash
@Service("seataBusinessService")
public class SeataBusinessServiceImpl  implements SeataBusinessService {

    @Autowired
    private StockTblFeign stockTblFeign;

    @Autowired
    private OrderTblFeign orderTblFeign;

    @GlobalTransactional
    public void purchase(String userId, String commodityCode, int orderCount) {
        // 先减库存后创建订单
        stockTblFeign.deduct(commodityCode, orderCount);
        orderTblFeign.create(userId, commodityCode, orderCount);
    }
}
```

> 完整代码请参考[这里](https://gitee.com/FSDGarden/microservices-spring/tree/feature%2Fsc-2020.0.1-v1/)

> 参考文献

* [你为Spring Cloud整合Seata、Nacos实现分布式事务案例跑不起来苦恼过吗（巨细排坑版）](https://developer.aliyun.com/article/1058275#slide-26)