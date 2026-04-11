## Redis development and operations

### 客户端通信协议

* 客户端通信协议背景，```Redis```之所以能拥有极其丰富的客户端支持（涵盖几乎所有主流编程语言），其核心技术原因有两点：
  *   **基于TCP协议**：```Redis```的客户端与服务端通信是构建在可靠的```TCP```协议之上的。
  *   **制定RESP协议**：```Redis```专门制定了**RESP**（```REdis Serialization Protocol```，```Redis```序列化协议）来实现正常的交互。 这种协议具有**简单高效**、**易于机器解析**且**人类可识别**的特点。

* 发送命令格式，在```RESP```协议中，客户端发送给服务端的每条命令都必须按照特定的格式进行封装，**封装结构如下（其中CRLF代表`\r\n`）：**
  ```bash
  *<参数数量> CRLF
  $<参数1的字节数量> CRLF
  <参数1> CRLF
  ...
  $<参数N的字节数量> CRLF
  <参数N> CRLF
  ```
  **实例解析：**，以命令 `set hello world` 为例：
  *  该命令包含3个参数（`set`、`hello`、`world`），因此第一行为 `*3`。
  *  三个参数的字节长度分别为3、5、5。
  *  **实际传输的字符串格式**为：`*3\r\n$3\r\nSET\r\n$5\r\nhello\r\n$5\r\nworld\r\n`。

* 返回结果格式，```Redis```服务端执行完命令后，返回的结果根据类型分为五种，通过**返回数据的第一个字节**来识别：
  *   **状态回复（Status Reply）**：第一个字节为 **`+`**。例如执行 `set` 成功后返回 `+OK`。
  *   **错误回复（Error Reply）**：第一个字节为 **`-`**。当执行不存在的命令或操作非法时触发。
  *   **整数回复（Integer Reply）**：第一个字节为 **`:`**。例如执行 `incr`、`exists` 等命令返回的结果。
  *   **字符串回复（Bulk Reply）**：第一个字节为 **`$`**。
      *   会先返回字符串的字节长度，再返回内容。
      *   **特殊情况**：如果请求的键不存在，服务端会返回 **`$-1`**，代表空值。
  *   **多条字符串回复（Multi-bulk Reply）**：第一个字节为 **`*`**，每个结果仍然使用 **`$`**。
      *   常用于批量操作（如 `mget`）或返回列表结构的命令（如 `hgetall`）。
      *   如果批量结果中某一项对应的键不存在，该项会返回 `$-1`。例如 `mget hello not_exist_key java` 的返回格式会包含对应的三个部分。

* 协议的可观察性，由于 `redis-cli` 命令行客户端会自动解析 ```RESP``` 协议并将最终结果展示给用户，我们无法直接看到这些特殊字符。 为了观察“真正”的协议数据，开发者可以使用以下工具：
  *   **nc (Netcat)** 命令：例如通过 `nc 127.0.0.1 6379` 连接后手动输入命令，即可看到带符号的原始返回结果。
  *   **telnet** 命令或编写简单的 **socket 程序** 进行模拟。

### Java客户端Jedis

* 获取```Jedis```，```Jedis```是第三方的```Java```开发包。在实际项目中，通常建议使用**集成构建工具**（如```Maven```或```Gradle```）来引入依赖，在**Maven**项目中，可以在`pom.xml`中添加如下依赖（以书中推荐的2.8.2稳定版本为例）：
  ```xml
  <dependency>
      <groupId>redis.clients</groupId>
      <artifactId>jedis</artifactId>
      <version>2.8.2</version>
  </dependency>
  ```
  选取第三方包时，应优先考虑**稳定版本**和**更新活跃**的包。

