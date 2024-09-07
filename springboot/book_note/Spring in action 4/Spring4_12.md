# Spring4

## Spring集成使用NoSQL数据库

#### 了解Spring Data 对[NoSQL](http://www.runoob.com/mongodb/nosql.html)的支持
* 支持的NoSQL数据库：MongoDB，Neo4j，Redis。
  * 支持运行时自动化生成Repository实现的功能
  * 支持基于模板的数据访问
  * 支持注解映射对象

#### 集成使用[MongoDB](https://www.mongodb.com/)持久化文档数据
* 文档数据：将数据信息收集到一个非规范化（文档）的结构中并且相互独立，以此方式存储的数据称为文档数据。适用于不具有丰富关联关系的数据。
* Spring Data MongoDB对Spring应用中的MongoDB的支持：
  * 支持运行时自动化生成Repository实现的功能
  * 支持基于MongoTemplate模板的数据访问
  * 支持注解映射对象-文档关系
* 集成使用（[快速集成](https://projects.spring.io/spring-data-mongodb/)|[详细文档](http://docs.spring.io/spring-data/mongodb/docs/current/reference/html/)）：
  * 启用MongoDB
  ```
  @Configuration
  @EnableMongoRepositories(basePackages = "com.web.spring4.dao")/*启用MongoDB的自动化生成Repository实现的功能，属性repositoryImplementationPostfix="Stuff"可修改扫描的混合自定义功能的实现类的后缀*/
  public class MongoConfig extends AbstractMongoConfiguration {
    @Autowired
    private Environment env;
    //扩展AbstractMongoConfiguration隐示创建MongoTempalteBean
    //数据库访问
    @Override
    protected String getDatabaseName() {/*指定数据库名称*/
      return "OrdersDB";
    }
    @Override
    public Mongo mongo() throws Exception {/*创建mongo客户端*/
      MongoCredential credential = MongoCredential.createMongoCRCredential(
        env.getProperty("mongo.username"),"OrdersDB",env.getProperty("mongo.password").toCharArray());
      return new MongoClient(new ServerAddress("localhost",37017),Arrays.asList(credential));
    }
  }
  ```
  * 为Model添加注解，实现MongoDB持久化（对象-领域，属性-域）
  ```
  @Document    /*标示映射到文档上的领域对象，声明文档*/
  public class Order {
	@Id         /*标示某个领域的id域，声明文档id*/
  private String id;
	@Field("customer")    /*为文档域指定自定义的元数据，覆盖默认域名*/
	private String customer;
	private String type;  
	private Collection<Item> items = new LinkedHashSet<Item>();
	public String getCustomer() {
		return customer;
	}
	public void setCustomer(String customer) {
		this.customer = customer;
	}
	public String getType() {
		return type;
	}
	public void setType(String type) {
		this.type = type;
	}
	public Collection<Item> getItems() {
		return items;
	}
	public void setItems(Collection<Item> items) {
		this.items = items;
	}
	public String getId() {
		return id;
  }
  }
  //@DbRef：标示某个域要引用其他的文档；@Version：标示版本域
  //除非将属性设置为瞬时态，否则Java对象中所有的属性都会持久化为文档中的域。
  ```
  * 编写MongoDB Repository：Repository接口拓展MongoRepository，继承基本的CRUD操作；自动合并以Impl为后缀的Repository的实现方法。
  ```
  @Repository
  public interface OrderRepository extends MongoRepository<Order, String>,OrderOperations {/*Order为带有@Document注解的对象类型，String为带有@Id的属性类型*/
    //根据Spring Data方法名命名约束添加自定义操作
      List<Order> findByCustomer(String customer);
	  List<Order> findByCustomerLike(String customer);
	  List<Order> findByCustomerAndType(String customer, String type);
	  List<Order> getByType(String type);
	  @Query("{customer:'Chuck Wagon'}")/*JSON查询参数*/
	  List<Order> findChucksOrders();
  }
  ```
  ```
  public interface OrderOperations {
    List<Order> findOrdersByType(String
      @Override
      public List<Order> findOrdersByType(String type);
  }
  ```
  ```
  public class OrderRepositoryImpl implements OrderOperations {
    @Autowired
    private MongoOperations mongo; /*注入MongoOperations（实现MongoTemplate所有方法的接口）*/
    @Override
    public List<Order> findOrdersByType(String t){
      String type = t.equals("NET")?"WEB":t;
      Criteria where = Criteria.where("type").is(t);
      Query query = Query.query(where);
      return mongo.find(query,Order.class);
    }
  }
  ```

#### 集成使用[Neo4j](https://neo4j.com/)持久化图数据
* 图数据：存储到多个细粒度的节点中并且节点之间可以通过关系建立关联的数据。
* Spring Data Neo4j对Spring应用中的Neo4j的支持：
  * 支持运行时自动化生成Repository实现的功能
  * 支持基于Neo4jTemplate模板的数据访问
  * 支持注解映射对象-图（节点与关联）关系
* 集成使用（[快速集成](https://projects.spring.io/spring-data-neo4j/#quick-start)|[详细文档](https://docs.spring.io/spring-data/neo4j/docs/current/reference/html/)）：
  * 启用Neo4j
  ```
  @Configuration
  @EnableNeo4jRepositories(basePackages = "orders.db")/*启用运行时自动化生成Repository实现的功能*/
  public class Neo4jConfig extends Neo4jConfiguration {
    //扩展Neo4jConfiguration隐示创建Neo4jTemplate
    public Neo4jConfig() {    /*设置扫描的模型的基础包包名*/
      setBasePackage("orders");
    }
    //数据库访问
    @Bean(destroyMethod="shutdown")
    public GraphDatabaseService graphDatabaseService(Environment env) {
      //return new GraphDatabaseFactory().newEmbeddedDatabase("/tmp/graphdb");/*配置嵌入式数据库*/
      return new SpringRestGraphDatabase("http://graphdbserver:7474/db/data",
                                         env.getProperty("db.username"),
                                         env.getProperty("db.password"));
    }
  }
  ```
  * 为Model添加[注解](https://docs.spring.io/spring-data/neo4j/docs/current/reference/html/#reference:annotating-entities)，实现Neo4j持久化（对象-图（节点与关联））
  ```
  @NodeEntity    /*声明Order类是节点*/
  public class Order {
    @GraphId    /*声明Graph ID*/
    private Long id;
    private String customer;
    private String type;
    @RelatedTo(type="HAS_ITEMS")    /*与条目的关联关系*/
    private Set<Item> items = new LinkedHashSet<Item>();
    public String getCustomer() {
      return customer;
    }
    public void setCustomer(String customer) {
      this.customer = customer;
    }
    public String getType() {
      return type;
    }
    public void setType(String type) {
      this.type = type;
    }
    public Collection<Item> getItems() {
      return items;
    }
    public void setItems(Set<Item> items) {
      this.items = items;
    }
    public Long getId() {
      return id;
    }
  }
  ```
  ```
  @RelationshipEntity(type="HAS_LINE_ITEM_FOR")/*声明关联关系*/
  public class LineItem {
    @GraphId    /*声明Graph ID*/
    private Long id;
    @StartNode /*声明开始结点*/
    private Order order;
    @EndNode  /*声明结束结点*/
    private Product product;
    private int quantity;
    ...
  }
  ```
  * 编写Neo4j Repository：Repository接口拓展GraphRepository，继承基本的CRUD操作；自动合并以Impl为后缀的Repository的实现方法。
  ```
  @Repository
  public interface OrderRepository extends GraphRepository<Order> extends OrderOperations{
    //根据Spring Data方法名命名约束添加自定义操作
    List<Order> findByCustomer(String customer);
    List<Order> findByCustomerLike(String customer);
    List<Order> findByCustomerAndType(String customer, String type);
    List<Order> getByType(String type);
    @Query("{customer:'Chuck Wagon'}")/*Cypher查询参数*/
    List<Order> findChucksOrders();
  }
  ```
  ```
  public interface OrderOperations {
    List<Order> findSiAOrders();
  }
  ```
  ```
  public class OrderRepositoryImpl implements OrderOperations {
    @Autowired
    private Neo4jOperations neo4j; /*注入Neo4jOperations（实现Neo4jTemplate所有方法的接口）*/
    public List<Order> findSiAOrders() {
      Result<Map<String, Object>> result = neo4j.query(
        "match (o:Order)-[:HAS_ITEMS]->(i:Item) " +
        "where i.product='Spring in Action' return o",
        EndResult<Order> endResult = result.to(Order.class);
        return IteratorUtil.asList(endResult);
      }
    }
  ```

#### 集成使用[Redis](https://redis.io/)持久化key-value数据
* key-value数据：以键值对形式存储的数据
* Spring Data Redis对Spring应用中的Redis的支持：
  * 支持基于RedisTemplate模板的数据访问
* 集成使用（[快速集成](http://projects.spring.io/spring-data-redis/)|[详细文档](https://docs.spring.io/spring-data/data-redis/docs/current/reference/html/)）
  * 启用Redis
  ```
  @Configuration
  public class RedisConfig {
    //RedisTemplate模板配置
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory cf) {
      RedisTemplate<String, Object> redis = new RedisTemplate<String, Object>();
      redis.setConnectionFactory(cf);
      return redis;
    }
    //连接Redis配置
    @Bean
    public RedisConnectionFactory redisCF() {
      JedisConnectionFactory cf = new JedisConnectionFactory();
      cf.setHostName("redis-server");
      cf.setPort(7379);
      cf.setPassword("foobared");
      return cf;
    }
  }
  ```
  * 编写Repository：[RedisTemplate API](https://docs.spring.io/spring-data/data-redis/docs/current/api/org/springframework/data/redis/core/RedisTemplate.html)
  ```
  @Repository
  public class OrderRepositoryImpl implements OrderRepository {
    @Autowired
    private RedisTemplate redis;
    ...
    }
  ```
