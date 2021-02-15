## EffectiveJava3

#### 创建与销毁对象

> 考虑使用静态工厂方法替代构造方法

  * 公共静态工厂方法，返回类实例，为客户端获取类实例提供另外一种构造方式。如Boolean类的公共静态工厂方法valueOf：
    ```
    public static final Boolean TRUE = new Boolean(true);
    public static final Boolean FALSE = new Boolean(false);
    ...
    public static Boolean valueOf(boolean b) {
        return (b ? TRUE : FALSE);
    }
    ...
    ```
  * 公共静态工厂方法的优点是选择替代公共构造方法的关键
    * 可自定义方法签名。一个类只能有一个给定签名的构造方法，不同构造方法只能由参数类型及其顺序判断，API用户需结合文档才能正确调用，而静态工厂方法可自定义方法签名，API用户可从方法签名获取方法调用信息。例如BigInteger：
      ```
      // 返回一个可能为素数的BigInteger
      // 构造方法
      BigInteger(int,int,Random)
      // 静态工厂方法
      BigInteger.probablePrime(int,Randoms)
      ```
    * 无需每次调用都创建新对象实例。不可变类使用预先构建的实例或在构造时缓存实例并反复分配它们以避免创建不必要的重复对象。例如Boolean：
      ```
      public static final Boolean TRUE = new Boolean(true);
      public static final Boolean FALSE = new Boolean(false);
      ...
      public static Boolean valueOf(boolean b) {
        return (b ? TRUE : FALSE);
      }
      ...
      ```
    * 可返回其类型的任意子类型对象实例。常应用于基于接口的框架，其中接口为静态工厂方法提供自然返回类型。例如Collections：
      ```
      public static <K,V> Map<K,V> unmodifiableMap(Map<? extends K, ? extends V> m) {
        return new UnmodifiableMap<>(m);
      }
      private static class UnmodifiableMap<K,V> implements Map<K,V>, Serializable
      {
        ...
      }
      ```
    * 可根据入参选择返回其类型的子类型对象实例。静态工厂方法的返回类型根据入参条件返回不同的子类型。例如EnumSet：
      ```
      public static <E extends Enum<E>> EnumSet<E> noneOf(Class<E> elementType) {
        Enum<?>[] universe = getUniverse(elementType);
        if (universe == null)
            throw new ClassCastException(elementType + " not an enum");
        if (universe.length <= 64)
            return new RegularEnumSet<>(elementType, universe);
        else
            return new JumboEnumSet<>(elementType, universe);
      }
      ```
    * 返回对象的类型可不存在。常应用于服务提供者框架，服务提供者框架有三个基本组，服务接口、提供者注册API、服务访问API，其中服务访问API为灵活的静态工厂方法。例如Java 数据库连接 API（JDBC），Connection为服务接口，DriverManager.registerDriver为提供者注册API、DriverManager.getConnection为服务访问API，Driver为服务提供者接口。
      ```
      private static Connection getConnection(
        String url, java.util.Properties info, Class<?> caller) throws SQLException {
          ...
          for(DriverInfo aDriver : registeredDrivers) {
            // If the caller does not have permission to load the driver then
            // skip it.
            if(isDriverAllowed(aDriver.driver, callerCL)) {
                try {
                    println("    trying " + aDriver.driver.getClass().getName());
                    Connection con = aDriver.driver.connect(url, info);
                    if (con != null) {
                        // Success!
                        println("getConnection returning " + aDriver.driver.getClass().getName());
                        return (con);
                    }
                } catch (SQLException ex) {
                    if (reason == null) {
                        reason = ex;
                    }
                }

            } else {
                println("    skipping: " + aDriver.getClass().getName());
            }

        }
        ...
      }
      ```
  * 公共静态工厂方法的缺点要求选择替代公共构造方法的标准
    * 只提供公共静态工厂方法，没有公共或受保护构造方法的类不能被子类化。推荐使用组合方式而非继承。
    * 自定义方法签名易造成命名不规范导致客户端在使用时难以确认是否为公共静态工厂方法。建议使用遵守标准的命名习惯，如下：
      * from：类型转换方法，接受单个参数并返回此类型相应的对象实例，如 Date date = Date.from(instant);
      * of：聚合方法，接受多个参数合并后再返回此类型相应的对象实例，如 EnumSet enumSet = EnumSet.of(JACK,QUEEN,KING);
      * valueOf：from更为详细的替代方式，如 Boolean boolean = Boolean.valueOf(true);
      * instance/getInstance：返回一个由参数描述(如果有)的对象实例，对象实例不一定具有相同的值，如 DateFormat dateFormat = DateFormat.getInstance();
      * create/newInstance：与instance/getInstance类似，且保证每次调用返回一个新的实例，如 Object newArr = Array.newInstance(class,arrLen);
      * getType：与getInstance类似，但在公共静态工厂方法处于不同类时使用，如 FileStore fileStore = Files.getFileStore(path);
      * newType：与newInstance类似，但在公共静态工厂方法处于不同类时使用，如 BufferedReader bufferedReader = Files.getBufferedReader(path);