* ```Jedis```的基本使用方法
  * **(1) 直连与基础操作**通过实例化`Jedis`对象并传入```Redis```实例的```IP```和端口即可建立连接。推荐使用`try-catch-finally`结构，以确保无论执行成功与否都能**关闭连接释放资源**：

    ```java
    Jedis jedis = null;
    try {
        // 1. 生成Jedis对象（IP, 端口, 连接超时, 读写超时）
        jedis = new Jedis("127.0.0.1", 6379, 1000, 1000);
    
        // 2. 执行常用操作
        jedis.set("hello", "world"); // String
        System.out.println(jedis.get("hello"));
    
        jedis.hset("myhash", "f1", "v1"); // Hash
        jedis.rpush("mylist", "1", "2", "3"); // List
        jedis.sadd("myset", "a", "b"); // Set
        jedis.zadd("myzset", 99, "tom"); // Zset
    
    } catch (Exception e) {
       e.printStackTrace();
    } finally {
        if (jedis != null) {
            jedis.close(); // 直连模式下为关闭连接
        }
    }
    ```

  * **(2) 序列化处理**，```Jedis```本身不提供序列化工具，但支持`byte[]`参数。当需要存储```Java```对象时，开发者需自行引入如**Protostuff**、**JSON**或**XML**等工具进行序列化，将其转为二进制数组后再存入```Redis```。以下是书中提供的以**Protostuff**（```Protobuf```的```Java```客户端）为例的完整序列化处理代码示例：

    * 1. 添加Maven依赖，在项目的`pom.xml`中引入```Protostuff```的相关包（推荐版本1.0.11）：

      ```xml
      <dependency>
          <groupId>com.dyuproject.protostuff</groupId>
          <artifactId>protostuff-runtime</artifactId>
          <version>1.0.11</version>
      </dependency>
      <dependency>
          <groupId>com.dyuproject.protostuff</groupId>
          <artifactId>protostuff-core</artifactId>
          <version>1.0.11</version>
      </dependency>
      ```

    * 2. 定义实体类，定义一个需要被序列化的```Java```对象，例如俱乐部对象`Club`：

      ```java
      public class Club implements Serializable {
          private int id;             // ID
          private String name;        // 名称
          private String info;        // 描述
          private Date createDate;    // 创建日期
          private int rank;           // 排名
    
          // 省略 getter 和 setter 方法
          public Club(int id, String name, String info, Date createDate, int rank) {
              this.id = id;
              this.name = name;
              this.info = info;
              this.createDate = createDate;
              this.rank = rank;
          }
      }
      ```

    * 3. 编写序列化工具类，创建一个专门负责对象与字节数组相互转换的工具类`ProtostuffSerializer`：

      ```java
      import com.dyuproject.protostuff.LinkedBuffer;
      import com.dyuproject.protostuff.ProtostuffIOUtil;
      import com.dyuproject.protostuff.Schema;
      import com.dyuproject.protostuff.runtime.RuntimeSchema;

      public class ProtostuffSerializer {
          // 根据类信息生成Schema（模式）
          private Schema<Club> schema = RuntimeSchema.createFrom(Club.class);

          /**
           * 序列化：对象 -> 字节数组
           */
          public byte[] serialize(final Club club) {
              final LinkedBuffer buffer = LinkedBuffer.allocate(LinkedBuffer.DEFAULT_BUFFER_SIZE);
              try {
                  return ProtostuffIOUtil.toByteArray(club, schema, buffer);
              } catch (final Exception e) {
                  throw new IllegalStateException(e.getMessage(), e);
              } finally {
                  buffer.clear();
              }
          }

          /**
           * 反序列化：字节数组 -> 对象
           */
          public Club deserialize(final byte[] bytes) {
              try {
                  Club club = schema.newMessage();
                  ProtostuffIOUtil.mergeFrom(bytes, club, schema);
                  if (club != null) {
                      return club;
                  }
              } catch (final Exception e) {
                  throw new IllegalStateException(e.getMessage(), e);
              }
              return null;
          }
      }
      ```

    * 4. 在```Jedis```中使用序列化，将上述工具类应用于实际的Redis存取操作中：

      ```java
      public void serializationTest() {
          // 1. 初始化序列化工具和Jedis
          ProtostuffSerializer serializer = new ProtostuffSerializer();
          Jedis jedis = new Jedis("127.0.0.1", 6379);
    
          String key = "club:1";
          Club club = new Club(1, "AC", "米兰", new Date(), 1);

          // 2. 序列化并存入Redis
          // 注意：Jedis的set方法需要将key和value都转为byte[]
          byte[] clubBytes = serializer.serialize(club);
          jedis.set(key.getBytes(), clubBytes);

          // 3. 从Redis获取并反序列化
          byte[] resultBytes = jedis.get(key.getBytes());
          Club resultClub = serializer.deserialize(resultBytes);

          // 输出验证结果
          System.out.println("反序列化结果: " + resultClub.getName()); // 输出: AC
          jedis.close();
      }
      ```

