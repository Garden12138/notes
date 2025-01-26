单机可能存在的问题：性能瓶颈，单机无法承受高并发，可能需要集群部署（server）。
1. client(域名) -> haproxy/nginx -> server
2. client(dns) -> server
3. client -> zk(注册中心) ->server
2、3的本质是通过获取指定服务的地址，然后进行通信，客户端需要做策略性的选择，比如一致性hash。