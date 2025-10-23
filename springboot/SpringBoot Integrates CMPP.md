## Spring Boot集成CMPP协议通信

### 介绍

* 是中国移动通信协议（```China Mobile Peer to Peer```协议），主要用于企业短信发送系统（```SP，Service Provider```）与短信网关（```ISMG```）之间的通信。常用的版本有```CMPP2.0```、```CMPP3.0```。本文主要以```CMPP3.0```协议为例。

### 协议通信主要流程

* 建立连接（```CMPP_CONNECT```），企业短信发送系统（客户端）与短信网关（服务端）建立```TCP```连接，并进行鉴权。
* 提交短信（```CMPP_SUBMIT```），企业短信发送系统（客户端）向短信网关（服务端）提交短信（号码、内容）。
* 网关响应（```CMPP_SUBMIT_RESP```），短信网关（服务端）向企业短信发送系统（客户端）返回提交结果。
* 状态报告（```CMPP_DELIVER```），短信网关（服务端）向企业短信发送系统（客户端）发送状态报告。
* 链路检测（```CMPP_ACTIVE_TEST```），用于保持```TCP```连接的活跃性。
* 终止连接（```CMPP_TERMINATE```）。

### 使用SMSGate框架，SpringBoot集成实现服务端

* 引入```SMSGate```依赖：

  ```xml
  <dependency>
      <groupId>com.chinamobile.cmos</groupId>
      <artifactId>sms-core</artifactId>
      <version>2.1.13.6</version>
  </dependency>
  ```

* 定义服务端处理抽象类，重新管道接收```channelRead```（用于接收信息，返回发送响应等）方法以及自定义处理器userEventTriggered（用于开启回执发送）方法：

  ```java
  public abstract class ServerHandler extends AbstractBusinessHandler {

      protected static final Logger logger = LoggerFactory.getLogger(ServerHandler.class);

      private static final AtomicInteger sequenceId = new AtomicInteger(RandomUtils.nextInt());

      protected long delay = 60000L;

      protected DefaultPromise sendOver = new DefaultPromise(GlobalEventExecutor.INSTANCE);

      public long getDelay() {
          return delay;
      }

      public void setDelay(long delay) {
          this.delay = delay;
      }

      public DefaultPromise getSendOver() {
          return this.sendOver;
      }

      public ServerHandler() {
      }

      public ServerHandler(long delay, DefaultPromise sendOver) {
          this.delay = delay;
          this.sendOver = sendOver;
      }

      protected abstract List<CmppDeliverRequestMessage> createCmppDeliverRequestMessages(String userName);

      protected abstract boolean send(String ak, String[] phones, String content, MsgId msgId);

      protected abstract void handleCmppDeliverResponse(String userName, CmppDeliverResponseMessage e);

      /**
       * 获取消息ID体
       *
       * @param msgid
       * @return
       */
      private MsgId getMsgid(MsgId msgid) {
          return Objects.nonNull(msgid) ? msgid : new MsgId(sequenceId.incrementAndGet() & 0x3fffff);
      }

      /**
       * 管道接收channelRead（用于接收信息，返回发送响应等）
       *
       * @param ctx
       * @param msg
       * @throws Exception
       */
      @Override
      public void channelRead(final ChannelHandlerContext ctx, Object msg) throws Exception {

          CMPPServerChildEndpointEntity ce = (CMPPServerChildEndpointEntity) this.getEndpointEntity();
          logger.info("server receive message: {} from customer: {}", msg.toString(), ce.getUserName().concat("@").concat(ce.getPassword()));

          // 针对每种消息需要做对应处理
          if (msg instanceof CmppSubmitRequestMessage) {
              // 接收短信发送请求（将短信消息投放至消息队列后做出响应）
              CmppSubmitRequestMessage e = (CmppSubmitRequestMessage) msg;
              // 发送短信
              boolean successful = send(ce.getUserName(), e.getDestterminalId(), e.getMsgContent(), getMsgid(e.getMsgid()));
              CmppSubmitResponseMessage responseMessage = new CmppSubmitResponseMessage(e.getHeader().getSequenceId());
              if (successful) {
                  responseMessage.setMsgId(e.getMsgid());
                  responseMessage.setResult(0);
              } else {
                  responseMessage.setResult(-1);
              }
              ctx.channel().writeAndFlush(responseMessage);
          } else if (msg instanceof CmppDeliverResponseMessage) {
              // 接收回执消息响应并进行处理
              CmppDeliverResponseMessage e = (CmppDeliverResponseMessage) msg;
              handleCmppDeliverResponse(ce.getUserName(), e);
          } else {
              ctx.fireChannelRead(msg);
          }

      }

      /**
       * 自定义处理器userEventTriggered（用于开启回执发送）
       *
       * @param ctx
       * @param evt
       * @throws Exception
       */
      @Override
      public void userEventTriggered(final ChannelHandlerContext ctx, Object evt) throws Exception {
          if (evt == SessionState.Connect) {

              final Channel ch = ctx.channel();
              EventLoopGroupFactory.INS.submitUnlimitCircleTask(new Callable<Boolean>() {

                  @Override
                  public Boolean call() throws Exception {
                      // 每隔一段时间（delay）查询消息队列获取需发送的回执信息
                      // 创建回执请求消息
                      CMPPServerChildEndpointEntity ce = (CMPPServerChildEndpointEntity) getEndpointEntity();
                      List<CmppDeliverRequestMessage> msgList = createCmppDeliverRequestMessages(ce.getUserName());
                      for (CmppDeliverRequestMessage msg : msgList) {
                          // 异步发送
                          ChannelFuture channelFuture = ChannelUtil.asyncWriteToEntity(ce.getId(), msg);
                          try {
                              channelFuture.addListener(new GenericFutureListener<ChannelFuture>() {
                                  @Override
                                  public void operationComplete(ChannelFuture future) throws Exception {
                                      if (future.isSuccess()) {
                                          // logger.info("server send success, response:{}", future.get());
                                      } else {
                                          // logger.error("server send failed, response:" + future.cause());
                                      }
                                  }
                              });
                              // channelFuture.sync(); //阻塞线程，等待异步结果返回，此处可不接收结果，接收结果可由channelRead统一完成
                          } catch (Exception e) {
                              logger.error("server send occur exception:" + e.getMessage());
                          }
                      }
                      return true;
                  }
              }, new ExitUnlimitCirclePolicy<Boolean>() {
                  @Override
                  public boolean notOver(Future<Boolean> future) {
                      if (future.cause() != null) {
                          logger.error("server occur exception:" + future.cause() + " when over");
                      }
                      boolean active = ch.isActive();
                      if (!active) {
                          logger.info("server channel is not active, over");
                          sendOver.trySuccess(0);
                          // ch.writeAndFlush(new CmppTerminateRequestMessage());
                      }
                      return active;
                  }
              }, delay);
          }
          ctx.fireUserEventTriggered(evt);
      }

      @Override
      public String name() {
          return "ServerHandler";
      }

  }
  ```

