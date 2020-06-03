## 为什么选择RocketMQ
### 动力
  * 在早期阶段，我们构建了基于ActiveMQ 5.x（小于5.3）的分布式消息中间件。我们的国际业务使用它应用于异步通信，搜索，社交网络活动流，数据通道，甚至在贸易进程方面。随着我们贸易业务吞吐量地不断提升，来源于信息集群的压力也迫在眉睫。
### 为什么选择RocketMQ ?
  * 基于我们不断探索发现，随着队列以及虚拟主题使用地增加，ActiveMQ IO 模型遇到了瓶颈。我们尽最大努力尝试通过节流，熔断器或者降级方式解决这些问题，但都没有取到比较好的效果。所以在那段时间我们开始关注比较流行的消息传递方案Kafka。不幸的是，Kafka不能够满足我们的需求，特别是低延迟和高可靠性其中一直，了解详情点击[这里](http://rocketmq.apache.org/rocketmq/how-to-support-more-queues-in-rocketmq/)
### RocketMQ vs.ActiveMQ vs.Kafka