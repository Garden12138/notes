## 使用 docker 部署 altermanager

> 前期准备

* 编写配置文件```altermanager.yml```

  ```bash
  # 全局配置
  global:
    resolve_timeout: 5m
    smtp_smarthost: 'smtp.163.com:465' # 邮箱服务器的POP3/SMTP主机配置如网易邮箱（smtp.163.com），端口为465或587
    smtp_from: 'nedrag520@163.com' # 发件人
    smtp_auth_username: 'nedrag520@163.com' # 用户名 
    smtp_auth_password: 'OIOVIGMUVGYDMGLW' # 授权码
  # 路由配置
  route:
    receiver: 'default-receiver' # 父节点
    group_by: ['alertname'] # 分组规则
    group_wait: 10s # 为了能够一次性收集和发送更多的相关信息时，可以通过group_wait参数设置等待时间
    group_interval: 1m  #定义相同的Group之间发送告警通知的时间间隔
    repeat_interval: 1m
    routes: # 子路由，根据match路由
    - receiver: 'rhf-mail-receiver'
      group_wait: 10s
      match: # 匹配自定义标签
        team: rhf    
  # 告警接收者配置
  receivers:
  - name: 'default-receiver'
    email_configs:
    - to: '847686279@qq.com'
  - name: 'rhf-mail-receiver'
    email_configs:
    - to: '847686279@qq.com'
  ```

> 拉取镜像
  
  ```bash
  docker pull prom/alertmanager:latest
  ```

> 运行容器

  ```bash
  docker run \
    --name=alertmanager \
    --restart=always \
    -d \
    -p 9093:9093 \
    -v /data/altermanager/altermanager.yml:/etc/alertmanager/alertmanager.yml \
    prom/alertmanager:latest
  ```