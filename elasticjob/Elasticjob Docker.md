## Elasticjob Docker

```
docker pull apache/shardingsphere-elasticjob-lite-ui:latest
docker run --name elasticjob-lite-ui --restart always -p 8088:8088 -d apache/shardingsphere-elasticjob-lite-ui:latest

http://159.75.138.212:8088/index.html#/login
root
root
```
[自定义构建shardingsphere-elasticjob-lite-ui](https://blog.csdn.net/weixin_45357522/article/details/122635467)

```
docker pull zookeeper:latest
docker run --name zookeeper --restart always -p 2181:2181 -d zookeeper:latest
```

[Running docker container : iptables: No chain/target/match by that name](https://stackoverflow.com/questions/31667160/running-docker-container-iptables-no-chain-target-match-by-that-name)
```
sudo iptables -t filter -F
sudo iptables -t filter -X
systemctl restart docker
```

