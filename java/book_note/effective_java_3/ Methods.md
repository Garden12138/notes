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

> 仔细设计方法签名

> 明智审慎地使用重载

> 明智审慎地使用可变参数

> 返回空的数组或集合，不要返回 null

> 明智审慎地返回 Optional

> 为所有已公开的 API 元素编写文档注释