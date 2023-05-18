## 自定义 logback 日志 在 logstash 的管道配置

> 自定义 logback 日志样例：
  
```bash
[2023-05-12 11:48:00.000] [WINDOWS-ECSBFQF] [main] INFO c.g.s.SpringbootLoggingApplicationTests@lombokTest:23 - lombokTest => logback testing
[2023-05-12 11:49:00.000] [WINDOWS-ECSBFQF] [main] ERROR c.g.s.SpringbootLoggingApplicationTests@lombokTest:23 - lombokTest => logback err
[2023-05-12 12:03:00.000] [WINDOWS-ECSBFQF] [main] ERROR c.g.s.SpringbootLoggingApplicationTests@lombokTest:23 - lombokTest => logback err2
```

> logstash 管道配置

```bash
input {
  kafka {
    bootstrap_servers => "159.75.138.212:4000"
    topics => ["kafka-test-topic"]
    codec => "json"
  }
}

filter {

  grok {
    match => ["message", "(?m)\[%{TIMESTAMP_ISO8601:timestamp}\] \[%{HOSTNAME:host}\] \[%{DATA:thread}\] %{LOGLEVEL:logLevel} %{DATA:class}@%{DATA:method}:%{DATA:line} \- %{GREEDYDATA:message}"]
    overwrite => ["host", "message"]
  }

  mutate {
    add_field => {
      "code" => "%{thread}-%{class}@%{method}:%{line}"
    }
    remove_field => ["thread", "class", "method", "line"]
    lowercase => ["logLevel"]
  }

  date {
    match => ["timestamp" , "YYYY-MM-dd HH:mm:ss.SSS"]
    target => "@timestamp"
  }

  if [logLevel] == 'info' {
    mutate { add_field => { "[@metadata][target_index]" => "logback_customize_dev-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "logback_customize_dev-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "logback_customize_dev-other-%{+YYYY.MM.dd}" } }
  }

}

output {
  stdout {}
  elasticsearch {
    hosts => ["172.17.0.3:9200"]
    index => "%{[@metadata][target_index]}"
  }
}
```