* 定义服务端处理实现类，继承```ServerHandler```实现抽象方法```send```、```createCmppDeliverRequestMessages```以及```handleCmppDeliverResponse```：

 ```java
 public class CMPPServerHandler extends ServerHandler {

    public CMPPServerHandler(long delay) {
        super.delay = delay;
    }

    /**
     * 发送短信
     *
     * @param username  用户名
     * @param phones    手机号
     * @param content   短信内容
     * @param msgId     消息ID
     * @return
     */
    @Override
    protected boolean send(String username, String[] phones, String content, MsgId msgId) {
        if (StringUtils.isBlank(username) || phones.length == 0 || StringUtils.isBlank(content)) {
            logger.error("CMPPServerHandler send fail, param is null");
            return false;
        }
        try {
            for (String phone : phones) {
                // TODO 发送短信
                logger.info("CMPPServerHandler send success, send message:{} to kafka", JSON.toJSONString(message));
            }
            return true;
        } catch (Exception e) {
            logger.error("CMPPServerHandler send fail, send message to kafka error:{}", e.getMessage());
            return false;
        }

    }

    /**
     * 创建回执请求消息
     *
     * @param username
     * @return
     */
    @Override
    protected List<CmppDeliverRequestMessage> createCmppDeliverRequestMessages(String username) {
        List<CmppDeliverRequestMessage> messages = new ArrayList<>();
        // TODO 查询消息队列获取需发送的回执信息rptList
        logger.info("创建通知客户的回执请求，读取文本短信的回执消息：{} ", JSON.toJSONString(rptList));
        for (ReportMessage rpt : rptList) { // TODO ReportMessage自行定义
            CmppDeliverRequestMessage cmppDeliverRequestMessage = new CmppDeliverRequestMessage();
            // 设置报告消息
            CmppReportRequestMessage cmppReportRequestMessage = new CmppReportRequestMessage();
            MsgId msgId = new MsgId(rpt.getPkSmsId());
            cmppReportRequestMessage.setMsgId(msgId);
            cmppReportRequestMessage.setStat(rpt.getResultCode());
            cmppReportRequestMessage.setSubmitTime(rpt.getSendTime());
            cmppReportRequestMessage.setDoneTime(rpt.getReportTime());
            cmppReportRequestMessage.setDestterminalId(rpt.getPhoneNumber());
            cmppReportRequestMessage.setSmscSequence(msgId.getSequenceId());
            // 设置回执消息
            cmppDeliverRequestMessage.setMsgId(msgId);
            cmppDeliverRequestMessage.setDestId(rpt.getPkSmsId());
            cmppDeliverRequestMessage.setSrcterminalId(rpt.getPhoneNumber());
            cmppDeliverRequestMessage.setSequenceNo(msgId.getSequenceId());
            cmppDeliverRequestMessage.setReportRequestMessage(cmppReportRequestMessage);
            messages.add(cmppDeliverRequestMessage);
        }
        return messages;

    }

    /**
     * 处理CMPPDeliverResponse消息
     *
     * @param userName
     * @param e
     */
    @Override
    protected void handleCmppDeliverResponse(String userName, CmppDeliverResponseMessage e) {
        // TODO 处理回执消息
    }

 }
 ```

