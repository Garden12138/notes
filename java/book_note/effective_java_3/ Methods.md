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
  * 不过分地提供方便的方法。类中每个方法都应履行其职责，太多的方法使得类难以学习、使用、文档化、测试和维护。对于类货接口支持的每个操作提供一个功能完整的方法，只有在其经常使用时，才考虑提供。
  * 仔细选择方法名名称。名称应始终遵守标准命名约定，选择与同一包中的其他名称一致（如```xxxEntity```）且易于理解的、更广泛共识一致的名称。避免使用较长名称。若有选择方法名称困难，可参考```Java```类库```API```。
  * 避免过长的参数列表。标准的参数列表个数为四个或更少。过长的参数列表可能导致调用者容易忘记参数列表上各个参数的含义，如遇到相同类型参数的长序列，容易调用时弄错参数顺序，虽然程序仍然会编译和运行，但结果不正确。缩短过长的参数列表的常用方式：
    * 将方法分解为多个方法，每个方法只需要参数的一个子集，通过增加正交性减少方法个数。如```java.util.List```接口，它没有提供查找子列表中元素的第一个或最后一个索引的方法，这个方法需要三个参数，它提供了```subList```方法（该方法接受两个参数并返回子列表的视图）与```indexOf```或```lastIndexOf```方法（这两个方法都接受一个参数并返回索引）结合使用，实现查找子列表中元素的索引位置。
    * 创建辅助类保存参数组。这些辅助类通常是静态成员类。若一个频繁出现的参数序列表示某个不同的实体，建议使用这种方式。如正在编写一个表示纸牌游戏的类，并且发现不断地传递一个由两个参数组成的序列，这些参数表示纸牌的点数和花色，添加一个辅助类表示卡片，并用辅助类的单个参数替换参数序列的每次出现，此时```API```和类的内部结构会受益。
    * 从对象构造到方法调用采用```Builder```模式。若一个方法有许多参数，其中包含可选参数，那么可定一个对象来表示所有参数，并允许客户端在这个对象上进行多个```setter```调用，每次设置一个参数或较小相关的组，设置好所需的参数后，客户端调用```execute```方法，该方法对参数进行最后的有效性检查并执行实际的计算。
  * 参数类型优先选择接口。使用接口定义参数，可支持传递实现接口的类。
  * 与布尔型参数相比，优先使用两个元素枚举类型，除非布尔型参数的含义在方法名中是明确的。枚举类型使用代码更容易阅读和编写，还可以方便地在以后添加更多选项。如```Thermometer```类型的静态工厂方法，该方法的签名使用以下枚举饿类型：
    ```
    public enum TemperatureScale { FAHRENHEIT, CELSIUS }
    ```
    ```Thermometer.newInstance(TemperatureScale.CELSIUS)```不仅比```Thermometer.newInstance(true)```更有意义，而且在新版本中将``` KELVIN```添加到```TemperatureScale```中，无需向```Thermometer```添加新的静态工厂。此外还可将温度刻度```（temperature-scale）```依赖关系重构为枚举常量的方法，如每个刻度常量可以有一个采用```double```值并将其转换为```Celsius```的方法。

