# learn-note

个人技术学习笔记仓库，用于沉淀后端开发、云原生、中间件、AI 工具、工程实践和读书笔记等内容。

这个仓库不是单一应用项目，而是一套长期维护的知识库：每个目录对应一个技术主题，目录下的 Markdown 文档记录学习过程、部署实践、问题排查、源码/概念理解和可复用的配置示例。

## 内容导航

### 后端与 Java 生态

- `java/`：Java 基础、面试、Effective Java 等读书笔记与实践记录
- `spring/`：Spring 相关机制与注解笔记
- `springboot/`：Spring Boot 集成 Redis、RocketMQ、Security、Actuator、Prometheus、Minio 等实践
- `springcloud/`：Spring Cloud Gateway、Sentinel 等组件使用记录
- `mybatis/`、`mybatisplus/`：MyBatis 及 MyBatis-Plus 使用笔记
- `maven/`：Maven 实践
- `netty/`：Netty、NIO、RPC、CMPP 等网络编程笔记

### 中间件与基础设施

- `docker/`：Docker、Dockerfile、docker-compose、镜像理解与实践
- `k8s/`：Kubernetes、Minikube、Helm、Deployment、Service、Ingress 等实践
- `redis/`：Redis 入门、集群部署、应用场景与 CacheCloud
- `rocketmq/`、`kafka/`：消息队列学习与部署
- `mysql/`、`clickhouse/`：数据库事务、部署、分析型数据库学习
- `nacos/`、`seata/`、`xxl-job/`、`elasticjob/`：微服务治理与任务调度组件
- `nginx/`、`openresty/`、`haproxy/`、`apisix/`：网关、代理、负载均衡相关实践

### 可观测性与 DevOps

- `prometheus/`、`grafana/`、`altermanager/`：监控、告警与可视化部署
- `skywalking/`：链路追踪服务端、UI 与 Spring Cloud Agent 集成
- `elk/`：ELK Stack 部署与 Logstash Pipeline 配置
- `jenkins/`、`gocd/`、`harbor/`：CI/CD、镜像仓库与自动化部署

### AI 与自动化

- `ai/`：大模型部署、MCP、Dify、Prompt、OCR、语音识别、模型微调、AI 助手等笔记
- `dify/`：Dify 部署、工作流、插件问题处理与 YAML 示例
- `n8n/`：n8n 自动化工具学习记录

### 编程语言与算法

- `go/`：Go 语言学习、gRPC、Web 服务示例与读书笔记
- `python3/`：Python 基础语法、文件处理、爬虫、数据处理示例
- `rust/`：Rust 学习笔记
- `algorithm/`：算法学习、编码练习、反向传播算法理解

### 架构、设计与工程方法

- `architecture/`：电商数据平台架构、数据库设计与优化
- `design-pattern/`：DDD 等设计模式实践
- `frame/`：技术选型笔记
- `schedule/`：定时任务原理与方案探索
- `git/`：Git 使用与 Commit Message 规范
- `linux/`、`curl/`、`nodejs/`、`conda/`：常用开发环境与命令实践

## 如何阅读

你可以按主题目录进入对应文档，也可以直接使用编辑器或命令行搜索关键词：

```bash
rg "关键词"
```

例如：

```bash
rg "RocketMQ"
rg "docker-compose"
rg "SpringCache"
```

多数文档是独立笔记，适合按需查阅；部分目录中包含可运行的配置文件、脚本或示例代码，建议结合文档说明一起使用。

## 仓库结构

```text
.
├── ai/                 # AI、大模型、MCP、Dify、自动化工具
├── docker/             # Docker 与容器实践
├── k8s/                # Kubernetes 与 Helm 示例
├── springboot/         # Spring Boot 集成实践
├── redis/              # Redis 学习与部署
├── rocketmq/           # RocketMQ 学习与部署
├── prometheus/         # Prometheus 监控配置
├── grafana/            # Grafana 部署记录
├── java/               # Java 基础、实践和读书笔记
├── go/                 # Go 学习与示例
├── python3/            # Python 学习与脚本示例
└── README.md
```

更多目录请以仓库实际结构为准。

## 文档约定

- 文件名通常使用英文描述主题，部分中文文档保留原始语境。
- `Use docker deploy ...` / `Use docker-compose deploy ...` 类型文档通常记录组件部署步骤。
- `Integrates ...` 类型文档通常记录 Spring Boot 或 Spring Cloud 集成实践。
- `Learning`、`usage`、`practice` 类型文档通常是概念学习和使用总结。
- 配置文件、脚本、示例工程会尽量放在对应主题目录下。

## 适用场景

- 复习某个技术点的核心概念
- 查找常见组件的 Docker / docker-compose 部署方式
- 记录和复盘实际工程问题
- 沉淀后端、云原生、AI 工具链的实践经验
- 作为个人知识库持续迭代

## 维护方式

新增笔记时建议遵循：

1. 按主题放入已有目录；没有合适目录时再创建新目录。
2. 文档标题尽量表达清楚问题或主题。
3. 部署类文档尽量包含环境、配置、启动命令和验证方式。
4. 问题排查类文档尽量包含现象、原因、解决方案和参考命令。
5. 示例代码或配置应放在对应主题目录下，避免散落在根目录。

## 说明

本仓库主要服务于个人学习和实践沉淀，内容会随着学习过程持续更新。部分笔记可能带有阶段性理解，使用时建议结合具体版本、运行环境和官方文档进行校验。
