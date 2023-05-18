## web 样例日志 在 logstash 的管道配置

> web 样例日志样例：
  
```bash
14.49.42.25 - - [12/May/2023:05:07:44 +0000] "GET /articles/ppp-over-ssh/
HTTP/1.1" 200 18586 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b1) Gecko/20091014 Firefox/3.6b1 GTB5"
```

> logstash 管道配置

```bash
input {
  kafka {
    bootstrap_servers => "159.75.138.212:4000"
    topics => "kafka-test-topic"
  }
}

filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }

  mutate {
    convert => {
      "bytes" => "integer"
    }
  }

  geoip {
    source => "clientip"
  }

  useragent {
    source => "user_agent"
    target => "useragent"
  }

  date {
    match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
  }
}

output {
  stdout { }

  elasticsearch {
    hosts => ["172.17.0.3:9200"]
    index => "web_sample_dev-%{+YYYY.MM.dd}"
    user => elastic
    password => garden520
  }
}

```