> 明智审慎地使用重载
  * 重载方法之间的选择是静态的，在编译时选择；重写方法之间的选择是动态的，在运行时选择。如：
    ```
    public class CollectionClassifier {
      public static String classify(Set<?> set) {
        return "Set";
      }
      public static String classify(List<?> list) {
        return "List";
      }
      public static String classify(Collection collection) {
        return "Unknow Collection";
      }

      public static void main() {
        Collection<?>[] collections = {
          new HashSet<String>(),
          new ArrayList<BigInteger>(),
          new HashMap<String, String>().values()
        };
        for(Collection<?> c : collections) {
          System.out.println(classify(cP));
        }
      }
    }
    ```
    ```
    Unknow Collection
    Unknow Collection
    Unknow Collection
    ```
    对于所有的迭代，参数在编译时类型是相同的，所以选择参数类型为```Collection<?>```。
    ```
    public class Wine {
      public String name() {
        return "Wine";
      }
    }

    public class SparkingWine extends Wine {
      @Override
      public String name() {
        return "sparking wine";
      }
    }

    public class Champagne extends SparkingWine {
      @Override
      public String name() {
        return "champagne";
      }
    }

    public class Overriding {
      public static void main(String[] args) {
        List<Wine> wineList = List.of(new Wine(), new SparklingWine(), new Champagne());

        for(Wine wine : wineList) {
          System.out.println(wine.name());
        }
      }
    }
    ```
    ```
    Wine
    sparking wine
    champagne
    ```
    对于所有的迭代，实例在执行各自的重写方法。
  * 应该避免混淆使用重载。重载容易混淆对方法调用行为的期望，不知为给定的参数集调用多个方法重载方法中的具体一个，使用```API```容易导致错误。
  * 谨慎使用方法重载。一个安全且保守的策略是不要导出两个具有相同参数数量的重载。若清楚各个重载方法将应用于任何给定的实际参数集，那么可导出相同数量的多个重载方法，在这种情况下，重载中至少有一个对应的形式参数具有完全不用的类型（不可能将任何非空表达式强制转换为这对类型）。```Java8```中不要在相同参数位置重载采用不同函数式结构的方法。
  * 可以为方法赋予不同名称的方式替代方法重载。如```ObjectOutputStream```类的```writeBoolean(boolean)```、```writeInt(int)```和```writeLong(long)```。但对于构造方法，无法使用不同方法名称，类的多个构造方法总是被重载。
  * 允许同一个对象引用调用完全相同行为的重载方法，确保这种行为的标准方法是将更具体的重载方法调用转发给更一般的重载方法，如：
    ```
    public boolean contentEquals(StringBuffer sb) {
      return contentEquals((CharSequence) sb);
    }
    ```
  * 总结：最好避免重载具有相同数量参数的多个签名的方法。在某些情况下，如涉及构造方法的情况下，可能无法遵循此建议。在这些情况下，至少应避免通过添加强制转换将相同的参数集传递给不同的重载。如果这是无法避免的，如对现有类进行改造以实现新接口，那么应该确保在传递相同参数时所有重载行为都是相同的（```contentEquals(StringBuffer sb)```、```contentEquals((CharSequence) sb)```）。若无法遵循此要求，将不考虑使用重载方法或构造方法。

> 明智审慎地使用可变参数
  * 可变参数方法，即可变的参数数量方法，接受零个或多个指定类型的参数。可变参数的机制是首先创建一个数组，其大小由调用时参数数量决定，然后将参数值放入数组，最后将数组传递给方法。如设计一个接受一系列```int```类型的参数并返回它们的总和：
    ```
    public static int sum(int ...args) {
      int sum = 0;
      for (int arg : args) {
        sum += arg;
      }
      return sun;
    }
    ```
  * 若客户端不传递任何参数，单纯使用可变参数，容易导致异常，如：
    ```
    public static int min(int ..args) {
      int min = args[0];
      for (int i = 1; i < args.length; i++) {
        if(args[i] < min) {
          min = args[i]
        }
      }
      return min;
    }
    ```
    参数```args```客户端传空时，程序发生异常。可使用参数的有效性检查或将最小值```min```初始化为```Integer.MAX_VALUE```：
    ```
    public static int min(int ..args) {
      if(args.length == 0) {
        throw new IllegalArgumentException("too few arguments");
      }
      int min = args[0];
      for (int i = 1; i < args.length; i++) {
        if(args[i] < min) {
          min = args[i]
        }
      }
      return min;
    }
    ```
    ```
    public static int min(int ..args) {
      int min = Integer.MAX_VALUE;
      for (int i = 0; i < args.length; i++) {
        if(args[i] < min) {
          min = args[i]
        }
      }
      return min;
    }
    ```
    更好的解决是声明两个参数，第一个为指定类型的普通参数，第二个为此类型的可变参数：
    ```
    public static int min(int firstArg, int ...args) {
      int min = firstArg;
      for(int arg : args) {
        if(arg < min) {
          min = arg
        }
      }
      return min;
    }
    ```
  * 关键性能下谨慎使用可变参数，每次调用可变参数都会导致数组分配和初始化。若是关心性能成本，但又需要可变参数的灵活性，可结合重载的方式设计可变参数方法，如方法大多数情况下至多接受两个参数，少数情况下接受两个以上的参数：
    ```
    public void foo() {

    }

    public void foo(int a1) {
      
    }

    public void foo(int a1, int a2) {
      
    }

    public void foo(int a1, int a2, int ...args) {
      
    }
    ```

> 返回空的数组或集合，不要返回 null

> 明智审慎地返回 Optional

> 为所有已公开的 API 元素编写文档注释