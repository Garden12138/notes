## 基础概念

>nginx
* nginx是可快速提供服务的web服务器。还可反向代理，集成上游服务器（Unicorn或Puma），负载均衡，流媒体，动态调整图像大小以及缓存内容等。
* 基本的nginx体系结构由master进程和其worker进程组成。master读取配置文件，并维护worker进程，而worker则会对请求进行实际处理。

>指令
* 指令-可选项，包含名称和参数，以分号结尾，例如：gzip on;
* 类型
  * 普通指令：在每个上下文仅有唯一值。而且，它只能在当前上下文中定义一次。子级上下文可以覆盖父级中的值，并且这个覆盖值只在当前的子级上下文中有效
    ```
    gzip on;
    gzip off; # 非法，不能在同一个上下文中指定同一普通指令2次server {
        location /downloads {
            gzip off; # 覆盖全文上下文的gzip指令，仅在当前上下文有效
        }
    }
    ```
  * 数组指令：同一上下文中多条不同值的指令。在子级上下文中定义指令将覆盖给父级上下文中的值
    ```
    error_log /var/log/nginx/error.log;
    error_log /var/log/nginx/error_debug.log debug;
    server{
        location /downloads{
            # 覆盖父级上下文中的指令
            error_log /var/log/nginx/error_downloads.log
        }
    }
    ```
  * 行动指令：改变事情的指令。
    ```
    server{
        rewrite ^ /foobar;
        location /foobar{
            rewrite ^ /foo;
        }
    }
    ```

>上下文
* 上下文-分块，类似编程语言中的作用域，可在作用域内声明指令。
```
worker_processes 2; # 该指令位于全局上下文
http{
    gzip on; # 该指令卫浴http上下文
    ...
}
```

>nginx处理请求
* 在nginx的http上下文指定多个虚拟服务器，每个虚拟服务器用server{}上下文描述。
```
http{
    server{
        listen    *:80 default_server; # 监听请求端口
        server_name gardenpzq.cn;      # 映射请求头的Host字段 
        return 200 "connect success";  # 返回客户端状态码以及信息
    }
}
```
* nginx将会首先通过检查listen指令来测试哪一个虚拟主机在监听给定的IP端口组合，然后，server_name指令的值将检测Host 头(存储着主机域名)。
* nginx选择虚拟服务器顺序：
  * 匹配IP端口以及server_name的虚拟主机。
  * 匹配IP端口以及default_server标记的虚拟主机。
  * 匹配首先定义IP端口的虚拟主机。
  * 无匹配则拒绝连接。

>nginx最小配置
```
# /etc/nginx/nginx.conf #nginx配置文件路径
events{}
http{
    server{
        listen    *:80 default_server; 
        server_name www.gardenpzq.cn www.gardenqaq.cn;     
        return 200 "connect success";
    }
}
```

## 指令
>listen
* 匹配接受IP以及端口值，确定虚拟主机。
  ```
  listen 127.0.0.1:80;   # 显示IP
  listen 127.0.0.1;      # 使用默认端口80
  listen 80;             # 使用默认本机IP
  listen gardenpzq.cn:80 # 使用主机名
  listen [::]:80;        # IPv6 address
  ```
* 匹配套接字
  ```
  listen unix:/var/run/nginx.sock;
  ```
* 如果指令不存在，则使用*:80;
  ```
  listen *:80;
  ```

>server_name
* 匹配请求头的Host，确定虚拟主机。
* 匹配顺序（Nginx 会存储 3 个哈希表：确切的名字，以星号开始的通配符，和以星号结尾的通配符。如果结果不在任何表中，则将按顺序进行正则表达式测试）
  * 确切的名字，如server_name gardenpzq.cn gardenqaq.cn; 
  * 最长的通配符名称以星号开始，如server *.gardenpzq.cn;
  * 最长的通配符名称以星号结尾，如server gardenpzq.*;
  * 正则表达，如server ~^[0-9]*\.gardenpzq\.cn$;
* 以点符号为开始的值含义
  ```
  server .gardenpzq.cn => server gardenpzq.cn
                       => server www.gardenpzq.cn
                       => server *.gardenpzq.cn
  ```

