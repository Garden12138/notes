## 使用 HAProxy 负载均衡 CMPP Socket 长连接

### 背景

* 根据业务场景，```CMPP```的客户端是多个实例，每个实例都需要长连接通信，需要使用```HAProxy```进行负载均衡。

### 什么是 HAProxy

* ```HAProxy```（High Availability Proxy）是一个高性能的负载均衡器和代理服务器，用于```TCP```和```HTTP```应用。

* 主要功能：
  - **负载均衡**：将请求分发到多个后端服务器，提高系统可用性和性能
  - **反向代理**：作为客户端和服务器之间的中间层，隐藏后端服务器信息
  - **高可用性**：支持健康检查、故障转移，确保服务连续性
  - **会话保持**：支持```Sticky Session```，保持客户端与特定服务器的连接

* 主要特点：
  - 高性能、低延迟，适合高并发场景
  - 支持```TCP```和```HTTP```两种模式
  - 支持多种负载均衡算法（轮询、最少连接、源地址哈希等）
  - 提供详细的统计信息和监控接口
  - 配置灵活，支持动态配置重载

* 适用场景：
  - ```Web```应用负载均衡
  - ```TCP```长连接负载均衡（如```CMPP```、```SMPP```等协议）
  - 数据库连接池负载均衡
  - ```API```网关和代理服务

### 实现过程

* 下载安装```HAProxy```，以```CentOS```为例：

  ```bash
  yum install -y haproxy
  ```

  查看```HAProxy```版本：

  ```bash
  haproxy -version
  ```

* 默认配置文件```haproxy.cfg```安装路径为```/etc/haproxy/```，可修改或者新增配置文件：

  ```bash
  vim ./haproxy.cfg
  ```

  负载均衡```CMPP Socket```长连接配置如下：

  ```config
  global
      log 127.0.0.1 local2
      maxconn 50000
      daemon
      stats socket /var/run/haproxy.sock mode 600 level admin
      stats timeout 2m

  defaults
      mode tcp
      log global
      option dontlognull
      timeout connect 5000ms
      timeout client 3600000ms     # 1小时，支持长时间连接
      timeout server 3600000ms     # 1小时，支持长时间连接
      timeout check 5000ms          # 健康检查超时
      maxconn 50000

  frontend persistent_connection_frontend
      bind *:9999 # 监听端口
      default_backend persistent_connection_backend

  backend persistent_connection_backend
      balance source                # 源地址哈希，保证会话一致性
      option tcp-check              # TCP 健康检查
      server server1 127.0.0.1:9315 check inter 5s fall 3 rise 2 weight 1 # 每5秒检查一次、连续3次检查失败后标记为不可用、：连续2次检查成功后恢复服务
      server server2 127.0.0.1:9316 check inter 5s fall 3 rise 2 weight 1 # 每5秒检查一次、连续3次检查失败后标记为不可用、：连续2次检查成功后恢复服务
      server server3 127.0.0.1:9317 check inter 5s fall 3 rise 2 weight 1 # 每5秒检查一次、连续3次检查失败后标记为不可用、：连续2次检查成功后恢复服务
  ```

* 启动```HAProxy```：

  ```bash
  haproxy -f ./haproxy.cfg
  ```

  平滑重载：
  ```bash
  haproxy -f ./haproxy.cfg -p /var/run/haproxy.pid -sf $(cat /var/run/haproxy.pid)
  ```

* 验证```HAProxy```是否正常运行：

  ```bash
  ps -ef | grep haproxy
  ```

  若看到```haproxy```进程，则表示```HAProxy```正常运行。

* 会话保持验证

  * 前提：已在```backend```启用```balance source```（源地址哈希）。

  * 同一客户端源地址多次连接应落到同一后端

    ```bash
    # 连续多次建立连接（同一主机执行）
    for i in $(seq 1 5); do (echo test-$i | nc 127.0.0.1 9999); done

    # 观察 stats：同一源地址的连接应固定到同一 server
    watch -n 2 'echo "show stat" | socat stdio /var/run/haproxy.sock | grep persistent_connection_backend'
    ```

  * 不同客户端源地址应分散到不同后端

    ```bash
    # 在另一台主机或使用不同网卡/容器发起连接
    echo hello | nc 127.0.0.1 9999
    # 对比两端执行 watch 输出，验证分配到的 server 是否不同
    ```
  
### 参考文献

* [haproxy org](https://www.haproxy.org/)
* [HAProxy 入门](https://jaminzhang.github.io/lb/HAProxy-Get-Started/)