* 定义```CMPP```服务端配置属性类，用于服务端初始化：

  ```java
  @Data
  public class CmppServerPropertiesChild {

      private Boolean valid;
      private Short retryWaitTimeSec;
      private Short maxRetryCnt;
      private Boolean isReSendFailMsg;
      private Boolean proxyProtocol;
  }
  ```

  ```java
  @Data
  public class CmppServerProperties {

      private String id;
      private String host;
      private Integer port;
      private boolean useSSL;
      private Long handlerDelay;
      private CmppServerPropertiesChild child;
  }
  ```

* 定义```CMPP```服务端```bean```配置类，初始化服务端：

  ```java
  @Slf4j
  @Configuration
  public class ServerConfig {

      @Autowired
      private CmppServerProperties cmppServerProperties;

      /**
       * 从MySQL中添加子端点
       *
       * @param server CMPPServerEndpointEntity
       */
      private void addChildEndpointsFromDatasource(CMPPServerEndpointEntity server) {
          // TODO 从数据源中获取子端点信息dtoList
          for (CMPPServerChildEndpointDto dto : dtoList) { // TODO CMPPServerChildEndpointDto自行定义
              CMPPServerChildEndpointEntity child = new CMPPServerChildEndpointEntity();
              child.setId(dto.getClientId());
              child.setChartset(Charset.forName("utf-8"));
              child.setGroupName(dto.getGroupName());
              child.setUserName(dto.getUserName());
              child.setPassword(dto.getPassword());
              child.setValid(cmppServerProperties.getChild().getValid());
              child.setVersion(dto.getVersion());
              child.setMaxChannels(dto.getMaxChannels());
              child.setRetryWaitTimeSec(cmppServerProperties.getChild().getRetryWaitTimeSec());
              child.setMaxRetryCnt(cmppServerProperties.getChild().getMaxRetryCnt());
              child.setReSendFailMsg(cmppServerProperties.getChild().getReSendFailMsg());
              child.setProxyProtocol(cmppServerProperties.getChild().getProxyProtocol());
              child.setWriteLimit(dto.getWriteLimit());
              child.setReadLimit(dto.getReadLimit());
              List<BusinessHandlerInterface> serverhandlers = new ArrayList<BusinessHandlerInterface>();
              serverhandlers.add(new CMPPServerHandler(cmppServerProperties.getHandlerDelay()));
              child.setBusinessHandlerSet(serverhandlers);
              server.addchild(child); // 添加客户端点
          }
      }

     
      /**
       * 初始化服务端点
       */
      @Bean
      public CMPPServerEndpointEntity sendServer() {
          // 设置服务端点
          CMPPServerEndpointEntity server = new CMPPServerEndpointEntity();
          server.setId(cmppServerProperties.getId()); // 设置服务端ID
          server.setHost(cmppServerProperties.getHost()); // 设置服务端IP
          server.setPort(cmppServerProperties.getPort()); // 设置服务端端口
          server.setValid(true); // 设置服务端口是否有效
          server.setUseSSL(cmppServerProperties.isUseSSL()); // 使用ssl加密数据流
          server.setOverSpeedSendCountLimit(0); // 关闭默认因CMPP协议接收到错误码为8的响应而重试30次的功能
          // 查询数据源客户端配置，初始化客户端点并添加至服务端点监听
          addChildEndpointsFromDatasource(server);
          return server;
      }

      /**
       * 初始化服务端管理器
       * @param sendServer 服务端点
       */
      @Bean
      public EndpointManager endpointManager(CMPPServerEndpointEntity sendServer) {
          EndpointManager manager = EndpointManager.INS;
          manager.addEndpointEntity(smsServer);
          manager.openEndpoint(smsServer);
          log.info("CMPP server started on {}:{}", smsServer.getHost(), smsServer.getPort());
          return manager;
      }


  }
  ```