* ```Jedis```连接池的使用方法，**直连方式**在频繁访问场景下由于每次都需要新建/关闭```TCP```连接，开销极大。生产环境中通常使用**连接池（JedisPool）**管理连接，这种方式预先初始化好连接，使用时借用，用完归还，能有效保护和控制资源使用。

    ```java
    // 1. 连接池配置
    GenericObjectPoolConfig poolConfig = new GenericObjectPoolConfig();
    poolConfig.setMaxTotal(40); // 最大连接数
    poolConfig.setMaxIdle(24);  // 最大空闲连接数
    poolConfig.setMaxWaitMillis(3000); // 最大等待时间

    // 2. 初始化连接池（通常为单例）
    JedisPool jedisPool = new JedisPool(poolConfig, "127.0.0.1", 6379);

    Jedis jedis = null;
    try {
        // 3. 从连接池借用对象
        jedis = jedisPool.getResource();
        jedis.get("hello");
    } catch (Exception e) {
        e.printStackTrace();
    } finally {
        // 4. 归还连接给连接池
        if (jedis != null) {
            jedis.close(); // 在使用池的情况下，close方法内部实现为归还而非关闭
        }
    }
    ```

* ```Redis```中```Pipeline```的使用方法，**Pipeline（流水线）**机制允许客户端将一批命令一次性传给服务器，能有效减少网络往返时间（```RTT```）。```Jedis```提供了完善的```Pipeline```支持。

  ```java
  public void pipelineExample() {
      Jedis jedis = new Jedis("127.0.0.1", 6379);
      // 1. 生成Pipeline对象
      Pipeline pipeline = jedis.pipelined();
    
      // 2. 将命令封装进Pipeline（注意：此时命令并未真正执行）
      pipeline.set("hello", "world");
      pipeline.incr("counter");
    
      // 3. 执行并获取结果
      List<Object> results = pipeline.syncAndReturnAll();
      for (Object res : results) {
          System.out.println(res);
      }
      jedis.close();
  }
  ```

  **注意**：虽然```Pipeline```好用，但一次组装的命令不宜过多，否则可能造成网络阻塞或增加等待时间，建议将大量命令拆分成多个小的```Pipeline```。

* ```Jedis```执行```Lua```脚本，这对于保证多条命令的**原子性**和定制化命令非常有用。主要有三种相关函数：`eval`、`evalsha`和`scriptLoad`。

  ```java
  Jedis jedis = new Jedis("127.0.0.1", 6379);
  String script = "return redis.call('get', KEYS)";
  String key = "hello";

  // 方式1：使用eval直接执行脚本
  Object result = jedis.eval(script, 1, key);
  System.out.println("Eval Result: " + result);

  // 方式2：先加载脚本，再通过SHA1校验和执行（更高效）
  String sha1 = jedis.scriptLoad(script); // 将脚本常驻内存
  Object resultSha = jedis.evalsha(sha1, 1, key);
  System.out.println("Evalsha Result: " + resultSha);

  jedis.close();
  ```

### Python客户端redis-py

* 获取```redis-py```，通常有以下三种方法：
  *   **使用pip安装**：执行 `pip install redis`。
  *   **使用easy_install安装**：执行 `easy_install redis`。
  *   **源码安装**：通过 `wget` 下载压缩包，解压后进入目录执行 `python setup.py install`。

* ```redis-py```的基本使用方法

  * 核心步骤与```String```操作示例：
    ```python
    import redis

    # 1. 生成客户端连接，需要指定Redis实例的IP和端口
    client = redis.StrictRedis(host='127.0.0.1', port=6379)

    # 2. 执行String命令
    key = "hello"
    setResult = client.set(key, "python-redis") # 返回 True
    print(setResult)

    value = client.get(key) # 返回 "python-redis"
    print("key:" + key + ", value:" + value)

    # 计数操作
    client.incr("counter") # 返回 1
    ```

  * 其他四种数据结构操作示例：
    ```python
    # Hash操作
    client.hset("myhash", "f1", "v1")
    client.hset("myhash", "f2", "v2")
    print(client.hgetall("myhash")) # 输出: {'f1': 'v1', 'f2': 'v2'}

    # List操作
    client.rpush("mylist", "1", "2", "3")
    print(client.lrange("mylist", 0, -1)) # 输出: ['1', '2', '3']

    # Set操作
    client.sadd("myset", "a", "b", "a")
    print(client.smembers("myset")) # 输出: set(['a', 'b'])

    # Zset操作
    client.zadd("myzset", 99, "tom", 66, "peter", 33, "james")
    # 输出: [('james', 33.0), ('peter', 66.0), ('tom', 99.0)]
    print(client.zrange("myzset", 0, -1, withscores=True))
    ```

