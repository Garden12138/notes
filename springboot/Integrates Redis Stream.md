## 集成 Redis Stream

> 简介

* ```Redis5.0```引入```Stream```数据结构，它提供了丰富的消息队列功能，包括数据持久化、分组以及消息消费确认等功能，合适用作消息队列。```Redis Stream```有以下特点：

  * 持久化。支持消息持久化，可以将消息存储在内存中也可选择将消息存储在磁盘上。
  * 多消费者分组。支持消费者分组，每个消费者分组内的多个消费者共享一个消息流，多个消费者并行消费消息。
  * 消息消费确认。消费者可对已处理的消息进行确认，确保消息被正常消费，避免消息的重复消费问题。
  * 消息时间序列。消息在消息流中是有序存储的，每个消息都有唯一的```ID```和时间戳，可按照时间顺序进行消费。
  * 复杂数据结构。支持复杂的数据结构，每个消息可包含多个字段和值。
  * 消费者消费位置。支持控制自身的消费位置，可从头部或尾部开始，也可从特定消息```ID```开始消费。

> 集成步骤

* 封装```RedisStreamUtil```工具类，用于生产者发布、消费者初始化和订阅使用：

  ```bash
  @Component
  public class RedisStreamUtil {

      @Autowired
      private RedisTemplate<String, Object> redisTemplate;

      /**
       * 创建消费组
       */
      public String createGroup(String key, String group) {
          return redisTemplate.opsForStream().createGroup(key, group);
      }

      /**
       * 获取消费者信息
       */
      public StreamInfo.XInfoConsumers queryConsumers(String key, String group) {
          return redisTemplate.opsForStream().consumers(key, group);
      }

      /**
       * 添加Map消息
       */
      public String addMap(String key, Map<String, Object> value) {
          return redisTemplate.opsForStream().add(key, value).getValue();
      }

      /**
       * 读取消息
       */
      public List<MapRecord<String, Object, Object>> read(String key) {
          return redisTemplate.opsForStream().read(StreamOffset.fromStart(key));
      }

      /**
       * 确认消费
       */
      public Long ack(String key, String group, String... recordIds) {
          return redisTemplate.opsForStream().acknowledge(key, group, recordIds);
      }

      /**
       * 删除消息。当一个节点的所有消息都被删除，那么该节点会自动销毁
       */
      public Long del(String key, String... recordIds) {
          return redisTemplate.opsForStream().delete(key, recordIds);
      }

      /**
       * 判断是否存在key
       */
      public boolean hasKey(String key) {
          Boolean aBoolean = redisTemplate.hasKey(key);
          return aBoolean == null ? false : aBoolean;
      }

  }
  ```

* 添加消费者初始化和订阅配置项及其配置项类：

  ```bash
  garden:
    redis:
      mq:
        streams:
          # 消息队列名称（定义为Topic）
          - keyName: stream:producer:1
            # 消费组
            groups:
              - groupName: group_consumers_1
                consumers:
                  # 消费者及其监听器类（消费者类创建后更新全限定类名值）
                  - consumerName: consumer_1
                    listenerClass: 
  ```

  ```bash
  @EnableConfigurationProperties
  @Configuration
  @ConfigurationProperties(prefix = "garden.redis.mq")
  @Data
  public class GardenRedisMqStreamsProperties {

      private List<RedisMqStream> streams;

      @Data
      public static class RedisMqStream {
          private String keyName;
          private List<RedisMqGroup> groups;
      }

      @Data
      public static class RedisMqGroup {
          private String groupName;
          private List<RedisMqConsumers> consumers;
      }

      @Data
      public static class RedisMqConsumers {
          private String consumerName;
          private String listenerClass;
      }

  }
  ```