* 附加功能，可以实现注册、注销以及修改```CMPP```服务子节点：

  ```java
  @Slf4j
  @Service
  public class CMPPServerService {

      @Autowired
      private CMPPServerEndpointEntity sendServer;

      @Autowired
      private CmppServerProperties cmppServerProperties;

      /**
       * 注册子端点
       *
       * @param dto 子端点信息
       */
      public void register(CMPPServerChildEndpointDto dto) { // TODO CMPPServerChildEndpointDto自行定义
          CMPPServerChildEndpointEntity child = new CMPPServerChildEndpointEntity();
          child.setId(dto.getClientId());
          child.setChartset(Charset.forName("utf-8"));
          child.setGroupName(dto.getGroupName());
          child.setUserName(dto.getUserName());
          child.setPassword(dto.getPassword());
          child.setValid(cmppServerProperties.getChild().getValid());
          child.setVersion(dto.getVersion());
          child.setMaxChannels(dto.getMaxChannels());
          child.setRetryWaitTimeSec(cmppServerProperties.getChild().getRetryWaitTimeSec());
          child.setMaxRetryCnt(cmppServerProperties.getChild().getMaxRetryCnt());
          child.setReSendFailMsg(cmppServerProperties.getChild().getReSendFailMsg());
          child.setProxyProtocol(cmppServerProperties.getChild().getProxyProtocol());
          child.setWriteLimit(dto.getWriteLimit());
          child.setReadLimit(dto.getReadLimit());
          List<BusinessHandlerInterface> serverhandlers = new ArrayList<BusinessHandlerInterface>();
          serverhandlers.add(new CMPPServerHandler(cmppServerProperties.getHandlerDelay()));
          child.setBusinessHandlerSet(serverhandlers);
          // 每个服务端都监听
          server.addchild(child);
          manager.addEndpointEntity(server);

      }


      /**
       * 注销子端点
       *
       * @param clientId 子端点ID
       */
      public void logout(String clientId) {
          CMPPServerChildEndpointEntity child = (CMPPServerChildEndpointEntity) server.getChild(clientId);
          if (Objects.nonNull(child)) {
              // TODO 注销前可能需要检查下节点是否正在使用发送短信
              log.info("注销CMPP服务子节点：{}", clientId);
              server.removechild(child);
              manager.remove(child.getId());
          } else {
              log.warn("CMPP服务子节点不存在，无法注销：{}", clientId);
          }
      }


      /**
       * 修改子端点
       *
       * @param clientId 子端点ID    
       * @param dto 子端点信息
       */
      public void modify(String clientId, CMPPServerChildEndpointDto dto) { // TODO CMPPServerChildEndpointDto自行定义

          CMPPServerChildEndpointEntity child = (CMPPServerChildEndpointEntity) server.getChild(clientId);
          if (Objects.nonNull(child)) {
              log.info("修改CMPP服务子节点：{}", key);
              child.setChartset(Charset.forName("utf-8"));
              child.setGroupName(dto.getGroupName());
              child.setUserName(dto.getUserName());
              child.setPassword(dto.getPassword());
              child.setValid(cmppServerProperties.getChild().getValid());
              child.setVersion(dto.getVersion());
              child.setMaxChannels(dto.getMaxChannels());
              child.setRetryWaitTimeSec(cmppServerProperties.getChild().getRetryWaitTimeSec());
              child.setMaxRetryCnt(cmppServerProperties.getChild().getMaxRetryCnt());
              child.setReSendFailMsg(cmppServerProperties.getChild().getReSendFailMsg());
              child.setProxyProtocol(cmppServerProperties.getChild().getProxyProtocol());
              child.setWriteLimit(dto.getWriteLimit());
              child.setReadLimit(dto.getReadLimit());
              server.addchild(child);
              manager.addEndpointEntity(server);
          } else {
              log.warn("CMPP服务子节点不存在，无法修改：{}", key);
          }

      }

  }
  ```

### 参考文献

* [SMSGate](https://github.com/Lihuanghe/SMSGate)