> 当可选参数过多时考虑使用Builder模式
  * 构造方法与静态工厂方法都有不能友好扩展可选参数的限制，常见扩展可选参数的模式有可伸缩构造方法模式，JavaBeans模式以及Builder模式。
  * 可伸缩构造方法模式
    ```
    // 类设计
    public class Hamburger {
      // required
      private final int bread;
      private final int vegetables;
      private final int egg;
      // optional
      private final int chicken;
      private final int beef;
      private final int shrimp;

      public Hamburger(int bread, int vegetables, int egg) {
        this(bread,vegetables,egg,0);
      }

      public Hamburger(int bread, int vegetables, int egg, int chicken) {
        this(bread,vegetables,egg,chicken,0);
      }

      public Hamburger(int bread, int vegetables, int egg, int chicken, int beef) {
        this(bread,vegetables,egg,chicken,beef,0);
      }

      public Hamburger(int bread, int vegetables, int egg, int chicken, int beef, int shrimp) {
        this.bread = bread;
        this.vegetables = vegetables;
        this.egg = egg;
        this.chicken = chicken;
        this.beef = beef;
        this.shrimp = shrimp;
      }
    }
    // 客户端调用
    // 双层鸡肉堡
    Hamburger doubleChickenHamburger = new Hamburger(2,2,2,2);
    // 单层鸡肉牛肉虾堡
    Hamburger singleChickenBeefShrimpHamburger = new Hamburger(2,1,1,1,1,1);
    ```
  * JavaBeans模式
    ```
    // 类设计
    public class Hamburger {
      // required
      private int bread;
      private int vegetables;
      private int egg;
      // optional
      private int chicken;
      private int beef;
      private int shrimp;

      public Hamburger() {

      }

      public void setBread(int bread) {
        this.bread = bread;
      }
      public void setVegetables(int vegetables) {
        this.vegetables = vegetables;
      }
      public void setEgg(int egg) {
        this.egg = egg;
      }
      public void setChicken(int chicken) {
        this.chicken = chicken;
      }
      public void setBeef(int beef) {
        this.beef = beef;
      }
      public void setShrimp(int shrimp) {
        this.shrimp = shrimp;
      }
    }
    // 客户端调用
    // 双层鸡肉堡
    Hamburger doubleChickenHamburger = new Hamburger();
    doubleChickenHamburger.setBread(2);
    doubleChickenHamburger.setVegetables(2);
    doubleChickenHamburger.setEgg(2);
    doubleChickenHamburger.setChicken(2);
    // 单层鸡肉牛肉虾堡
    Hamburger singleChickenBeefShrimpHamburger = new Hamburger();
    singleChickenBeefShrimpHamburger.setBread(2);
    singleChickenBeefShrimpHamburger.setVegetables(1);
    singleChickenBeefShrimpHamburger.setEgg(1);
    singleChickenBeefShrimpHamburger.setChicken(1);
    singleChickenBeefShrimpHamburger.setBeef(1);
    singleChickenBeefShrimpHamburger.setShrimp(1);
    ```
  * Builder模式
    ```
    // 具体类的具体Builder
    // 类设计
    public class Hamburger {
      // required
      private final int bread;
      private final int vegetables;
      private final int egg;
      // optional
      private final int chicken;
      private final int beef;
      private final int shrimp;

      public static class Builder {
        // required
        private final int bread;
        private final int vegetables;
        private final int egg;
        // optional
        private int chicken = 0;
        private int beef = 0;
        private int shrimp = 0;

        public Builder(int bread, int vegetables, int egg) {
          this.bread = bread;
          this.vegetables = vegetables;
          this.egg = egg;
        }

        public Builder chicken(int chicken) {
          this.chicken = chicken;
          return this;
        }
        public Builder beef(int beef) {
          this.beef = beef;
          return this;
        }
        public Builder shrimp(int shrimp) {
          this.shrimp = shrimp;
          return this;
        }

        public Hamburger build() {
          return new Hamburger(this);
        }
      }

      public Hamburger(Builder builder) {
        this.bread = builder.bread;
        this.vegetables = builder.vegetables;
        this.egg = builder.egg;
        this.chicken = builder.chicken;
        this.beef = builder.beef;
        this.shrimp = builder.shrimp;
      }
    }
    // 客户端调用
    // 双层鸡肉堡
    Hamburger doubleChickenHamburger = new Hamburger.Builder(2,2,2).chicken(2).build();
    // 单层鸡肉牛肉虾堡
    Hamburger singleChickenBeefShrimpHamburger = new Hamburger.Builder(2,1,1).chicken(1).beef(1).shrimp(1).build();
    ```
    ```
    // 抽象类的抽象Builder
    // 类设计
    public abstract class Hamburger {
      // required
      private final int bread;
      private final int vegetables;
      private final int egg;
      
      public abstract static class Builder<T extends Builder<T>> {
        private int bread;
        private int vegetables;
        private int egg;
        
        public T baseHamburger(int bread, int vegetables, int egg) {
          this.bread = bread;
          this.vegetables = vegetables;
          this.egg = egg;
          return self();
        }
        public abstract Hamburger build();
        protected abstract T self();
      }

      public Hamburger(Builder<?> builder){
        this.bread = builder.bread;
        this.vegetables = builder.vegetables;
        this.egg = builder.egg;
      }
    }
    public class KFCHamburger extends Hamburger {
      private final int chicken;

      public static class Builder extends Hamburger.Builder<Builder> {
        private int chicken;

        public Builder chicken(int chicken) {
          this.chicken = chicken;
          return this;
        }
        @Override
        public KFCHamburger build() {
          return new KFCHamburger(this);
        }
        @Override
        public Builder self() {
          return this;
        }
      }
      private KFCHamburger(Builder builder) {
        super(builder);
        this.chicken = builder.chicken;
      }
    }
    public class MCHamburger extends Hamburger {
      private final int beef;

      public static class Builder extends Hamburger.Builder<Builder> {
        private int beef;

        public Builder beef(int beef) {
          this.beef = beef;
          return this;
        }
        @Override
        public MCHamburger build() {
          return new MCHamburger(this);
        }
        @Override
        public Builder self() {
          return this;
        }
      }
      private MCHamburger(Builder builder) {
        super(builder);
        this.beef = builder.beef;
      }
    }
    // 客户端调用
    // 单层KFC鸡肉堡
    KFCHamburger singleKFCChickenHamburger = new KFCHamburger.Builder().baseHamburger(1,1,1).chicken(1).build();
    // 单层MC牛肉堡
    MCHamburger singleMCBeefHamburger = new MCHamburger.Builder().baseHamburger(1,1,1).beef(1).build();
    ```
  * 可读性与安全性

    | 性质\模式 | 可伸缩构造方法模式 | JavaBeans模式 | Builder模式 |
    | :-----| :----: | :----: | :----: |
    | 可读性 | ❎ | ✅ | ✅ |
    | 安全性 | ✅ | ❎ | ✅ |


