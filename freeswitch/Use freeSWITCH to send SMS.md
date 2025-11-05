## 使用freeSWITCH实现短信发送

### 什么是freeSWITCH

* ```freeSWITCH```是一个强大的开源通信平台，本质上是一个电话的软交换解决方案包括一个软件电话和软交换机，用以提供语音、视频、IM等通信服务；它也可以作为交换机引擎、```PBX```以及多媒体网关使用。

* 特点：跨平台、开源、高性能、模块化（扩展功能）、多协议。

### 针对短信发送场景，有以下实现方式

* 对接物理语音网关设备，如```AIO100```（```SIM``卡）：

  * 部署```freeSWITCH```
  * 网关设备注册```SIP```（```freeSWITCH```服务）
  * 网关设备配置短信路由
  * ```freeSWITCH```配置网关设备信息，重启或重新加载配置
  * ```freeSWITCH```客户端命令发送短信

    ```bash
    fs_cli --execute="chat sip|noreply@mydomain|external/sip:${手机号码}@${网关设备IP}:${网关设备端口}|${短信文本内容}"
    ```
  
  此种方式发送能力在网关设备。

* 使用```freeSWITCH```的拨号计划（```Dialplan```）或其他机制触发扩展模块的调用，比如使用```mod_xml_rpc```或```mod_xml_curl```模块对短信服务平台进行接口调用、使用```socket```对于已实现短信对接的```flask web```应用进行接口调用：

  ```bash
  <extension name="send_sms_via_curl">
    <condition field="destination_number" expression="^1001$">
      <action application="set" data="content_type=application/json"/>
      <action application="set" data="api_url=http://your_server_ip:5000/send_sms"/>
      <action application="set" data="to_number=+0987654321"/>
      <action application="set" data="message=Hello%20from%20FreeSWITCH!"/>
      <action application="set" data="post_data='{\"to_number\":\"${to_number}\",\"message\":\"${message}\"}'"/>
      <action application="curl" data="${api_url} -d ${post_data} -H 'Content-Type: ${content_type}'"/>
      <!-- 其他动作，如播放音频或挂断电话 -->
      <action application="hangup"/>
  </condition>
  </extension>
  ```

  此种方式发送能力在于提供的接口服务（通道服务），理论上是传递```http```协议的请求，所以发送号码应该都能在提供的接口服务（通道服务）上获取。但这种方式依赖于拨号计划或者嵌套字触发，没法直接调用。

* 使用基于```freeSWITCH```实现的```signalwire```产品平台，只需要在平台上注册项目以及对应```TOKEN```，就可以使用其产品特性，```Relay.Messaging```，有对应的```SDK```，如```python```：

  ```bash
  result = await client.messaging.send(context='office', from_number='+1XXXXXXXXXX', to_number='+1YYYYYYYYYY', body='Welcome at SignalWire!')
  if result.successful:
    print(f'Message ID: {result.message_id}')
  ```

  此种方式发送能力在于```signalwire```平台。如果使用```Relay Task```以及```Relay Consumer```则可实现消息的发送与接收，在接收方实现通道服务的调用即可：
  
  ```bash
  # 发送方
  # create-task.py
  from signalwire.relay.task import Task

  project = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
  token = 'PTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
  task = Task(project=project, token=token)
  success = task.deliver('office', {
    'uuid': 'unique id',
    'data': 'data for your job'
  })
  if success:
    print('Task delivered')
  else:
    print('Error delivering task..')
  ```
  
  ```bash
  # 接收方
  from signalwire.relay.consumer import Consumer

  class CustomConsumer(Consumer):
    def setup(self):
      self.project = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
      self.token = 'PTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
      self.contexts = ['office']

    async def on_task(self, message):
      print('Handle inbound task')
      print(message['uuid']) # => 'unique id'
      print(message['data']) # => 'data for your job'
      # 调用通道服务，如发送短信

  consumer = CustomConsumer()
  consumer.run()
  ```
  
  此种方式发送能力在于通道服务。
  
* 使用freeSWITCH Event事件机制实现短信发送

  * 部署```freeSWITCH```，可使用第三方提供的Docker镜像，如```safarov/freeswitch```

    ```bash
    docker run -d \
             -p 8021:8021/tcp \
             --net=host \
             --name freeswitch \
             -v ./conf/:/etc/freeswitch \
             safarov/freeswitch
    ```
  
  * 编写自定义发送短信事件（```Python ESL```脚本）
    
    ```python
    # -*- coding: utf-8 -*-
    import ESL
    import json
    import sys
    import logging

    # 配置日志记录
    logging.basicConfig(level=logging.INFO,  # 设置日志级别
                    format='%(message)s',  # 设置日志格式
                    datefmt='%Y-%m-%d %H:%M:%S',  # 设置日期和时间格式
                    handlers=[  # 设置处理器
                        logging.FileHandler("client-app.log"),  # 将日志写入文件
                        logging.StreamHandler()  # 将日志输出到控制台
                    ])

    # 获取日志记录器
    logger = logging.getLogger(__name__)
    
    text = sys.argv[1]
    mobile = sys.argv[2]
       
    try:
        con = ESL.ESLconnection("localhost", "8021", "ClueCon")

        event = {
            'text': text,
            'mobile': mobile
        }

        con.api("event", json.dumps(event, ensure_ascii=False))
        con.disconnect()
        logger.info(json.dumps({'result': 0, 'message': 'send event success'}))
    except:
        errorMsg = 'send event occur unexpected error:' + sys.exc_info()[0] 
        logger.error(json.dumps({'result': 1, 'message': errorMsg}))
    ```

    执行方式：

    ```bash
    python3 client.py 【签名】发送内容 13111111111
    ```

  * 编写监听发送事件（Python ESL脚本），事件执行逻辑包含发送短信的操作

    ```python
    # -*- coding: utf-8 -*-

    import ESL
    import hashlib
    import json
    import time
    import urllib.parse
    import requests
    import logging
    from datetime import datetime

    # 配置日志记录
    logging.basicConfig(level=logging.DEBUG,  # 设置日志级别
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 设置日志格式
                    datefmt='%Y-%m-%d %H:%M:%S',  # 设置日期和时间格式
                    handlers=[  # 设置处理器
                        logging.FileHandler("listener-app.log"),  # 将日志写入文件
                        logging.StreamHandler()  # 将日志输出到控制台
                    ])

    # 获取日志记录器
    logger = logging.getLogger(__name__)

    def on_event(event):
        if event.getHeader('Event-Name') == 'API':
            args = event.getHeader('API-Command-Argument')
            logger.info(f'Received API event: {args}')
            logger.info('Call ended, here is your test SMS!')
            send_args = json.loads(args)
            #text_send_single(send_args['text'], send_args['mobile'])

    con = ESL.ESLconnection('localhost', '8021', 'ClueCon')

    if con.connected():
        con.events('plain', 'all')
        while 1:
            e = con.recvEvent()
            if e:
                #logger.info(e.serialize())
                on_event(e)
    ```

    启动方式：
    
    ```bash
    python3 listener.py &
    ```

    关闭方式；

    ```bash
    kill -9 $(ps -ef | grep 'listener.py' | awk '{print $2}')
    ``` 

  * 效果如下：

    * 执行发送：
      
      ```bash
      python3 client.py 【签名】发送内容 13111111111
      ```

    * 接收方：

      ```bash
      2025-11-05 16:17:33 - __main__ - INFO - Received API event: {"text": "【签名】发送内容", "mobile": "13111111111"}
      2025-11-05 16:17:33 - __main__ - INFO - Call ended, here is your test SMS!
      ```

### 注意事项

* 安装```ESL```模块，使用```pip3 install ESL```命令安装前，需要更新```swig```到旧版本如```swig==3.0.12```：

  ```bash
  # 卸载当前版本swig
  sudo dnf remove -y swig
  
  # 安装旧版本swig=3.0.12
  cd /usr/local/src
  sudo curl -LO https://github.com/swig/swig/archive/refs/tags/v3.0.12.tar.gz
  sudo tar xvf v3.0.12.tar.gz
  cd swig-3.0.12
  sudo ./autogen.sh
  sudo ./configure
  sudo make -j$(nproc)
  sudo make install

  # 确认版本
  swig -version

  # 安装ESL模块
  pip3 install python-ESL
  ```


### 参考文献
* [官方开发者文档](https://developer.signalwire.com/freeswitch/FreeSWITCH-Explained/)
* [官方仓库](https://github.com/signalwire/freeswitch/tree/master)
* [Freeswitch的Docker镜像构建](https://www.cnblogs.com/fortuneju/p/18777204)
* [freeswitch笔记(3)-esl入门](https://cloud.tencent.com/developer/article/1585511)
* [Freeswitch服务+语音网关设备发送短信功能](https://blog.csdn.net/giscong/article/details/124155466)
* [最全FreeSwitch 1.10.9 Linux通用编译部署教程](https://blog.csdn.net/qq_36369267/article/details/131564019)
* [Python ESL](https://developer.signalwire.com/freeswitch/FreeSWITCH-Explained/Client-and-Developer-Interfaces/Python-ESL/)