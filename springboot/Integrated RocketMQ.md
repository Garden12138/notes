## SpringBoot集成RocketMQ

> RocketMQ快速开始
  * 简介：Apache RocketMQ是一个分布式消息传递和流媒体平台，具有低延迟，高性能和可靠性、万亿级容量和灵活的可伸缩性。它提供了许多功能，具体参考：https://github.com/apache/rocketmq
  * 准备：根据[官方快速开始指导手册](http://rocketmq.apache.org/docs/quick-start/)，RocketMQ的使用环境环境需要具备以下条件：
    * 64bit OS，推荐使用Linux/Unix/Mac
    * 64bit JDK 1.8+
    * Maven 3.2x
    * 4g+ free disk for Broker server
  * 下载
    ```
    //选择合适的版本
    https://archive.apache.org/dist/rocketmq/
    //下载zip包
    wget https://archive.apache.org/dist/rocketmq/4.7.0/rocketmq-all-4.7.0-source-release.zip
    ```
  * 安装
    ```
    //解压zip包
    unzip rocketmq-all-4.7.0-source-release.zip
    ```
  * 编译
    ```
    //mvn编译
    cd rocketmq-all-4.7.0/
    mvn -Prelease-all -DskipTests clean install -U
    ```
  * 启动
    ```
    //启动NameServer
    nohup sh bin/mqnamesrv &
    //查看NameSrv日志
    tail -f ~/logs/rocketmqlogs/namesrv.log

    //启动Broker
    nohup sh bin/mqbroker -n localhost:9876 autoCreateTopicEnable=fasle &
    //查看Broker日志
    tail -f ~/logs/rocketmqlogs/broker.log 
    ```
  * 关闭
    ```
    //关闭Broker
    sh bin/mqshutdown broker
    //关闭NameSrv
    sh bin/mqshutdown namesrv
    ```

> SpringBoot集成

> 参考文献

> 代码