* 封装消费者初始化配置类：

  ```bash
  @Component
  public class RedisMqStreamConfig {

      @Autowired
      private RedisStreamUtil redisStreamUtil;
      @Autowired
      private GardenRedisMqStreamsProperties gardenRedisMqStreamsProperties;
      @Autowired
      public ThreadPoolTaskExecutor executor;


      @Bean
      public List<Subscription> subscription(LettuceConnectionFactory factory) throws ClassNotFoundException, InstantiationException, IllegalAccessException {

          List<Subscription> resultList = new ArrayList<>();

          // 配置Stream监听容器选项
          StreamMessageListenerContainer.StreamMessageListenerContainerOptions<String, MapRecord<String, String, String>> options =
                  StreamMessageListenerContainer
                          .StreamMessageListenerContainerOptions
                          .builder()
                          .batchSize(5)
                          .executor(executor)
                          .pollTimeout(Duration.ofSeconds(1))
                          .build();
          // 创建Stream监听容器
          StreamMessageListenerContainer<String, MapRecord<String, String, String>> listenerContainer =
                  StreamMessageListenerContainer.create(factory, options);
          // 遍历RedisMqStream
          for (GardenRedisMqStreamsProperties.RedisMqStream redisMqStream : gardenRedisMqStreamsProperties.getStreams()) {
              String keyName = redisMqStream.getKeyName();
              List<GardenRedisMqStreamsProperties.RedisMqGroup> groups = redisMqStream.getGroups();
              // 初始化Stream，创建Stream并创建对应的消费组
              for (GardenRedisMqStreamsProperties.RedisMqGroup group : groups) {
                  initStream(keyName, group.getGroupName());
                  // 遍历每个消费者配置,动态创建监听器实例并订阅
                  for (GardenRedisMqStreamsProperties.RedisMqConsumers redisMqConsumers : group.getConsumers()) {
                      Consumer consumer = Consumer.from(group.getGroupName(), redisMqConsumers.getConsumerName());
                      String listenerClass = redisMqConsumers.getListenerClass();
                      StreamListener listener = (StreamListener) Class.forName(listenerClass).newInstance();
                      Subscription subscription = listenerContainer.receiveAutoAck(consumer,
                              StreamOffset.create(keyName, ReadOffset.lastConsumed()), listener);
                      resultList.add(subscription);
                  }
              }
              // 启动监听容器
              listenerContainer.start();
          }

          return resultList;
      }

      /**
       * 初始化Stream，如果不存在，则创建Stream和对应的消费组
       *
       * @param key   Stream的键名
       * @param group 消费组的名称
       */
      private void initStream(String key, String group) {
          boolean hasKey = redisStreamUtil.hasKey(key);
          if (!hasKey) {
              // 如果Stream不存在，则创建Stream、添加初始数据和创建消费组
              Map<String, Object> map = Collections.singletonMap("key", "value");
              String result = redisStreamUtil.addMap(key, map);
              redisStreamUtil.createGroup(key, group);
              redisStreamUtil.del(key, result);
          }
      }

  }
  ```

* 创建消费者，完成消费信息逻辑：

  ```bash
  package com.garden.consumer.listener;

  @Slf4j
  @Component
  public class RedisStreamConsumer1 implements StreamListener<String, MapRecord<String, String, String>> {

      @Override
      public void onMessage(MapRecord<String, String, String> message) {
          try {
              RedisStreamUtil redisStreamUtil = ConsumerApplication.ac.getBean(RedisStreamUtil.class);
              String streamKey = message.getStream();
              RecordId recordId = message.getId();
              Map<String, String> msg = message.getValue();
              // 模拟业务逻辑实现
              log.info("RedisStreamConsumer1 stream: {}, messageId: {}, message: {}", streamKey, recordId, msg);
              redisStreamUtil.ack(streamKey, "group_consumers_1", recordId.getValue());
              redisStreamUtil.del(streamKey, recordId.getValue());
          } catch (Exception e) {
              log.error("RedisStreamConsumer1 deal message occur exception: {}", e.getMessage());
          }
      }

  }
  ```

  将消费者类路径更新至消费者初始化和订阅配置项：

  ```bash
  listenerClass: com.garden.consumer.listener.RedisStreamConsumer1
  ```

* 生产者发布消息：

  ```bash
  @Component
  public class RedisMessageQueueProducer {

    @Autowired
    private RedisStreamUtil redisStreamUtil;

    public void sendMessageByStream(String topic, String message) {
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", message);
        msg.put("createTime", new Date());
        redisStreamUtil.addMap(topic, msg);
    }

  }
  ```

  ```bash
  @Slf4j
  @RestController
  @RefreshScope
  public class ConsumerController {

      @Autowired
      private RedisMessageQueueProducer redisMessageQueueProducer;

      @GetMapping("/redisMessageQueueProducer")
      public String redisMessageQueueProducer(@RequestParam String method, @RequestParam String topic, @RequestParam String message) {
        redisMessageQueueProducer.sendMessageByStream(topic, message);
        return "success";
      }

  }
  ```

> 参考文献

* [【SpringBoot】使用 Redis 就可以当作MQ使用啦 ~](https://juejin.cn/post/7317158687441371171)