> 使用私有构造方法或枚举类实现Singleton
  * Singleton单例是一个仅实例化一次的类，单例对象通常为无状态，如函数或本质上唯一的系统组件。实现单例的常见方法有，私有构造方法与公共静态属性、私有构造方法与公共静态工厂方法、单一元素枚举类。
  * 私有构造方法与公共静态属性
    ```
    public class Singleton {
      public static final Singleton instance = new Singleton();
      private Singleton() {
      }
    }
    ```
  * 私有构造方法与公共静态工厂方法
    ```
    public class Singleton {
      private static final Singleton instance = new Singleton();
      private Singleton() {
      }
      public static Singleton getInstance() {
        return instance;
      }
    }
    ```
  * 单一元素枚举类
    ```
    public enum Singleton {
      INSTANCE;
    }
    ```
  * 说明
    * 特权客户端可使用AccessibleObject.setAccessible方法以反射方式调用私有构造方法，如需防御此攻击，可在构造函数添加请求创建第二个实例时抛出异常。
      ```
      public class Singleton {
        public static final Singleton instance = new Singleton();
        private Singleton() {
          if (null != instance) {
            throw new RuntimeException();
          }
        }
      }
      ```
    * 私有构造方法模式的序列化
      * 添加```implements Serializable```声明。
      * 必须声明所有的实例字段为```transient```。
      * 防止每当序列化的实例被反序列化时，就会创建一个新的实例的问题
        ```
        private Object readResolve() {
          return instance;
        }
        ```
    * 静态工厂方法的优势
      * 提供了灵活性，在不改API的前提下，可修改该类是否应该为单例的做法。
      * 可编写泛型单例工厂。
      * 可通过方法引用作为提供者，```Singleton::getInstance``` 等同于 ```Supplier<Singleton>```。
    * 单一元素枚举的优势，更简洁，无偿提供序列化机制，通常是实现单例的最佳方式。
    * 单一元素枚举的不足，单例不能继承Enum以外的父类。


> 使用私有构造方法执行非实例化

> 依赖注入优于硬连接资源

> 避免创建不必要的对象

> 消除过期的对象引用

> 避免使用Finalizer和Cleaner机制

> 使用try-with-resources语句替代try-finally语句