## 使用 docker 部署 seata server

```bash
registry {
  type = "nacos"
  
  nacos {
    application = "seata-server"
    serverAddr = "159.75.138.212:8848"
    namespace = ""
    cluster = "default"
    username = "nacos"
    password = "garden520"
  }
}

config {
  type = "nacos"
  
  nacos {
    serverAddr = "159.75.138.212:8848"
    namespace = ""
    group = "DEFAULT_GROUP"
    username = "nacos"
    password = "garden520"
    dataId: "seata-server.yaml"
  }
}
```

```bash
store:
  db:
    datasource: druid
    dbType: mysql
    driverClassName: com.mysql.cj.jdbc.Driver
    password: 'garden520'
    url: jdbc:mysql://159.75.138.212:13306/seata-server?useUnicode=true&characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useSSL=false
    user: 'root'
  mode: db
```

```bash
docker pull seataio/seata-server:1.3.0
```

```bash
docker run --name seata-server --restart=always --privileged=true -d -p 8091:8091 -e SEATA_PORT=8091 -e SEATA_IP=159.75.138.212 -e SEATA_CONFIG_NAME=file:/root/seata-config/registry -v /data/seata/config:/root/seata-config seataio/seata-server:1.3.0
```