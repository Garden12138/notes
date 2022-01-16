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
  * ```Stream```介绍
    * ```Java8```添加```Stream API```以简化串行或并行执行批量操作的任务。
    * ```Stream API```提供了两个关键抽象：流（```Stream```），表示有限或者无限的数据元素序列；流管道（```Stream Pipeline```），表示对数据元素序列的多级计算。
    * 流的数据元素可来源于任何地方，常见有集合、数组、文件等。流的数据元素类型可以为对象引用或基本类型（```int、double、long```）。
    * ```Stream Pipeline```由源流（```Source Stream```）、零或多个中间操作（```Intermediate Operations```）和一个终结操（```Terminal Operation```）组成。每个中间操作的结果都是转换为另外一个流，其元素类型可相同或不同。终结操作是对最后一个中间操作产生的流进行最终计算，如将元素存储到集合、返回某个元素或打印所有元素。直到终结操作被调用才开始计算，故```Stream Pipeline```是惰性计算求值，没有终结操作的```Stream Pipeline```是一个无操作的指令。```Stream API```允许所有组成```Stream Pipeline```的调用链接在一个表达式上，多个管道也可以链接在一起形式一个表达式。默认情况下，流管道顺序执行，若使流管道并行执行，可在任何流上使用```parallel()```方法（不推荐）。

  * 恰当使用```Stream```，实现从字典中读取单词并打印指定其最小值的所有同位词（两个单词位数相同，组成单词的字母相同且顺序不同）
    * 使用```HashMap```集合框架```API```实现
      ```
      public class Anagrams {
        
        public static void main(String[] args) throws IOException {
          // 获取字典路径、指定同位词的大小
          File dict = new File(args[0]);
          int minGroupSize = Integer.parseInt(args[1]);
          // 使用computeIfAbsent方法，将重新排序单词后作为key，若存在，则返回key对应value值，若不存在，则初始化key-value键值对，最后添加单词至value
          Map<String, Set<String>> groups = new Hash<>();
          try (Scanner scan = new Scanner(dict)) {
            while(scan.hasNext()) {
              String word = scan.next();
              groups.computeIfAbsent(alphabetize(word), () -> new TreeSet<>()).add(word);
            }
          }

          // 输出结果
          for(Set<String> group : groups.values()) {
            if (group.size() >= minGroupSize) {
              System.out.println(group.size() + " : " + group);
            }
          }
        }
        
        // 重新排序单词字母
        private static String alphabetize(String s) {
          char[] ch = s.toCharArray();
          Arrays.sort(ch);
          return new String(ch);
        }

      }
      ```
    * 使用大量```Stream```实现
      ```
      public class Anagrams {
        
        public static void main(String[] args) throws IOException {
          // 获取字典路径、指定同位词的大小
          Path dict = new Paths.get(args[0]);
          int minGroupSize = Integer.parseInt(args[1]);
          // 将文件流进行重新排序单词后分组，分组后过滤符合最小值的分组，重新封装后返回打印
          try (Stream<String> words = Files.lines(dict)) {
            words.collect(Collectors.groupingBy(
                  word -> word.chars().sorted().collect(
                  StringBuilder::new, (sb, c) -> sb.append((char)c), StringBuilder::append).toString()))
                .values().stream().filter(group -> group.size() >= minGroupSize).map(group -> group.size() + " : " + group).forEach(System.out.println);
          }
        }

      }
      ```
    * 恰当使用```Stream```实现
      ```
      public class Anagrams {
        
        public static void main(String[] args) throws IOException {
          // 获取字典路径、指定同位词的大小
          Path dict = new Paths.get(args[0]);
          int minGroupSize = Integer.parseInt(args[1]);
          // 将文件流进行重新排序单词后分组，分组后过滤符合最小值的分组，重新封装后返回打印
          try (Stream<String> words = Files.lines(dict)) {
            words.collect(word -> alphabetize(word))
                .values().stream().filter(g -> g.size() >= minGroupSize).map(g -> g.size() + " : " + g).forEach(System.out.println);
          }
        }

        // 重新排序单词字母
        private static String alphabetize(String s) {
          char[] ch = s.toCharArray();
          Arrays.sort(ch);
          return new String(ch);
        }

      }
      ```
  * 谨慎使用```Stream```
    * 在没有显式类型下，尽量简短命名```lambda```表达式参数
    * 善使用辅助方法实现特点功能，流管道缺少显式类型信息和命名临时变量
    * 流管道使用函数对象（```lambda```表达式或方法引用）表示重复计算，迭代代码使用代码块表示重复计算。函数对象与代码的使用区别：
      * 代码块可以读取或修改范围内的任何局部变量；```lambda```只能读取最终变量且无法修改任何局部变量
      * 代码块可以从封闭方法返回，中断或继续循环，也可以抛出声明此方法的任何已检查异常；lambda表达式不支持。
    * 尽量避免使用```Stream```处理```char```值
    * ```Stream```容易处理统一转换元素序列、过滤元素序列、使用单个操作组合元素序列（如添加、连接或计算最值）、分组元素序列等
    
  * 解决同时访问流管道多个阶段中相应元素
    * 由于流管道将值映射到其他值，原始值就会消失。传统的解决方案是将每个值映射到一个包含原始值和新值的```pair```对象，但这将导致每个阶段都需要维护一个```pair```对象，易造成代码混乱冗长；一个更好的解决方案是在需要访问（```forEach```）早期阶段值时转换映射（```map```）。如设计一个打印前20个梅森素数（满足```2^p - 1```形式的数字，p是素数，```2^p - 1```是素数）的程序：
      ```
      // 返回所有素数的初始流
      public static Stream<BigInteger> primes() {
        return Stream.iterate(TWO, BigInteger::nextProbablePrime);
      }
      // 打印前20个梅森素数
      public static void main(String[] agrs) {
        primes()
          .map(p -> TWO.pow(p.intValueExact()).subtract(ONE))
          .filter(mersenne -> mersenne.isProbablePrime(50))
          .limit(20)
          .forEach(System::out::println);
      }
      ```
      现需要将每个梅森素数前面打印对应指数（```p```）,这个值只出现在初始流（```primes```）中，因此在终结操作中不可访问。由于第一个中间操作中发生映射，可以通过反转计算出（指数```p```是二进制表示的位数，可以使用```bitLength()```方法表示）。
      ```
      .forEach(mp -> System.out.println(mp.bitLength() + " : " + mp));
      ```

> 优先考虑流中无副作用的函数

> 优先使用Collection而不是Stream来作为方法的返回类型

> 谨慎使用流并行