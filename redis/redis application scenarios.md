## redis 应用场景

> 布隆过滤器

* 工作原理：
  
  布隆过滤器是一个高空间利用率的概率性数据结构，由二进制向量（数组）和若干个随机映射函数（哈希函数）两部分组成。工作流程如下：

    * 添加元素。当添加```Key```（布隆过滤器）时，会使用不同的哈希函数对元素值进行哈希计算得到多个哈希值，每个哈希值计算出整数索引值，将该索引值与位数组长度做取余运算得出位数组位置，将该位置的值设置为1。通过多个哈希函数所计算出的多个位数组位置上的多个值组合起来，代表添加的元素。

    * 判断元素。首先对元素进行添加时的哈希运算获取位数组的位置，通过判断每个位置是否都为1，判断元素是否存在，若其中一个为0则不存在，若都为非0则可能不存在（可能不存在的原因是因为哈希碰撞，这是被允许的，故存在错误率概念，若希望减少碰撞，则声明布隆过滤器时需设置低错误率，同时扩大位数组容量）。

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2024-01-21_21-56-01.png)

* 服务端安装与使用。在```Redis4.0```后，布隆过滤器才作为插件正式使用，需单独安装：

  * 布隆过滤器插件（```redisbloom.so```）的生成：

    ```bash
    # 方式一：下载源码并编译（待验证）
    # 下载地址：
    https://github.com/RedisBloom/RedisBloom
    # 解压文件并进入目录
    unzip RedisBloom-master.zip
    cd RedisBloom-master
    # 执行编译命令，生成插件文件
    make
    # 方式二：运行redislabs/rebloom测试容器，拷贝插件
    docker run --name redisbloom-test -d redislabs/rebloom:latest 
    docker cp redisbloom-test:/usr/lib/redis/modules/redisbloom.so . && docker stop redisbloom-test && docker rm redisbloom-test
    ```

  * ```docker```安装：

    ```bash
    # 拉取集成布隆过滤器插件的镜像
    docker pull redislabs/rebloom:latest

    # 运行集成布隆过滤器插件的容器，挂载文件redis.conf为配置文件，挂载目录rdb为数据持久化目录，挂载目录exp为扩展模块目录
    docker run \
            --name redisbloom \
            -d \
            -v /data/redis/redis.conf:/etc/redis/redis.conf \
            -v /data/redis/rdb:/data \
            -v /data/redis/exp:/exp \
            -p 6379:6379 \
            redislabs/rebloom:latest \
            redis-server /etc/redis/redis.conf --appendonly yes

    # 进入容器，测试布隆过滤器是否可正常使用
    docker exec -it redis-redisbloom /bin/bash
    root@aaa0e92b4b1f:/data# redis-cli
    127.0.0.1:6379> bf.add name redis1
    (integer) 1
    ```

    上述```docker```安装方式适用于运行新的```redis```服务容器的场景。针对运行中的```redis```服务容器：

    ```bash
    # 拷贝插件文件至扩展模块挂载目录
    cp redisbloom.so /data/redis/exp/
    # 编辑配置文件，新增加载布隆过滤器插件配置
    vi /data/redis/redis.conf
    loadmodule /exp/redisbloom.so
    # 重启容器
    docker restart redis
    ```

  * ```linux```安装：

    ```bash
    # 拷贝至指定目录
    cp redisbloom.so /usr/local/redis/bin/redisbloom.so
    # 编辑配置文件，新增加载布隆过滤器插件配置
    vi /${path}/redis.conf
    loadmodule /usr/local/redis/bin/redisbloom.so
    # 重启服务
    sudo /etc/init.d/redis-server restart
    ```

  * 常用命令使用：

    | 序号 | 命令 | 说明 |
    | :--- | :--- | :--- | 
    | 1 | BF.ADD {key} {element} | 添加一个元素至布隆过滤器 |
    | 2 | BF.EXISTS {key} {element} | 判断元素是否存在布隆过滤器 |
    | 3 | BF.MADD {key} {elements} | 添加多个元素至布隆过滤器 |
    | 4 | BF.MEXISTS {key} {elements} | 判断多个元素是否存在布隆过滤器 |
    | 5 | BF.RESERVE {key} {error_rate} {capacity} [EXPANSION {expansion}] [NONSCALING] | 手动创建错误率为{error_rate}、容量为{capacity}的布隆过滤器。选项EXPANSION可设置当数据达到满容量后自动扩容的倍数（默认为2）；选项NONSCALING可设置当数据达到满容量后不自动扩容 |

