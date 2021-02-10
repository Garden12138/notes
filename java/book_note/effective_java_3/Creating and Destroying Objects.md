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

> 当构造方法参数过多时使用builder模式

> 使用私有构造方法或枚举类实Singleton属性

> 使用私有构造方法执行非实例化

> 依赖注入优于硬连接资源

> 避免创建不必要的对象

> 消除过期的对象引用

> 避免使用Finalizer和Cleaner机制

> 使用try-with-resources语句替代try-finally语句