* ```Pipeline```的使用方法：

  * 代码示例：使用```Pipeline```模拟批量删除（```mdel```）
    ```python
    import redis

    def mdel(keys):
        client = redis.StrictRedis(host='127.0.0.1', port=6379)
        # 生成Pipeline对象，通过 `transaction=False` 参数指定不使用事务。
        pipeline = client.pipeline(transaction=False)
        # 将命令封装到Pipeline中，此时命令并未真正执行
        for key in keys:
            pipeline.delete(key)
        # 执行Pipeline
        return pipeline.execute() # 返回每条命令的结果列表
    ```

* ```Lua```脚本的使用方法，```redis-py```提供了 `eval`、`script_load` 和 `evalsha` 三个重要函数来执行```Lua```脚本：

  * 使用```eval```执行脚本，`eval` 函数需要脚本内容、键的个数以及相关参数（```KEYS```和```ARGV```）：
    ```python
    import redis

    client = redis.StrictRedis(host='127.0.0.1', port=6379)
    script = "return redis.call('get', KEYS)"
    # 输出结果为对应key的值，例如 "world"
    print(client.eval(script, 1, "hello"))
    ```

  * 使用```evalsha```执行脚本，为了提高效率，通常先使用 `script_load` 将脚本加载到```Redis```并获取```SHA1```校验和，之后使用 `evalsha` 调用：
    ```python
    import redis

    client = redis.StrictRedis(host='127.0.0.1', port=6379)
    script = "return redis.call('get', KEYS)"

    # 1. 加载脚本获取SHA1
    scriptSha = client.script_load(script)

    # 2. 使用SHA1执行脚本
    # 参数：SHA1值, KEYS个数, KEYS列表...
    print(client.evalsha(scriptSha, 1, "hello"))
    ```

### 客户端管理

