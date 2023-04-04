## 使用 docker-compose 部署 think 知识库

> 安装部署

* 下载源码：
  
  ```bash
  git clone https://github.com/fantasticit/think.git
  ```

* 修改 ```/think/docker-compose.yaml```的```mysql```、```redis```配置：

  ```bash
  # mysql service
    mysql:
    image: mysql:5.7
    restart: always
    container_name: mysql
    volumes:
      - ./runtime/mysql:/var/lib/mysql
    environment:
      - TZ=Asia/Shanghai
      - MYSQL_ROOT_PASSWORD=@root520
      - MYSQL_DATABASE=think
      - MYSQL_USER=garden
      - MYSQL_PASSWORD=@garden520
    expose:
      - '3306'
    ports:
      - '3306:3306'
    command:
      - '--character-set-server=utf8mb4'
      - '--collation-server=utf8mb4_unicode_ci'
    networks:
      - think
  ```

  ```mysql```服务一般设置```root```账号密码（```MYSQL_ROOT_PASSWORD```）、用户账号密码（```MYSQL_USER```、```MYSQL_PASSWORD```）、数据库名（```MYSQL_DATABASE```）以及端口映射（```expose```与```ports```）。

  ```bash
  # redis service
    redis:
    image: redis:latest
    restart: always
    container_name: redis
    command: >
      --requirepass root
    expose:
      - '6379'
    ports:
      - '6379:6379'
    volumes:
      - ./runtime/redis:/data
    privileged: true
    networks:
      - think
  ```

  ```redis```服务一般设置端口映射（```expose```与```ports```）。

* 从```/think/config/docker-prod-sample.yaml```复制一份配置文件，如```prod.yaml```，修改```client```、```server```、```db```、```oss```以及```jwt``配置：

  ```bash
  # Client
  client:
    port: 5001  # 配置client端口
    assetPrefix: '/'  # 不做修改
    apiUrl: 'http://159.75.138.212:5002/api'  # 配置服务端API地址，可配置可用域名如：http://dev.api.garden.cn/api 
    collaborationUrl: 'ws://159.75.138.212:5003/think/wss'  # 配置协作端API地址，可配置可用域名如：ws://dev.api.garden.cn/think/wss
    # 以下为页面meta配置，可自定义
    seoAppName: 'Think知识库文档'
    seoDescription: 'Think知识库文档是一款开源知识管理工具。通过独立的知识库空间，结构化地组织在线协作文档，实现知识的积累与沉淀，促进知识的复用与流通。'
    seoKeywords: 'Think知识库文档,协作,文档,fantasticit,https://github.com/fantasticit/think'
    # 预先连接的来源，空格分割（比如图片存储服务器）
    dnsPrefetch: '//wipi.oss-cn-shanghai.aliyuncs.com'
    # 站点地址，一定要设置，否则会出现 cookie、跨域等问题，可配置可用域名如：http://dev.think.garden.cn
    siteUrl: 'http://159.75.138.212:5001'
    siteDomain: ''
  ```

  ```bash
  # Server
  server:
    prefix: '/api'  #配置API前缀，一般不做修改
    port: 5002  # 配置服务端端口
    collaborationPort: 5003  # 配置协作端端口
    maxDocumentVersion: 20 # 最大版本记录数
    logRetainDays: 3 # 日志保留天数，比如只保留近三天日志
    enableRateLimit: true # 是否限流
    rateLimitWindowMs: 60000 # 限流时间
    rateLimitMax: 1000 # 单位限流时间内单个 ip 最大访问数量
    # 邮箱服务，参考 http://help.163.com/09/1223/14/5R7P6CJ600753VB8.html?servCode=6010376 获取 SMTP 配置
    email:
      host: ''
      port: 465
      user: ''
      password: ''
    # 配置管理员信息
    admin:
      name: 'garden'  # 配置管理员账号
      password: 'garden520'  # 配置管理员账号密码
      email: '' # 配置管理员真实邮箱地址
  ```
  
  ```bash
  # DB
  db:
    # 配置mysql信息
    mysql:
      host: 'mysql'  # 在docker-compose的network中，使用service名字访问
      username: 'garden'
      password: '@garden520'
      database: 'think'
      port: 3306
      charset: 'utf8mb4'
      timezone: '+08:00'
      synchronize: true
    # 配置redis信息
    redis:
      host: 'redis'  # 在docker-compose的network中，使用service名字访问
      port: '6379'
      password: 'root'
  ```

  ```bash
  # OSS
  oss:
    local:
      enable: true
      # 配置服务端访问地址，可配置可用域名如：http://dev.think.garden.cn
      server: 'http://159.75.138.212:5002' 
  # 以下可设置支持的阿里云以及腾讯云厂商OSS配置信息
    tencent:
      enable: false
      config:
        SecretId: ''
        SecretKey: ''
        Bucket: ''
        Region: ''
    aliyun:
      enable: false
      config:
        accessKeyId: ''
        accessKeySecret: ''
        bucket: ''
        https: true
        region: ''
  ```

  ```bash
  # JWT
  jwt:
    secretkey: 'zA_Think+KNOWLEDGE+WIKI+DOCUMENTS@2023'  # 配置安全访问key，建议修改
    expiresIn: '6h'
  ```

* 安装目录下运行：
  
  ```bash
  docker-compose up -d
  ```

* [若需前置```Nginx```，```nginx.conf```可参考](https://gitee.com/FSDGarden/learn-note/tree/master/think/nginx.conf.sample)

> 使用效果图

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-03_17-41-08.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-03_17-40-42.png)
 
> 参考文献

* [how-to-use-docker](https://github.com/fantasticit/think/blob/main/how-to-use-docker.md)