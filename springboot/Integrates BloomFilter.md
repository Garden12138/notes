## SpringBoot 集成 Redis 布隆过滤器

> 简介

* 布隆过滤器是一个高空间利用率的概率性数据结构，常用于缓存穿透场景。

> 集成步骤

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
