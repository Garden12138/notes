## 基础概念

>nginx
* nginx是可快速提供服务的web服务器。还可反向代理，集成上游服务器（Unicorn或Puma），负载均衡，流媒体，动态调整图像大小以及缓存内容等。
* 基本的nginx体系结构由master进程和其worker进程组成。master读取配置文件，并维护worker进程，而worker则会对请求进行实际处理。

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