# 集成Micrometer-Tracing

## 背景

Spring Boot 3.x后移除了spring-cloud-starter-sleuth，并迁移了相关的jar包

官方解决方案：使用micrometer-tracing替换sleuth

相关链接：

https://github.com/micrometer-metrics/tracing/wiki/Spring-Cloud-Sleuth-3.1-Migration-Guide


## 预备知识（重要）
可观测性 Observability（https://springdoc.cn/spring-boot-3-observability/）


## 引入micrometer-tracing

### 什么是micrometer-tracing

Micrometer-tracing是Micrometer项目的一部分，用于提供应用程序度量信息的收集和报告。它是一个基于JVM的度量库，可以用于监控应用程序的各种指标，如请求响应时间、请求数量、内存使用情况等。

相关链接：

https://micrometer.io/docs/tracing



### 支持的Tracers
* OpenZipkin Brave (https://github.com/openzipkin/brave)
* OpenTelemetry (https://opentelemetry.io/)



### 添加相关依赖

以OpenZipkin Brave为例

```xml
<!-- 包含相关的自动配置类
	 相关目录: 
		org.springframework.boot.actuate.autoconfigure.tracing.* 
		org.springframework.boot.actuate.autoconfigure.observation.*
-->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<!-- micrometer-tracing 
	 micrometer-tracing只是一个链路追踪门面,本身并不实现链路追踪功能 
-->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing</artifactId>
</dependency>
<!-- OpenZipkin Brave的桥接
     真正实现链路追踪功能
 -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>

<!-- zipkin-reporter(非必要)
	 将span报送到zipkin 
-->
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

<br/>

### 远程调用传递TracingContext

若要实现分布式链路追踪，就需要在服务之间传递TracingContext，Micrometer-Tracing提供以下几种方式：

#### HttpClient的实现

以RestTemplate为例（WebClient大致相同）

```java
/**
 * 使用RestTemplateBuilder创建RestTemplate即可,发起Http Request时会被PropagatingSenderTracingObservationHandler捕获
 * @see io.micrometer.tracing.handler.PropagatingSenderTracingObservationHandler
 */
@Bean
public RestTemplate restTemplate(RestTemplateBuilder builder) {
    return builder.build();
}
```

注1：这个RestTemplateBuilder是RestTemplateAutoConfiguration创建的（自己创建的也可以，不过需要额外的补充一些配置）

相关内容：

org.springframework.boot.actuate.autoconfigure.observation.web.*



#### OpenFeign的实现

引入依赖包即可

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
<!-- 额外引入对micrometer的支持 -->
<dependency>
    <groupId>io.github.openfeign</groupId>
    <artifactId>feign-micrometer</artifactId>
</dependency>
```

<br/>


### 关于Span（重要）
#### 核心接口
* io.micrometer.observation.Observation
* io.micrometer.tracing.handler.TracingObservationHandler

#### 默认创建span
主要由TracingObservationHandler处理，提供三种默认实现（详见 io.micrometer.tracing.handler.*）
* DefaultTracingObservationHandler (本地传播)
* PropagatingReceiverTracingObservationHandler（跨服务传播,接收Http请求）
* PropagatingSenderTracingObservationHandler（跨服务传播,发送Http请求）


#### 手动创建Span
```java
public void test(String msg){
    //此处基于OpenZipkin Brave实现
    //获取Tracer
    Tracer tracer = null;
    try {
        tracer = SpringBeanTool.getBean(BraveTracer.class);
    }catch (Exception e){
    }

    Span span = tracer.nextSpan()
            .name("test_span")
            .tag("test.msg", msg)
            .start();
    try(Tracer.SpanInScope ws = tracer.withSpan(span)) {
        //do something
    }finally {
        span.end();
    }
}
```


<br/>


### 关于传播机制

#### 传播协议

##### w3c/trace-context

Spring Boot 3.x 后，默认的传播协议采用w3c/trace-context标准。

相关实现类：

io.micrometer.tracing.brave.bridge.W3CPropagation

相关链接：

https://www.w3.org/TR/trace-context/



##### B3

仍然支持B3传播协议，可通过配置调整

```yaml
#Single Header
management:
  tracing:
    propagation:
      type: b3
```

```yaml
#Multiple Header    
management:
  tracing:
    propagation:
      type: b3_multi
```



#### 默认传播字段（重要）

基于w3c/trace-context标准，默认传播字段为：traceId、spanId

发出Http请求之前，会将默认传播字段添加到HTTP Header

格式：
```
traceparent= [version]-[trace-id]-[parent-id]-[trace-flags]
```


包含4个字段：

version

trace-id（对应默认传播字段traceId）

parent-id（对应默认传播字段spanId）

trace-flags



相关类：

io.micrometer.tracing.brave.bridge.W3CPropagation#injector

具体详见：

https://www.w3.org/TR/trace-context/


<br/>


#### 额外传播字段

基于Baggage机制实现

通过配置添加

```yaml
management:
  tracing:
    baggage:
      remote-fields:
        - field1
        - field2
```

相关类与方法：

org.springframework.boot.actuate.autoconfigure.tracing.BraveAutoConfiguration.BraveBaggageConfiguration#remoteFieldsBaggagePropagationCustomizer



设置BaggageField的值

```java
//例如
//以OpenZipkin Brave为例
public void test(){
    //获取Tracer(自动注入或手动注入)
    BraveTracer tracer  = ...;
    //获取当前span的brave.propagation.TraceContext
    TraceContext context = BraveTraceContext.toBrave(tracer.currentSpan().context());
    //从TraceContext中取出BaggageFields
    BaggageFields extra = context.findExtra(BaggageFields.class);
    //获取BaggageField列表
    List<BaggageField> fields = extra.getAllFields();
    BaggageField field1 = fields.get(0);
    BaggageField field2 = fields.get(1);
    //修改指定BaggageField的值
    extra.updateValue(field1, "123456");
    extra.updateValue(field2, "hello");
}
```

发出Http请求之前，会将额外传播字段添加到HTTP Header

若基于w3c/trace-context标准，格式如下（若BaggageField没有值，则不会传播）：
```
baggage = field1=123456,field2=hello
```


相关类：

io.micrometer.tracing.brave.bridge.W3CBaggagePropagator#injector