* 客户端```API```，```Redis```提供了多条命令来监控和管理与服务端相连的客户端连接状态。
  * `client list` 命令，这是最常用的命令，用于列出所有已连接客户端的信息。输出结果的每一行代表一个客户端，包含十几个重要的属性：
    *   **标识属性**：
        *   **id**：客户端连接的唯一标识，随连接自增，重启后重置。
        *   **addr**：客户端的```IP```和端口。
        *   **fd**：```socket```文件描述符，若为-1则代表是```Redis```内部的伪装客户端。
        *   **name**：客户端名称，可通过 `client setName` 设置。
    *   **输入缓冲区 (`qbuf`, `qbuf-free`)**：
        *   ```Redis```为每个客户端分配输入缓冲区，临时保存客户端发送的命令。
        *   **限制**：输入缓冲区不可配置，动态调整，但**每个客户端缓冲区上限为1GB**，超过则连接会被关闭。
        *   **风险**：输入缓冲区**不受 `maxmemory` 控制**。如果大量输入缓冲区占用过多内存（如```3GB```），即使数据本身只占```2GB```，也可能导致```OOM```或键值淘汰。

          ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_9.png)

    *   **输出缓冲区 (`obl`, `oll`, `omem`)**：
        *   用于保存命令执行结果并返回给客户端。
        *   **结构**：由**固定缓冲区**（16```KB```，用于小结果）和**动态缓冲区**（列表结构，用于大结果，如 `hgetall` 的返回）组成。
        *   **参数含义**：`obl` 为固定缓冲区长度，`oll` 为动态缓冲区列表长度，`omem` 为总占用字节数。
        *   **配置**：可通过 `client-output-buffer-limit` 按客户端类型（```normal```, ```slave```, ```pubsub```）设置硬限制和软限制。

          ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/redis_dev_maintenance_10.png)

    *   **存活状态 (`age`, `idle`)**：
        *   `age` 是连接已存在的时间，`idle` 是最近一次闲置的时间（单位为秒）。
    *   **客户端类型 (`flags`)**：
        *   标识客户端角色，例如 `N`（普通）、`S`（从节点）、`O`（正在执行 `monitor`）等。

    使用示例：

      ```bash
      127.0.0.1:6379> client list
      id=254487 addr=10.2.xx.234:60240 fd=1311 name= age=8888581 idle=8888581 flags=N db=0 sub=0 psub=0 multi=-1 qbuf=0 qbuf-free=0 obl=0 oll=0 omem=0 events=r cmd=get
      id=7125108 addr=10.10.xx.103:33403 fd=139 name= age=241 idle=1 flags=N db=0 sub=0 psub=0 multi=-1 qbuf=0 qbuf-free=0 obl=0 oll=0 omem=0 events=r cmd=del
      ```

  * `client setName` 和 `client getName`，用于设置和获取当前连接的名称，便于在多应用共享```Redis```时标识客户端来源。

    使用示例：

      ```bash
      # 1. 设置当前连接名称
      127.0.0.1:6379> client setName test_client
      OK

      # 2. 获取当前连接名称
      127.0.0.1:6379> client getName
      "test_client"

      # 3. 在 client list 中查看标识
      127.0.0.1:6379> client list
      id=55 addr=127.0.0.1:55604 fd=7 name=test_client age=23 idle=0 ...

  * `client kill`，用于杀掉指定```IP```和端口的客户端连接。在处理因 `timeout=0` 产生的长时间空闲连接时非常有用。

    使用示例：

      ```bash
      # 杀掉指定IP和端口的客户端
      127.0.0.1:6379> client kill 127.0.0.1:52343
      OK
      ```

  * `client pause`，阻塞客户端 `timeout` 毫秒。该命令对普通和发布订阅客户端有效，但**对从节点（主从复制）无效**，可用于可控地切换```Redis```节点。

    使用示例：

      ```bash
      # 1. 在客户端A执行暂停命令（阻塞10000毫秒，即10秒）
      127.0.0.1:6379> client pause 10000
      OK

      # 2. 此时在客户端B执行命令会感到明显阻塞，直到10秒后返回
      127.0.0.1:6379> ping
      PONG (9.72s)
    ```

  * `monitor`，用于监控```Redis```正在执行的所有命令。
    *   **警告**：在高并发环境下，`monitor` 客户端的输出缓冲区会因为接收所有命令而暴涨，**极易瞬间耗尽内存**。

    使用示例：
      
      ```bash
      127.0.0.1:6379> monitor
      OK
      1472513599.754326 [0 127.0.0.1:56335] "set" "hello" "world"
      1472513601.305303 [0 127.0.0.1:56335] "get" "hello"
      1472513605.514383 [0 127.0.0.1:56335] "ping"
      ```

* 客户端相关配置，这些参数控制了服务端如何处理客户端连接：
  *   **`timeout`**：检测客户端空闲连接的时间。若闲置时间达到 `timeout`，连接将被关闭。设置为0则不检测（默认值，但在实际运维中建议设置，如300秒）。
  *   **`maxclients`**：最大客户端连接数，默认为10000。若超过此限制，新连接将被拒绝并抛出异常。
  *   **`tcp-keepalive`**：```TCP```连接活性检测周期，建议设置为60秒，防止大量死连接占用系统资源。
  *   **`tcp-backlog`**：```TCP```三次握手后的连接队列大小，默认511。若受操作系统限制（如```Linux```的 `somaxconn` 较小），```Redis```会发出警告日志。

  使用示例：

    ```bash
    127.0.0.1:6379> info clients
    # Clients
    connected_clients:262             # 当前连接数
    client_longest_output_list:0      # 输出缓冲区队列最大对象数
    client_biggest_input_buf:0        # 输入缓冲区最大占用容量
    blocked_clients:0                 # 正在执行阻塞命令的客户端数
    ```

* 客户端统计片段，通过 `info clients` 命令可以快速获取当前客户端的汇总统计指标：
  * **`connected_clients`**：当前连接数，需重点监控，严防超过 `maxclients`。
  *  **`client_longest_output_list`**：当前所有输出缓冲区队列对象个数的最大值。
  *  **`client_biggest_input_buf`**：当前所有输入缓冲区占用的最大容量。
  *  **`blocked_clients`**：正在执行阻塞命令（如 `blpop`）的客户端个数。

  使用示例：

    ```bash
    127.0.0.1:6379> info clients
    # Clients
    connected_clients:262             # 当前连接数
    client_longest_output_list:0      # 输出缓冲区队列最大对象数
    client_biggest_input_buf:0        # 输入缓冲区最大占用容量
    blocked_clients:0                 # 正在执行阻塞命令的客户端数
    ```

  此外，`info stats` 中的 `total_connections_received`（累计处理连接总数）和 `rejected_connections`（拒绝连接数）也是重要的参考指标。
