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

> 优先使用标准的函数式接口

> 明智审慎地使用Stream

> 优先考虑流中无副作用的函数

> 优先使用Collection而不是Stream来作为方法的返回类型

> 谨慎使用流并行