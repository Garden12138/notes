# 基于consul的docker-overlay网络搭建指南

## 什么是Overlay网络

Overlay网络是指在物理网络之上，再构建一个逻辑网络。这种网络虚拟化技术可以将多个物理网络组成一个虚拟网络，实现多主机之间的通信。<br/>
在Docker中，Overlay网络是**一种容器跨主机的通信方案**，可以将多个Docker主机上的容器连接起来，形成一个虚拟网络。



## Overlay网络工作原理

Overlay网络是使用VXLAN协议实现的，VXLAN是一种虚拟化隧道协议，它可以将二层网络封装在UDP包中传输，从而实现跨主机的网络通信。

简单理解:
![](img\原理.png)



## 环境准备

* 2台服务器（这里用虚拟机模拟;需要先确保两台服务器是互通的）
* linux （这里使用的是centOS 7.4）
* docker
* consul



## 安装docker

这里使用的是yum安装

### 卸载旧docker

```shell
yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine
```



### 安装yum-util

```shell
 yum install -y yum-utils
```



### 设置镜像源

```shell
#官方源
yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
    
#阿里云
yum-config-manager \
    --add-repo \
    http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
```



### 更新软件包

```shell
yum makecache fast
```



### 安装docker-ce

```shell
yum install docker-ce docker-ce-cli containerd.io
```



## 安装consul

选一台服务器作为consul server，也可以集群搭建

### 使用yum安装consul

```shell
#安装
yum -y install consul
 
#查看版本
consul -v

#后台启动节点
#参数说明:
# -server
# -bootstrap
# -ui
# -data-dir		工作目录
# -client		客户端ip(一般填0.0.0.0)
# -bind			绑定id(填宿主机ip,默认127.0.0.1)
nohup consul agent -server -bootstrap -ui -data-dir=/data/docker/consul -client=0.0.0.0 -bind=127.0.0.1 &> /var/log/consul.log &

#开放8500端口
firewall-cmd --add-port=8500/tcp --permanent
#重载
firewall-cmd --reload

#或者直接关闭防火墙
systemctl stop firewalld

```



### 查看效果

访问 http://宿主机ip:8500/

![](img\consul.png)



## 配置docker daemon的启动参数

### 修改deamon参数

需要分别对两台服务器进行修改

```shell
#编辑docker.service文件
vi /lib/systemd/system/docker.service

#修改参数项ExecStart的值,在后面加上以下参数
#参数说明:
# -H tcp://0.0.0.0:2375 指定协议与端口（注：这里指定2375端口，仅用于测试环境【存在安全漏洞】；推荐使用2376端口【加密】，但需要自己配置密钥）
# --cluster-store		配置的Consul的leader地址，单体直接写，其它软件注意协议
# --cluster-advertise	指定监听的网卡和端口，也可以指定接收订阅服务的IP:PORT
ExecStart= [原本的值] -H tcp://0.0.0.0:2375 --cluster-store=consul://[consul服务的ip]:8500 --cluster-advertise=[宿主机ip]:2375

#修改完后,重启docker服务
systemctl daemon-reload && systemctl restart docker
```



### 查看效果

![](img\daemon.png)

可以在consul页面的key/values目录下，找到两台服务器的注册地址



## 创建overlay网络

### 通过docker network创建overlay网络

```shell
#在其中一台主机上，新建一个network
docker network create -d overlay overlay

#此时可以同时在两台机器上都可以通过ls或inspect查看overlay网络的状态
docker network ls
docker network inspect overlay
```

![](img\overlay.png)

![](img\overlay_inspect.png)

可以看到创建了一个网段为10.0.0.0/24的网络

### 开放端口

```shell
#开放相关端口
# 2377/tcp				用来集群管理相关的通信
# 7946/tcp,7946/udp		用来进行节点之间的通信
# 4789/udp				用来进行进行overlay网络上的数据传输
firewall-cmd --add-port=2377/tcp --permanent
firewall-cmd --add-port=7946/tcp --permanent
firewall-cmd --add-port=7946/udp --permanent
firewall-cmd --add-port=4789/udp --permanent

firewall-cmd --reload
```



## 验证overlay

### 启动容器

在两台服务器上分别跑一个容器(这里跑的是nginx)

```shell
#服务器1
# --net参数指定overlay网络的名称(可通过docker network ls查看)
docker run -itd --net overlay --name nginx_01 -v /home/nginx/conf.d:/etc/nginx/conf.d -v /home/nginx/html:/etc/nginx/html -v /home/nginx/log:/usr/log/nginx -p 8080:80 nginx

#服务器2
docker run -itd --net overlay --name nginx_02 -v /home/nginx/conf.d:/etc/nginx/conf.d -v /home/nginx/html:/etc/nginx/html -v /home/nginx/log:/usr/log/nginx -p 8080:80 nginx

#通过inspect命令查看容器在overlay网络的情况
docker network inspect overlay
```

![](img\overlay_container.png)

可以看到两个容器都已启动并分配了10.0.0.0/24网段的ip

### 验证联通

使用ping命令验证

```shell
#进入服务器1的nginx_01容器
docker exec -it nginx_01 /bin/bash

#直接ping服务器2的容器名
ping nginx_02
```

![](img\ping.png)

可以看到，直接通过容器名解析出ip，且ping通

完成搭建
