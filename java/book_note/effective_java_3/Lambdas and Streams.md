## EffectiveJava3

#### Lambdas与Streams

> lambda表达式优于匿名类
  * 以前常使用单一抽象方法的接口或抽象类作为函数类型，函数实例表示函数或行为动作，创建函数实例对象的方式为实例化匿名类，如按照字符串长度顺序对列表元素进行排序
    ```
    Collections.sort(words, new Comparator<String>() { 
        public int compare(String s1, String s2) { 
            return Integer.compare(s1.length(), s2.length()); 
        } 
    });
    ```
    由于匿名类比较冗长，```Java8```中添加了函数式接口、```lambda```表达式和方法引用，以便更容易创建函数实例对象：
    ```
    Collections.sort(words, (s1, s2) -> Integer.compare(s1.length(), s2.length()));
    ```
    ```lambda```表达式只包含函数参数以及函数行为，参数类型以及返回值类型通过上下文进行类型推断，为了能够正确进行类型推断，函数式接口在声明时使用泛型类型：
    ```
    @FunctionalInterface
    public interface Comparator<T> {
        int compare(T o1, T o2);
    }
    ```
    另外，使用内置比较构造器可以更加简洁：
    ```
    Collections.sort(words, comparingInt(String::length));
    ```
* lambda表达式应用在每个枚举都不同应用行为的枚举类型中。Operation枚举中不同操作类型进行不同的算术计算：
  ```
  // 没有使用lambda表达式
  public enum Operation { 
      PLUS("+") { 
          public double apply(double x, double y) { return x + y; } 
      },
      MINUS("-") { 
          public double apply(double x, double y) { return x - y; } 
      },
      TIMES("*") {
          public double apply(double x, double y) { return x * y; } 
      },
      DIVIDE("/") { public double apply(double x, double y) { return x / y; } 
      };
      
      private final String symbol; 
      Operation(String symbol) { 
          this.symbol = symbol; 
      } 
      
      @Override public String toString() { 
          return symbol; 
      } 
      
      public abstract double apply(double x, double y); 
  }
  // 使用lambda表达式
    public enum Operation { 
      PLUS("+", "x + y"),
      MINUS("-", "x - y"),
      TIMES("*", "x * y"),
      DIVIDE("/", "x / y");
      
      private final String symbol;
      private final DoubleBinaryOperator op; 
      Operation(String symbol, DoubleBinaryOperator op) { 
          this.symbol = symbol; 
          this.op = op;
      } 
      
      @Override public String toString() { 
          return symbol; 
      } 
      
      public abstract double apply(double x, double y); 
  }
  ```
* lambda表达式与匿名类的适用场景：
  * 如果函数不是自计算或者多行，选择使用匿名类。
  * 如果需要访问实例属性或者方法，选择使用匿名类。
  * 如果需要创建抽象类或多个抽象方法的实例，选择使用匿名类。
  * 如果需要使用关键字```this```引用实例对象，选择使用匿名类。
  * 对于支持函数式接口的```API```,选择使用```lambda```表达式。

> 方法引用优于lambda表达式
  * 方法引用是由```Java```提供一种比```lambda```表达式还有简洁的生成函数对象的方法。如维护一个```key```为键，```value```为值的集合```map```，其中```value```为```key```实例的个数：
    ```
    // Java8的Map接口支持merge方法，若键值映射不存在，则新增键值映射，插入给定值；若键值映射存在，则当前值与给定值应用与给定函数，且结果覆盖当前值。

    // 使用lambda表达式
    map.merge(key, 1, (count, incr) -> count + incr);
    // 使用方法引用（Integer提供的一个静态方法sum）
    map.merge(key, 1, Integer::sum);
    ```
    方法引用更加简洁，减少模版代码，但可读性、可维护性比较差。
  * 方法引用的多种方式：

    |方法引用类型|举例|Lambda等式|
    |:------:|:------:|:------:|
    |Static|Integer::parseInt|str -> Integer.parseInt(str)|
    |Bound|Instant.now()::isAfter|Instant then = Instant.now(); t -> then.isAfter(t)|
    |Unbound|String::toLowerCase|str -> str.toLowerCase()|
    |Class Constructor|TreeMap<K, V>::new|() -> new TreeMap<K, V>
    |Array Constructor|int[]::new|len -> new int[len]|
   

> 优先使用标准的函数式接口
  * ```lambda```表达式的普遍应用让编写```API```的实践方式发生改变，以往通过编写子类重写原始方法以专门化父类的行为方式逐渐由提供一个静态工厂方法或构造方法接受函数对象参数的方式替代，如使用```LinkedHashMap```的```removeEldestEntry```方法辅助实现缓存功能：
    ```
    // 子类重写
    @Override
    protected boolean removeEldestEntry(Map.Entry<K,V> eldest) { 
        return size() > 100; 
    }
    // 函数式接口编写
    @FunctionalInterface 
    public interface EldestEntryRemovalFunction<K,V> {
        boolean remove(Map<K,V> map, Map.Entry<K,V> eldest); 
    }
    ```
    但```Java```类库提供了标准的函数式接口```BiPredicate<Map<K,V>, Map.Entry<K,V>>```使用，所以不必要自定义编写函数式接口```
    EldestEntryRemovalFunction```。
  * ```java.util.Function```提供了43个标准的函数式接口，它们由六大基本函数式接口及其衍生接口组成：
    |接口|方法|示例|
    |:------:|:------:|:------:|
    |UnaryOperator```<T>```|T apply(T t)|String::toLowerCase|
    |BinaryOperator```<T>```|T apply(T t1, T t2)|BigInteger::add|
    |Predicate```<T>```|boolean test(T t)|Collection::isEmpty|
    |Function```<T,R>```|R apply(T t)|Arrays::asList|
    |Supplier```<T>```|T get()|Instant::now|
    |Consumer```<T>```|void accept(T t)|System.out::println|
  * 自定义函数式接口的条件：
    * 标准函数式接口不满足当前需求
    * 它将被广泛使用且可以从描述性名称中受益
    * 它拥有强大的契约
    * 它受益于自定义的默认方法
  * 声明自定义函数式接口：
    * 使用注解```@FunctionalInterface```标注函数式接口
    * 设计唯一一个抽象方法
  * 注意事项：
    * 不应该重载多个不同类型的函数式接口参数对象
    * [Stream与Lambda实践](https://gitee.com/FSDGarden/learn-note/blob/master/java/action/Stream%20And%20Lambda%20Action.md)

> 明智审慎地使用Stream

> 优先考虑流中无副作用的函数

> 优先使用Collection而不是Stream来作为方法的返回类型

> 谨慎使用流并行