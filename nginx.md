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