## 使用freeSWITCH实现短信发送

## 介绍
freeSWITCH是一个强大的开源通信平台，本质上是一个电话的软交换解决方案包括一个软件电话和软交换机，用以提供语音、视频、IM等通信服务；它也可以作为交换机引擎、PBX以及多媒体网关使用。

## 特点
跨平台、开源、高性能（C）、模块化（扩展功能）、多协议

## 针对短信发送场景，有以下实现方式：
* 对接物理语音网关设备，如AIO100（SIM卡）
  * 部署freeSWITCH
  * 网关设备注册SIP（freeSWITCH服务）
  * 网关设备配置短信路由
  * freeSWITCH配置网关设备信息，重启或重新加载配置
  * freeSWITCH客户端命令发送短信
    ```bash
    fs_cli --execute="chat sip|noreply@mydomain|external/sip:${手机号码}@${网关设备IP}:${网关设备端口}|${短信文本内容}"
    ```
  
  此种方式发送能力在网关设备。

* 使用freeSWITCH的拨号计划（Dialplan）或其他机制触发扩展模块的调用，比如使用mod_xml_rpc或mod_xml_curl模块对短信服务平台进行接口调用、使用socket对于已实现短信对接的flask web应用进行接口调用：
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

  此种方式发送能力在于提供的接口服务（通道服务），理论上是传递http协议的请求，所以发送号码应该都能在提供的接口服务（通道服务）上获取。但这种方式依赖于拨号计划或者嵌套字触发，没法直接调用。

* 使用基于freeSWITCH实现的signalwire产品平台，只需要在平台上注册项目以及对应TOKEN，就可以使用其产品特性，Relay.Messaging，有对应的SDK，如python：
  ```bash
  result = await client.messaging.send(context='office', from_number='+1XXXXXXXXXX', to_number='+1YYYYYYYYYY', body='Welcome at SignalWire!')
  if result.successful:
    print(f'Message ID: {result.message_id}')
  ```
  此种方式发送能力在于signalwire平台。如果使用Relay Task以及Relay Consumer则可实现消息的发送与接收，在接收方实现通道服务的调用即可：
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
  
## 使用freeSWITCH实现短信发送思路
  * 部署freeSWITCH
  * 编写自定义发送短信事件（Python ESL脚本）
    
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

    #logger.info(f"输入的参数text:{text}，mobile:{mobile}") 
       
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
    ```bash
    python3 client.py 【博今网络】测试文本短信发送 13710385821
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

    def calculate_md5(text):
        md5_hash = hashlib.md5()
        md5_hash.update(text.encode('utf-8'))
        return md5_hash.hexdigest()

    def url_code(text):
        return urllib.parse.quote(text)

    def text_send_single(text, mobile):
        account = 'JG8347'
        http_sign_Key = "202013"

        input_text = str(account) + "00000000" + http_sign_Key + str(time := datetime.now().strftime("%m%d%H%M%S"))
        url = ''
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(
            url,
            data=json.dumps(
                {"userid": f"{account}", "pwd": f"{calculate_md5(input_text)}", "mobile": mobile,
                 "content": f"{url_code(text)}",
                 "timestamp": f"{time}"}),
            headers=headers
        )
        logger.info(response.json())

    def on_event(event):
        if event.getHeader('Event-Name') == 'API':
            args = event.getHeader('API-Command-Argument')
            logger.info(f'{args}')
            logger.info('Call ended, here is your test SMS!')
            send_args = json.loads(args)
            text_send_single(send_args['text'], send_args['mobile'])

    con = ESL.ESLconnection('localhost', '8021', 'ClueCon')

    if con.connected():
        con.events('plain', 'all')
        while 1:
            e = con.recvEvent()
            if e:
                #logger.info(e.serialize())
                on_event(e)
    ```
    ```bash
    python3 listener.py &
    ps -ef | grep 'python3'
    kill -9 pid
    ```
  
  * 编写自定义发送短信事件web服务

    ```python
    # -*- coding: utf-8 -*-
    from flask import Flask, request, jsonify
    import subprocess

    app = Flask(__name__)

    @app.route('/execute-client', methods=['POST'])
    def execute_client():
        text = request.json.get('text')
        #mobile = request.json.get('mobile')
        mobiles = request.json.get('mobiles')
        mobile = ','.join(mobiles)
        result = subprocess.run(['python3', 'client.py', text, mobile], capture_output=True, text=True)
        return jsonify(result.stderr)

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
    ```
    ```bash
    python3 client-web.py &
    ```

## 仓库地址
http://gitlab.bojin-tech.com/thrid_biz/biz-dingdingzt-cloud.git

## 参考文献
[官方开发者文档](https://developer.signalwire.com/freeswitch/FreeSWITCH-Explained/)
