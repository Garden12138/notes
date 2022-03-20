## EffectiveJava3

#### 方法

> 检查参数有效性
  * 大多数方法和构造方法可对值传递至对应参数进行限制，如索引值必须为非负数，对象引用必须为非```null```等。限制时需要在方法文档中记载这些限制，且在方法主体开头用检查来强制执行。若将无效参数值传递给方法，且该方法在执行之前检查其参数，则抛出适当的异常后调用程序快速且清楚地以失败结束。若该方法无法检查其参数，可能在方法处理过程中会发生难以意料的异常，也有可能以错误的方法计算结果或将某个对象至于受损状态（将来某个未确定的时间点在代码中某些不相关处导致错误）正常返回。无法验证参数可能导致违反故障原子性。
  * 对于公共和受保护方法，使用```Java```文档```@throws```注解记载违反参数限制时将引发的异常，如：
    ```
    /**
     * @throws ArithmeticException if m is less than or equal to 0
     */
    public BigInteger mod(BigInteger m) { 
        if (m.signum() <= 0) 
            throw new ArithmeticException("Modulus <= 0: " + m); 
            ... // Do the computation 
    }
    ```
    文档注释没有记载```NullPointerException```，该异常记载在类级别文档注释中，类级别的注释应用于类的所有公共方法中的所有参数。这是避免在每个方法上分别记录每个```NullPointerException```。
  * 校验参数的常见方式：
    * 使用```Java7```中添加的```Objects.requireNonNull```方法，该方法执行空值检查，可自定义异常信息返回：
      ```
      // Inline use of Java's null-checking facility 
      this.strategy = Objects.requireNonNull(strategy, "strategy");
      ```
    * 使用```Java9```中添加的```java.util.Objects```类，用于范围检查，此工具类包含三个方法：```checkFromIndexSize```、```checkFromToIndex```、```checkIndex```。仅用于列表和数组索引。
    * 非公有方法可使用断言检查参数：
      ```
      private static void sort(long a[], int offset, int length) { 
          assert a != null; 
          assert offset >= 0 && offset <= a.length; 
          assert length >= 0 && length <= a.length - offset; 
          ... // Do the computation 
      }
      ```
      与普通有效性检查不同，断言若失败则会抛出```AssertionError```。与普通有效性检查不同，需要使用```-ea```或```-enableasserttions```标记传递给```java```命令来启动它，否则将不产生效果。
    * 检查参数有效性：
      * 构造方法中应该检查需要存储供使用的参数的有效性，防止违反构造对象违反类不变性。
      * 执行计算之前显式检查方法的参数。若此时检查参数有效性比较昂贵或不切实际的情况且在执行计算过程中隐式执行检查，不用执行计算之前显式检查方法的参数，如对象列表进行排序```Collections.sort(List)```，在对列表排序过程中，列表中的每个对象都与其他对象进行比较，若不可相互比较，则抛出```ClassCastException```异常，因此提前检查列表中元素是否具有可比性是没有意义的。计算过程中隐式检查抛出的异常与文档方法记载的异常抛出不匹配时，需要通过异常翻译转换为正确的异常。

> 必要时进行防御性拷贝
  * ```Java```是一种安全的语言，在缺少本地方法（```native methods```）情况下，不受缓冲区溢出、数组溢出等不安全语言的内存损坏错误的影响。在安全语言中，可以编写类并保持不变量不变，必要时需防御性地编写程序，避免类的客户端试图摧毁类其不变量。在无意的情况下，可能通过其他对象的帮助，修改对象的内部状态，如实现一个不可变时间期间的类：
    ```
    public final class Period {
      
      private final Date start;
      private final Date end;

      public Period(Date start, Date end) {
        if (start.compareTo(end) > 0) {
          throw new IllegalArgumentException(start + " after " + end);
        }
        this.start = start;
        this.end = end;
      }

      public Date start() {
        return start;
      }

      public Date end() {
        return end;
      }

    }
    ```
    利用```Date```可变性修改```Period```内部状态：
    ```
    Date start = new Date();
    Date end = new Date();
    Period p = new Period(start, end);
    end.setYear(78); // 修改实例p内部状态
    ```
    解决此类问题，简单的方法是使用不可变的对应类型作为内部状态的类型替代，如使用```Instant```、```LocalDateTime```或```ZonedDateTime```替代```Date```。另外一种解决办法是使用防御性拷贝作用于构造方法与实例方法中，如：
    ```
    public final class Period {
      
      private final Date start;
      private final Date end;

      public Period(Date start, Date end) {
        this.start = new Date(start.getTime());
        this.end = new Date(end.getTime());

        if (this.start.compareTo(this.end) > 0) {
          throw new IllegalArgumentException(this.start + " after " + this.end);
        }
      }

      public Date start() {
        return new Date(start.getTime());
      }

      public Date end() {
        return new Date(end.getTime());
      }

    }
    ```
    有效性检查是在拷贝上而不是客户端实例进行，它在检查参数和拷贝参数之间的漏洞窗口期保护类不受其他线程对参数的更改的影响，避免```time-of-check/time-of-use```（```TOCTOU```）攻击。
  * 构造方法中不使用```clone```方法对其类型可由不可信任子类化的参数进行防御性拷贝；因内部状态类型是可信任的，实例方法中可用```clone```方法进行防御性拷贝。
  * 若类有从客户端获取或返回的可变组件，那么这个类必须防御性拷贝这些组件，如果拷贝成本较高，并且信任客户端不会不适当地修改这些组件，则可使用文档替换防御性拷贝，文档概述客户端不得修改受影响组件的责任。

> 仔细设计方法签名

> 明智审慎地使用重载

> 明智审慎地使用可变参数

> 返回空的数组或集合，不要返回 null

> 明智审慎地返回 Optional

> 为所有已公开的 API 元素编写文档注释