>root
* 设置请求的根目录，允许nginx将传入的请求映射到文件系统。
* 默认将返回文件系统根目录的index.html资源，若资源不存在，则返回403。
* 一般使用在server上下文以及location上下文，若location的父级上下文是server，使用root指令时将覆盖。
  ```
  server{
      listen 80;
      server_name gardenpzq.cn;
      root /usr/share/nginx/html; # 请求/映射至该目录，将返回html目录下的index.html
  }
  ```
  ```
  location /index {
      root /usr/share/nginx/html; # 请求/index映射至该目录，将返回html目录下的index.html
  }
  ```
* 前端代码打包后（生成index.html）放置root指向的目录

>location
* 根据请求的URI设置配置
  ```
  location [modifier] uri
  ```
* 若无指定修饰符，则视路径为前缀，其后可任意匹配。
  ```
  location /index/ {
      #...
  }
  => /index
  => /index123
  => /index/dev/index.html
  ```
* 在给定的上下文里可使用多个location指令。
  ```
  server {
      listen 80;
      server_name gardenpzq.cn;
      location / {
          return 200 "root";
      }
      location /index {
          return 200 "index";
      }
  }
  ```
* 修饰符优先级
  * 精确匹配，修饰符为=
  * 优先匹配，修饰符为^~
  * 正则匹配，修饰符为~获取~*
  * 无修饰符【前缀】匹配
  ```
  location /match {
      return 200 'Prefix match: matches everything that starting with /match';
  }
  location ~* /match[0-9] {
      return 200 'Case insensitive regex match';
  }
  location ~ /MATCH[0-9] {
      return 200 'Case sensitive regex match';
  }
  location ^~ /match0 {
      return 200 'Preferential match';
  }
  location = /match {
      return 200 'Exact match';
  }
  ```
  ```
  /match/    # => 'Exact match'
  /match0    # => 'Preferential match'
  /match1    # => 'Case insensitive regex match'
  /MATCH1    # => 'Case sensitive regex match'
  /match-abc # => 'Prefix match: matches everything that starting with /match'
  ```

>try_files
* 尝试不同路径，找到一个路径就返回。一般用用于查询静态文件。
  ```
  try_files $uri index.html =404;
  # 对于/garden.html请求，尝试以下顺序返回文件
  => 1. $uri(/garden.html)
  => 2. index.html
  => 3. 返回404
  ```
* 最后一个选项为当前虚拟主机内重定向。

>tcp_nodelay
* Nagle算法，旨在防止通讯被大量的小包淹没。该理论不涉及全尺寸tcp包（最大报文长度，简称 MSS）的处理。只针对比MSS小的包，只有当接收方成功地将以前的包(ACK)的所有确认发送回来时，这些包才会被发送。在等待期间，发送方可以缓冲更多的数据之后再发送。
* 由于Nagle在和延迟ACK之间的数据格式交换过程中存在死锁，会引入200ms的延迟，故使用时关闭。
  ```
  tcp_nodelay on;
  ```

>sendfile
* 传递对象指针的发送文件方式，在nginx中打开。
  ```
  sendfile on;
  ```

>tcp_nopush
* 一次性优化数据的发送量，在发送给客户端之前，它将强制等待包达到最长长度，并且只有在sendfile开启时才起作用。
  ```
  sendfile on;
  tcp_nopush on;
  ```
>worker_process
* 指定nginx运行核心数（工作进程数），一般设置为auto。
  ```
  worker_process auto;
  ```

>worker_connections
* 指定一个工作进程每次可打开的连接数。
  ```
  worker_connections 1024;
  ```  

## 常用命令
>启动nginx
* [sudo] nginx
* service nginx start

>停止nginx
* service nginx stop

>重启nginx
* service nginx restart

>查看nginx状态
* service nginx status

>管理nginx实例
* 快速关闭：[sudo] nginx -s stop
* 优雅关闭[等待woker线程完成处理]：[sudo] nginx -s quit
* 重载配置文件：[sudo] nginx -s reload
* 重新打开日志文件： [sudo] nginx -s reopen

## 应用场景