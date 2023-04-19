## 使用 docker-compose 部署 elk stack

> elasticsearch

docker pull elasticsearch:7.17.9

mkdir -p /data/elk/es/config && mkdir -p /data/elk/es/data && mkdir -p /data/elk/es/logs && chown -R 1000:1000 /data/elk/es

vim /data/elk/es/config/elasticsearch.yml
```
cluster.name: "elasticsearch"
network.host: 0.0.0.0
http.port: 9200
```

docker run -d -p 9200:9200 -p 9300:9300 --name elasticsearch -e ES_JAVA_OPTS="-Xms512m -Xmx1024m" -e "discovery.type=single-node" --restart=always -v /data/elk/es/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -v /data/elk/es/data:/usr/share/elasticsearch/data -v /data/elk/es/logs:/usr/share/elasticsearch/logs elasticsearch:7.17.9

local_console:
curl http:127.0.0.1:9200/

> kibana

docker pull kibana:7.17.9

mkdir -p /data/elk/kibana && chown -R 1000:1000 /data/elk/kibana

docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elasticsearch

vim /data/elk/kibana/kibana.yml
```
server.port: 5601
server.name: kibana
server.host: 0.0.0.0
elasticsearch.hosts: ["http://172.17.0.2:9200"]
## elasticsearch.username: es-admin
## elasticsearch.password: nXxDlKe0n4O7wSn
xpack.monitoring.ui.container.elasticsearch.enabled: true
i18n.locale: "zh-CN"
```

docker run -d --restart=always --log-driver json-file --log-opt max-size=100m --log-opt max-file=2 --name kibana -p 5601:5601 -v /data/elk/kibana/kibana.yml:/usr/share/kibana/config/kibana.yml kibana:7.17.9

browser:
${IP}:5601/