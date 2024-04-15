## SpringBoot集成RocketMQ

> RocketMQ快速开始
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
  * 引入RocketMQ客户端依赖（本文使用的是4.7.0版本）
    ```
    <dependency>
        <groupId>org.apache.rocketmq</groupId>
        <artifactId>rocketmq-client</artifactId>
        <version>4.7.0</version>
    </dependency>
    ```
  * 编写生产者与消费者配置文件application.yml
    ```
    rocketmq:
      producer:
        # 生产者类型：同步生产者
        sync:
          # 生产者组名
          groupName: sync_producer_group
          # 路由服务地址
          namesrvAdrr: localhost:9876
          # 消息最大限度
          maxMessageSize: 4096
          # 消息超时时间
          sendMsgTimeout: 3000
          # 消息发送失败重试次数
          retryTimesWhenSendFailed: 2
      consumer:
        # 消费者类型：一般消费者
        normal:
          # 消费者组名
          groupName: consumer_group
          # 路由服务地址
          namesrvAdrr: localhost:9876
          # 订阅主题
          topics: test_topic
          # 消费最小线程数
          consumeThreadMin: 20
          # 消费最大线程数
          consumeThreadMax: 64
          # 一次消费消息条数
          consumeMessageBatchMaxSize: 1
    ```
  * 编写同步生产者配置类
    ```
    /**
    * 同步生产者配置类 用于配置同步生产者Bean
    * Created by Garden on 2020-09-17 21:56
    */
    @Configuration
    public class SyncProducerConfig {
      
      public static final Logger LOGGER = LoggerFactory.getLogger(SyncProducerConfig.class);

      @Value("${rocketmq.producer.sync.groupName}")
      private String groupName;
      @Value("${rocketmq.producer.sync.namesrvAdrr}")
      private String namesrvAddr;
      @Value("${rocketmq.producer.sync.maxMessageSize}")
      private Integer maxMessageSize;
      @Value("${rocketmq.producer.sync.sendMsgTimeout}")
      private Integer sendMsgTimeout;
      @Value("${rocketmq.producer.sync.retryTimesWhenSendFailed}")
      private Integer retryTimesWhenSendFailed;

      @Bean(name = "syncProducer")
      @ConditionalOnMissingBean
      public DefaultMQProducer syncProducer() throws RuntimeException{
        
        //构建同步生产者对象，设置属性
        DefaultMQProducer defaultMQProducer = new DefaultMQProducer(this.groupName);
          //设置NameServer的地址，Producer启动后通过NameServer获取目标Topic的路由信息
        defaultMQProducer.setNamesrvAddr(this.namesrvAddr);
          //设置消息最大限度，默认为4m
        defaultMQProducer.setMaxMessageSize(this.maxMessageSize);
          //设置消息超时时间，默认为3s
        defaultMQProducer.setSendMsgTimeout(this.sendMsgTimeout);
          //设置消息发送失败重试次数，默认为2次
        defaultMQProducer.setRetryTimesWhenSendFailed(this.retryTimesWhenSendFailed);

        //启动实例
        try {
            defaultMQProducer.start();
            LOGGER.info("sync producer start success... groupName={},namesrvAdrr={}",this.groupName,this.namesrvAddr);
        } catch (MQClientException e) {
            LOGGER.error("sync producer start failed... errorMsg={}",e.getErrorMessage());
            throw new RuntimeException(e);
        }

        //返回Bean
        return defaultMQProducer;
      }
    }
    ```
  * 编写一般消费者配置类
    ```
    /**
    * 普通消费者配置类 用于配置普通消费者Bean
    * Created by Garden on 2020-09-17 21:57
    */
    @Configuration
    public class NormalConsumerConfig {

      public static final Logger LOGGER = LoggerFactory.getLogger(NormalConsumerConfig.class);
      
      @Value("${rocketmq.consumer.normal.groupName}")
      private String groupName;
      @Value("${rocketmq.consumer.normal.namesrvAdrr}")
      private String namesrvAddr;
      @Value("${rocketmq.consumer.normal.topics}")
      private String topics;
      @Value("${rocketmq.consumer.normal.consumeThreadMin}")
      private Integer consumeThreadMin;
      @Value("${rocketmq.consumer.normal.consumeThreadMax}")
      private Integer consumeThreadMax;
      @Value("${rocketmq.consumer.normal.consumeMessageBatchMaxSize}")
      private Integer consumeMessageBatchMaxSize;
      
      @Bean(name = "normalConsumer")
      @ConditionalOnMissingBean
      public DefaultMQPushConsumer normalConsumer() throws
      RuntimeException{
        
        //构建普通实时消费者，设置属性
        DefaultMQPushConsumer defaultMQPushConsumer = new
        DefaultMQPushConsumer(this.groupName);
          //设置NameServer的地址，Producer启动后通过NameServer获取目标Topic的路由信息
        defaultMQPushConsumer.setNamesrvAddr(this.namesrvAddr);
          //设置消息实时监听器，用于监听订阅消息，一般用于处理业务逻辑，常独立一个监听类实现
        defaultMQPushConsumer.setMessageListener(new MessageListenerConcurrently(){
          @Override
          public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> msgs, ConsumeConcurrentlyContext context) {
            LOGGER.info("Receive New Messages: thread={},msgs={}", Thread.currentThread().getName(), msgs);
            // 标记该消息已经被成功消费
            return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
          }
        });
          //设置最小线程数以及最大线程数（实时消费者每次消费消息都使用独立的线程）
        defaultMQPushConsumer.setConsumeThreadMin(this.consumeThreadMin);
        defaultMQPushConsumer.setConsumeThreadMax(this.consumeThreadMax);
          //设置一次消费消息的条数，默认为1条
        defaultMQPushConsumer.setConsumeMessageBatchMaxSize(this.consumeMessageBatchMaxSize);
          //设置消费方式：
          // 消息模型（广播或集群，默认为集群）；
        defaultMQPushConsumer.setMessageModel(MessageModel.CLUSTERING);
          // 消费起始位置，设置第一次启动时消费消费队列的队首位置（若非第一次启动，将按照上次消费的位置继续消费）
        defaultMQPushConsumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
        try {
              //设置订阅主题以及对应Tags
            defaultMQPushConsumer.subscribe(this.topics,"*");

            //启动实例
            defaultMQPushConsumer.start();
            LOGGER.info("normal consumer start success... groupName={},namesrvAdrr={},topics={}",this.groupName,this.namesrvAddr,this.topics);
        } catch (MQClientException e) {
            LOGGER.error("normal consumer start failed... errorMsg={}",e.getErrorMessage());
            throw new RuntimeException(e);
        }

        //返回Bean
        return defaultMQPushConsumer;
      }
    }
    ```
  * 编写测试类
    ```
    /**
    * 测试控制器 用于测试生产者的消息发送以及对应消费者的消息消费
    * PS: 每个测试方法都是调用样例
    * Created by Garden on 2020-09-20 14:51
    */
    @RequestMapping("/test")
    @RestController
    public class TestController {
      
      public static final Logger LOGGER = LoggerFactory.getLogger(TestController.class);
      
      @Autowired
      private DefaultMQProducer syncProducer;
      
      @GetMapping("/syncProducer/normalConsumer")
      public String testSyncProducerAndNormalConsumer() throws UnsupportedEncodingException, InterruptedException
            , RemotingException, MQClientException, MQBrokerException {
              
              for (int i = 0; i < 15; i++){
                //创建消息，指定主题Topic，标签Tag，业务标识Key，消息体MsgBody [Tag可用于消息过滤，Key可用于消息查询]
                Message msg = new Message("test_topic","sync_producer_tag"
                    ,"sync_producer_key." + i, ("SyncProducer Msg." + i).getBytes(RemotingHelper.DEFAULT_CHARSET));
                //发送消息至Broker
                SendResult sendResult = syncProducer.send(msg);
                //通过发送结果查看是否发送成功
                LOGGER.info("testSyncProducerAndNormalConsumer... sendResult={}", sendResult);
              }
              return "SUCCESS";
       }
    }
    ```
  * 运行效果
    * 启动NameServer
      
      ![RocketMQ_NameServer.png](https://i.loli.net/2020/11/29/EWTKlSwaevQshHz.png)

    * 启动Broker
      
      ![RocketMQ_Broker.png](https://i.loli.net/2020/11/29/buniSV7QoO8plvf.png)

    * 调试测试用例接口

      ![RocketMQ_Demo_Test.png](https://i.loli.net/2020/11/29/JC2xHGSBufgIXET.png)

  * 常见问题
    * 启动NameServer或者启动Broker失败，日志信息显示"Please set the JAVA_HOME variable in your environment, We need java(x64)!"。此时我们需要编辑其对应的.sh脚本文件（runserver.sh或runbroker.sh）,注释已存在的JDK环境配置，添加指定JDK环境配置，如下：
      ```
      #[ ! -e "$JAVA_HOME/bin/java" ] && JAVA_HOME=$HOME/jdk/java
      #[ ! -e "$JAVA_HOME/bin/java" ] && JAVA_HOME=/usr/java
      #[ ! -e "$JAVA_HOME/bin/java" ] && error_exit "Please set the JAVA_HOME variable in your environment, We need java(x64)!"
      [ ! -e "$JAVA_HOME/bin/java" ] && JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_261.jdk/Contents/Home
      ```

> 参考文献
 * [《SpringBoot 实践系列-集成 RocketMQ》 by glmapper](https://juejin.cn/post/6844904116020314125)
 * [《Apache RocketMQ》](http://rocketmq.apache.org)

> 代码
  * [码云](https://gitee.com/FSDGarden/rocketmq-learn.git)