* 客户端安装与使用。以```SpringBoot```为例：

  * [集成```Redis```。](https://gitee.com/FSDGarden/learn-note/blob/master/springboot/Integrates%20Redis.md)

  * 结合```Google Guava```集成布隆过滤器：

    引入依赖：

    ```bash
    <dependency>
        <groupId>com.google.guava</groupId>
        <artifactId>guava</artifactId>
        <version>33.0.0-jre</version>
    </dependency>
    ```

    创建布隆过滤器辅助类```RedisBloomFilterHelper```，利用```guava api```封装维护位大小和哈希方法数量（由容量```expectedInsertions```与错误率```fpp```决定）变量以及获取值的位数组方法的类：

    ```bash
    public class RedisBloomFilterHelper<T> {

        private int numHashFunctions;

        private int bitSize;

        private Funnel<T> funnel;

        public RedisBloomFilterHelper(Funnel<T> funnel, int expectedInsertions, double fpp) {
            Preconditions.checkArgument(funnel != null, "funnel不能为空");
            this.funnel = funnel;
            // 计算bit数组长度
            bitSize = optimalNumOfBits(expectedInsertions, fpp);
            // 计算hash方法执行次数
            numHashFunctions = optimalNumOfHashFunctions(expectedInsertions, bitSize);
        }

        public int[] murmurHashOffset(T value) {
            int[] offset = new int[numHashFunctions];
            long hash64 = Hashing.murmur3_128().hashObject(value, funnel).asLong();
            int hash1 = (int) hash64;
            int hash2 = (int) (hash64 >>> 32);
            for (int i = 1; i <= numHashFunctions; i++) {
                int nextHash = hash1 + i * hash2;
                if (nextHash < 0) {
                    nextHash = ~nextHash;
                }
                offset[i - 1] = nextHash % bitSize;
            }
            return offset;
        }

        /**
         * 计算bit数组长度
         */
        private int optimalNumOfBits(long n, double p) {
            if (p == 0) {
                // 设定最小期望长度
                p = Double.MIN_VALUE;
            }
            int sizeOfBitArray = (int) (-n * Math.log(p) / (Math.log(2) * Math.log(2)));
            return sizeOfBitArray;
        }

        /**
         * 计算hash方法执行次数
         */
        private int optimalNumOfHashFunctions(long n, long m) {
            int countOfHash = Math.max(1, (int) Math.round((double) m / n * Math.log(2)));
            return countOfHash;
        }
    }
    ```

    初始化字符串布隆过滤器为```Spring```容器：

    ```bash
    # RedisConfig
    # 初始化容量为1000000，错误率为0.01的字符串布隆过滤器
    @Bean
    public RedisBloomFilterHelper<String> initStringBloomFilterHelper() {
        return new RedisBloomFilterHelper<>((Funnel<String>) (from, into) -> into.putString(from, Charsets.UTF_8), 1000000, 0.01);
    }
    ```

    封装布隆过滤器工具类，实现添加布隆过滤器的值以及检查布隆过滤器的值的方法：

    ```bash
    @Slf4j
    @Service
    public class RedisBloomFilterUtil {

        @Autowired
        private RedisTemplate redisTemplate;

        /**
         * 根据指定的布隆过滤器添加值
         */
        public <T> void addByBloomFilter(RedisBloomFilterHelper<T> redisBloomFilterHelper, String key, T value) {
            Preconditions.checkArgument(redisBloomFilterHelper != null, "redisBloomFilterHelper不能为空");
            int[] offset = redisBloomFilterHelper.murmurHashOffset(value);
            for (int i : offset) {
                log.info("布隆过滤器-{}，添加值：{}", key, value);
                redisTemplate.opsForValue().setBit(key, i, true);
            }
        }

        /**
         * 根据指定的布隆过滤器判断值是否存在
         */
        public <T> boolean includeByBloomFilter(RedisBloomFilterHelper<T> redisBloomFilterHelper, String key, T value) {
            Preconditions.checkArgument(redisBloomFilterHelper != null, "redisBloomFilterHelper不能为空");
            int[] offset = redisBloomFilterHelper.murmurHashOffset(value);
            for (int i : offset) {
                if (!redisTemplate.opsForValue().getBit(key, i)) {
                    return false;
                }
            }
            return true;
        }

    }
    ```

    测试布隆过滤器，可在应用层（如```Controller```）使用布隆过滤器：

    ```bash
    @Autowired
    private RedisBloomFilterHelper redisBloomFilterHelper;

    @Autowired
    private RedisBloomFilterUtil redisBloomFilterUtil;

    @GetMapping("/addRedisBloomFilter")
    public boolean addRedisBloomFilter(@RequestParam String filterName, @RequestParam String value) {
        try {
            redisBloomFilterUtil.addByBloomFilter(redisBloomFilterHelper, filterName, value);
        } catch (Exception e) {
            return false;
        }
        return true;
    }

    @GetMapping("/checkRedisBloomFilter")
    public boolean checkRedisBloomFilter(@RequestParam String filterName, @RequestParam String value) {
        return redisBloomFilterUtil.includeByBloomFilter(redisBloomFilterHelper, filterName, value);
    }
    ```

> 分布式锁

* 分布式锁是控制分布式系统不同进程共同访问共享资源的一种锁的实现。不同的系统或同一系统的不同主机之间共享某个临界资源，需要互斥来防止彼此干扰以确保一致性。分布式锁应该有这些特征：

  * 互斥性：任意时刻，有且只有一个客户端能持有锁。
  * 锁超时释放：持有锁超时时可释放，防止死锁。
  * 可重入性：一个线程持有锁后可再次对其请求加锁。
  * 高性能与高可用：加锁和解锁开销需尽可能低，同时保证高可用。
  * 安全性：锁只能被持有的客户端删除，不能被其他客户端删除。

* 分布式锁实现原理使用以下基本命令：
  
  * ```SETNX key val```：仅当```key```不存在时设置```val```字符串且返回1；若```key```存在时设置失败且返回0。
  * ```EXPIRE key timeout```：为```key```设置超时时间，单位为秒，超过该时间锁则自动释放，避免死锁。
  * ```DEL key```：删除```key```。

    使用```SETNX```与```EXPIRE```命令实现加锁（由于原子性问题，这两条命令需在```LUA```脚本中使用或使用命令```SET key value [expiration EX seconds|PX milliseconds] [NX|XX]```代替）；使用```DEL```命令实现解锁。

* 分布式锁的常见实现：

  * 对于```Redis```单机部署场景，常用```LUA```脚本使用```SETNX```、```EXPIRE```、```GET```以及```DEL```命令实现。
  * 对于```Redis```集群部署场景，常用```Redisson```框架实现。

    以```SpringBoot```为例，上诉两种实现方式可参考[这里]()。对于单机部署可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/redis/redis%20started.md)；对于集群部署可参考[这里](https://gitee.com/FSDGarden/learn-note/blob/master/redis/Use%20docker-compose%20deploy%20redis%20cluster%20server.md)。

> 参考文献

* [5 分钟搞懂布隆过滤器，亿级数据过滤算法你值得拥有！](https://juejin.cn/post/6844904007790673933)
* [记一篇REDIS布隆过滤器的使用](https://zhuanlan.zhihu.com/p/89883126)
* [Redis布隆过滤器（原理+图解）](https://c.biancheng.net/redis/bloom-filter.html)
* [Redis 布隆（Bloom Filter）过滤器原理与实战](https://www.51cto.com/article/704389.html)
* [（Redis使用系列） Springboot 在redis中使用BloomFilter布隆过滤器机制 六](https://developer.aliyun.com/article/951745)
* [SpringBoot 中使用布隆过滤器 Guava、Redission实现](https://juejin.cn/post/7136214205618716709)
* [Redis分布式锁应用（实现+原理）](https://c.biancheng.net/redis/distributed-lock.html)
* [七种方案！探讨Redis分布式锁的正确使用姿势](https://juejin.cn/post/6936956908007850014)