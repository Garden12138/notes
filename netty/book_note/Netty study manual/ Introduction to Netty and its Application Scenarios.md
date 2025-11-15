## Netty 介绍和应用场景

### Netty 介绍

* ```Netty```是由```JBOSS```提供的一个```Java```开源框架，是一个异步的、基于事件驱动的网络应用框架，用以快速开发高性能、高可靠性的网络```IO```程序。在```TCP```协议下，面向```Client```端的高并发应用，或者```Peer-to-Peer```场景下大量数据持续传输的应用，其本质是```NIO```框架，适用于服务器通讯相关的多种应用。

### Netty 应用场景

* 互联网行业，在分布式系统中，各个节点之间需远程服务调用，```Netty```作为异步高性能的通信框架，通常作为基础通信组件被```RPC```框架使用，如```Dubbo```协议默认使用```Netty```作为基础通信组件，实现各进程节点之间的内部通信:

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/netty/netty1.png)

* 游戏行业，```Netty```提供```TCP/UDP```和```HTTP```协议栈，方便制定和开发私有协议栈，账号登录服务器；地图服务器之间可方便的通过```Netty```进行高性能的通信。

* 大数据领域，如```Hadoop```的高性能通信和序列化组件```Avro```的```RPC```框架，默认采用```Netty```进行跨界点通信，它的```NettyService```基于```Netty```框架二次封装实现。

* [其他开源项目](https://netty.io/wiki/related-projects.html)