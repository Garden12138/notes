## EffectiveJava3

#### 通用规范

> 最小化局部变量的作用域
  * 最小化局部变量的作用域，可提高代码的可读性和可维护性，并降低出错的可能性。最小化局部变量的作用域的方式：
    * 首次使用的地方声明变量。过早地声明局部变量可能导致其作用域过大，局部变量的作用域从声明它的位置延伸至封闭块的末尾。若变量在使用它的封闭块之外声明，则程序在退出该封闭时它仍然可见，若在其预定用途区域之前或之后意外使用变量，可能导致灾难性后果。
    * 几乎每个局部变量声明都应该包含一个初始化器。若没有足够信息来合理初始化一个变量，则应该延迟声明，此时需要初始化器初始化。如```try-catch```语句，若一个变量被初始化为一个表达式，该表达式的计算结果可能抛出一个已检查的异常，故该变量应该初始化在```try```块中，但该变量又应用于```try```块外，故该变量还需要在```try```块前使用初始化器初始化。
    * 循环可支持最小化变量的作用域。传统```for```循环与```for-each```形式都允许声明循环变量，将其作用域限制在它们确切的区域内。故循环优先选择```for```（```for-each```）而不是```while```循环。如：
      ```
      Iterator<Element> i = c.iterator(); 
      while (i.hasNext()) { 
          doSomething(i.next()); 
      }
      
      // ...

      Iterator<Element> i2 = c2.iterator(); 
      while (i.hasNext()) { // 使用上文局部变量i，编译、运行不报错，但不是预期结果
          doSomethingElse(i2.next()); 
      }
      ```
      ```
      for (Iterator<Element> i = c.iterator(); i.hasNext(); ) { 
          Element e = i.next(); 
          ... // Do something with e and i 
      }
      
      //... 
      
      // Compile-time error - cannot find symbol i
      for (Iterator<Element> i2 = c2.iterator(); i.hasNext(); ) { 
          Element e2 = i2.next(); 
          ... // Do something with e2 and i2 
      }
      ```

> for-each 循环优于传统 for 循环
  * 传统```for```循环常应用于集合的迭代遍历或数组索引变量遍历，但这种方式容易使迭代器或索引变量混乱，进而可能使用到错误的变量：
    ```
    // Not the best way to iterate over a collection!
    for (Iterator<Element> i = c.iterator(); i.hasNext(); ) { 
        Element e = i.next(); 
        ... // Do something with e 
    }
    ```
    ```
    // Not the best way to iterate over an array!
    for (int i = 0; i < a.length; i++) { 
        ... // Do something with a[i] 
    }
    ```
  * ```for-each```循环通过隐藏迭代器或索引变量消除混乱和可能错误的机会。此用法仍然适用于集合和数组：
    ```
    // The preferred idiom for iterating over collections and arrays
    for (Element e : elements) { 
        ... // Do something with e 
    }
    ```
    使用```for-each```循环不会降低性能，生成的代码本质上是相同的。当涉及嵌套迭代时，```for-each```比传统```for```循环优势大：
    ```
    enum Suit { CLUB, DIAMOND, HEART, SPADE } 
    enum Rank { ACE, DEUCE, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING } 
    
    static Collection<Suit> suits = Arrays.asList(Suit.values()); 
    static Collection<Rank> ranks = Arrays.asList(Rank.values());

    // 传统for循环嵌套
    List<Card> deck = new ArrayList<>();
    for (Iterator<Suit> i = suits.iterator(); i.hasNext(); )
        for (Iterator<Rank> j = ranks.iterator(); j.hasNext(); ) 
            deck.add(new Card(i.next(), j.next())); // 外部第一次循环中suit被用完时报NoSuchElementException异常

    // for-each循环
    for (Suit suit : suits)
        for (Rank rank : ranks) 
            deck.add(new Card(suit, rank));
    ```
    但有三种情况不能使用```for-each```循环：
    * 有损过滤。若需要遍历集合时，删除指定元素，则需使用显式迭代器，以便可调用其```remove```方法。通常可使用```Java8```添加的```Collection```类中的```removIf```方法，避免显式遍历。
    * 转换。若需要遍历集合或数组时，替换其部分或全部值时，则需利用集合迭代器或数组索引来替换元素的值。
    * 并行迭代。若需要并行地遍历多个集合，则使用显式控制的迭代器或索引变量。
  * ```for-each```不仅适用于遍历集合和数组，还允许遍历实现```Iterable```接口的任何对象：
    ```
    public interface Iterable<E> { 
        // Returns an iterator over the elements in this iterable Iterator<E> iterator(); 
    }
    ```

> 了解并使用库
  * 设计一个生成0到某个上界之间的随机整数的方法，通常：
    ```
    static Random rnd = new Random();

    static int random(int n) {
        retunr Math.abs(rnd.nextInt()) % n;
    }
    ```
    该方法存在三个问题：
    * 若```n```是小的平方数，随机数序列会在短时间内重复。
    * 若```n```不是2的幂数，一些数字会比其他数据更频繁地返回，如果```n```很大，效果更明显。
    * 极少数情况下会返回超出指定范围的数字，这将导致灾难性后果。

    通过使用标准库，解决上述问题。```Java7```之后常用的随机数生成器有```ThreadLocalRandom```，该生成器可产生更高质量的随机数且速度快。对于```fork```连接池和并行流，使用```SplittableRandom```。
  * 使用标准库的好处：
    * 不必花费时间为与工作内容无关的问题编写专门的解决方案。
    * 随着在行业标准中不断使用，库组织会持续不断地提高标准库的使用性能。
    * 随着新版本的发布，往往会获得新特性。
    * 将代码放在主干中，代码更容易被开发人员阅读、维护和重用。
  * 了解并使用常用类库：
    * ```java.lang```
    * ```java.util```，包括```java.util.concurrent```，该包包含高级的用来简化多线程编程任务的工具。
    * ```java.io```
    * ```Collections```框架
    * ```Streams```库
  * 若基本类库无法满足需求时，可以选择高质量第三方库，如谷歌开源的```Guava```库。如果无法在任何适当的库中找到支持所需的功能时，只能自身独立去实现。

> 若需要精确答案就应避免使用 float 和 double 类型
  * ```float```和```double```主要用于工程计算和科学计算，执行二进制浮点运算，能够在很大范围内快速提供精确的近似值，但不能提供准确的结果，也不应该在需要精确结果地方使用。```float```和```double```类型不适合进行货币计算。使用```float```或```double```进行货币计算会造成精度丢失问题，如假设口袋有一美元，零食店里有一个架子上有一排糖果，它们的价格从10美分、20美分依次递增直至1美元，现在我们从10美分的糖开始买起，直至剩余钱不足买下一颗糖，此时计算得出已买糖果数量以及剩余零钱：
    ```
    // 使用double计算
    public static void main(String[] args) { 
        double funds = 1.00; 
        int itemsBought = 0;
        for (double price = 0.10; funds >= price; price += 0.10) {
            funds -= price; 
            itemsBought++; 
        }
        System.out.println(itemsBought +"items bought."); // 3
        System.out.println("Change: $" + funds);   // 0.399999999999999999
    }
    ```
    ```
    // 使用Bigdecimal计算
    public static void main(String[] args) {
        final BigDecimal TEN_CENTS = new BigDecimal(".10"); 
        int itemsBought = 0; 
        BigDecimal funds = new BigDecimal("1.00");
        for (BigDecimal price = TEN_CENTS; funds.compareTo(price) >= 0; price = price.add(TEN_CENTS)) {
            funds = funds.subtract(price); 
            itemsBought++; 
        }
        System.out.println(itemsBought +"items bought.");  // 4
        System.out.println("Money left over: $" + funds);  // 0
    }
    ```
    ```
    // 使用int类型计算，将整型换算成最小单位后再进行计算
    public static void main(String[] args) { 
        int itemsBought = 0; 
        int funds = 100; // 1美元换算100美分
        for (int price = 10; funds >= price; price += 10) {
            funds -= price; 
            itemsBought++; 
        }
        System.out.println(itemsBought +"items bought."); // 4
        System.out.println("Cash left over: " + funds + " cents"); // 0
    }
    ```
  * 对于需要精确答案的计算，不考虑性能成本和方便性的情况下使用```Bigdecimal```类型。若性能成本重要，进行十进制小数点的处理后，数值不超过9位时使用```int```类型，数值不超过18位时使用```long```类型。不考虑使用```float```和```double```类型。

> 基本数据类型优于包装类
  * ```Java```类型系统由基本类型（如```int```）和引用类型（```String```）组成。每个基本类型都有一个对应的引用类型，称为包装类型，如基本类型```int```对应包装类型```Integer```。
  * 基本类型与包装类型的区别：
    * 基本类型只有值，包装类型不仅包含值且具有代表对象实例的标识，即两个包装类型实例可以具有相同的值和不同的标识。
    * 基本类型不能为```null```，包装类型可以为```null```。
    * 基本类型比包装类型更节省时间和空间。
  * 优先使用基本类型，谨慎使用包装类型：
    * 将```==```操作符应用于包装类型是错误的。此操作结果为实例标识比较的结果。
    * 在操作中混合使用基本类型和包装类型时，包装类型会自动拆箱。若一个空对象引用自动拆箱，将报```NullPointerException```。若操作运算多次，将会进行多次自动拆箱和自动装箱，容易导致性能问题。
    * 在参数化类型和方法中，必须使用包装类型作为类型参数，如```ThreadLocal<Intger>```。

> 当使用其他类型更合适时应避免使用字符串
  * 字符串被设计用来表示文本，以下是不适合使用字符串的场景：
    * 当数据是其他值类型时，不应该使用字符串，应该使用对应值类型。若是数值类型，则使用```int```、```double```或```float```等；若是是或否的形式则使用枚举类型或布尔值。
    * 当枚举常量时，不应该使用字符串，应该使用枚举类型。
    * 聚合类型不应该使用字符串代替。若一个实体有多个组件，将其表示为单个字符串容易导致混乱，甚至出错。
    * 字符串不能很好的代替```capabilities```。字符串常用于授予某些功能的访问权，如线程本地变量的机制，该机制提供每个线程拥有自己的独立变量。```Java1.2```后的库提供了线程本地变量机制，在这之前，出现由客户端提供字符串键用于标识每个线程本地变量的设计：
      ```
      // Broken - inappropriate use of string as capability! 
      public class ThreadLocal { 
          private ThreadLocal() { } // Noninstantiable 
          
          // Sets the current thread's value for the named variable.
          public static void set(String key, Object value); 
          
          // Returns the current thread's value for the named variable. public static Object get(String key); 
      }
      ```
      该设计的问题在于字符串键表示线程本地变量的共享全局名称空间。为了使该设计能够正常使用，客户端提供的字符串键必须是唯一的，否则两个客户端将会共享一个变量，导致两个端都失败。该设计安全性差，恶意客户端可故意使用与另一个客户端相同的字符串密钥来非法访问另一个客户端的数据。这个设计可通过用一个不可伪造的键（```capability```）替换字符串来修复：
      ```
      public class ThreadLocal { 
          
          private ThreadLocal() { } // Noninstantiable
          
          public static class Key {  // (Capability) 
              Key() { } 
          }
          
          // Generates a unique, unforgeable key 
          public static Key getKey() { 
              return new Key(); 
          }
          
          public static void set(Key key, Object value);
          public static Object get(Key key); 
      }
      ```
  * 当存在或可编写更好的数据类型是，应避免将字符串用来表示对象。如果使用不当，字符串比其他类型更麻烦、灵活性更差、速度更慢、更容易出错。

> 当心字符串连接引起的性能问题
  * 字符串连接操作符```+```是将若干个字符串组合成一个字符串的简便方法，一般用于单行输出或构造一个小的、固定大小的字符串对象表示形式。使用字符串串联运算符重复串联```n```个字符串需要```n```的平方级时间，这是由于字符串不可变事实导致的结果，故当```n```很大时将导致严重的性能问题。
  * 不使用字符串连接操作符合并多个字符串，除非性能无关紧要。否则使用```StringBuilder```、```StringBuffer```或使用字符数组的方式替代。

> 通过接口引用对象
  * 如果存在合适的接口类型，应该使用接口类型声明参数、返回值、变量和字段。使用构建函数构建对象时才引用对象的类，如：
    ```
    Set<Son> sonSet = new LinkedHashSet<>();
    ```
    而不是：
    ```
    LinkedHashSet<Son> sonSet = new LinkedHashSet<>();
    ```
    使用接口类型声明，程序将更加灵活。若需要更换实现类，只需在构造函数中更改类名（或使用不同的静态工厂），如：
    ```
    Set<Son> sonSet = new HashSet<>();
    ```
  * 如果没有合适的接口类型，使用类引用对象是完全合适的：
    * 声明值变量使用值类，如```String```、```BigInteger```等。值类很少在编写时考虑多个实现，通常是```final```，很少有相应的接口。
    * 声明框架的对象，框架的基本类型是类而不是接口，如果一个对象属于一个基于类的框架，则使用基类来声明它，一般基类是抽象的，如```java.io```中的```OutputStream```。
    * 实现接口但同时提供接口不存在额外方法的类，如```PriorityQueue```有一个在```Queue```接口中不存在的比较器方法。

> 接口优于反射
  * 核心放射机制```java.lang.reflect```提供对任意类的访问。给定一个```Class```对象，可获得```Constructor```、```Method```和```Field```实例，分别代表该```Class```实例所表示的类的构造器、方法和字段，这些实例提供对类的成员名、字段类型、方法签名等访问，通过调用这些实例的方法，可以构造底层类的实例且调用底层类的方法并访问底层类中的字段，如```Method.invoke```允许在任何类的任何对象上调用任何方法（受默认的安全约束）。
  * 反射允许一个类使用另一个类，即使在编译前者时后者不存在，但存在缺点：
    * 失去编译时的类型检查。若程序试图通过反射调用一个不存在或不可访问的方法时将在运行时失败，除非采取特殊的预防措施。
    * 执行反射访问所需的代码冗长。
    * 性能降低。
  * 通过非常有限的形式使用反射，可以从反射中受益。对于许多程序，它们必须用到在编译时无法获取的类，在编译时存在一个合适的接口或超类来引用该类，可以用反射的方式创建实例，并通过它们的接口或超类正常访问它们，如设计一个创建```Set<String>```实例的程序，类由第一个命令行参数指定，剩余的命令行参数插入到集合并打印出来：
    ```
    // Reflective instantiation with interface access 
    public static void main(String[] args) {
        // Translate the class name into a Class object 
        Class<? extends Set<String>> cl = null; 
        try {
            cl = (Class<? extends Set<String>>) // Unchecked cast! 
            Class.forName(args[0]); 
        } catch (ClassNotFoundException e) {
            fatalError("Class not found."); 
        }
        
        // Get the constructor 
        Constructor<? extends Set<String>> cons = null; 
        try {
            cons = cl.getDeclaredConstructor(); 
        } catch (NoSuchMethodException e) {
            fatalError("No parameterless constructor"); 
        }
        
        // Instantiate the set 
        Set<String> s = null; 
        try {
            s = cons.newInstance(); 
        } catch (IllegalAccessException e) {
            fatalError("Constructor not accessible"); 
        } catch (InstantiationException e) {
            fatalError("Class not instantiable."); 
        } catch (InvocationTargetException e) {
            fatalError("Constructor threw " + e.getCause()); 
        } catch (ClassCastException e) {
            fatalError("Class doesn't implement Set"); 
        }
        
        // Exercise the set 
        s.addAll(Arrays.asList(args).subList(1, args.length)); 
        System.out.println(s); 
    }
    
    private static void fatalError(String msg) { 
        System.err.println(msg); 
        System.exit(1); 
    }
    ```
  * 反射是一种功能强大的工具，对于某些复杂的系统编程任务（代码分析工具、依赖注入框架等）是必需的。若编写的程序必须在编译时处理未知的类，则应尽可能使用反射实例化对象，并使用在编译时已知的接口或超类访问对象。

> 明智审慎地本地方法
  * ```Java```本地接口（```JNI```）允许```Java```应用程序调用本地方法（用```C```或```C++```等本地编程语言编写）。本地方法的用途：
    * 提供对特定平台设施（如注册中心）的访问。使用本地方法访问特定平台的机制是合法的，随着```Java```平台的成熟，它提供了对许多以前只能在宿主平台的特性，例如```Java9```中添加的流```API```提供了对```OS```流程的访问。
    * 提供对现有本地代码库的访问，包括提供对遗留数据访问。在```Java```中没有等效库时，使用本地方法来使用本地库时合法的。
    * 本地方法可通过本地语言编写应用程序中注重性能的部分，以提供性能。
  * 为了提供应用程序的性能，谨慎使用本地方法。随着```JVM```地不断优化，对于大多数任务，都已经在```Java```中获得性能的提升，如在```Java1.1```版本中添加了```java.math```，```BigInteger```是在一个用```C```编写的快速多精度运算库的基础上实现的，但在```Java1.3```中，```BigInteger```则完全用```Java```重写且性能进行了调优，速度比之前快。若```Java```应用程序真正需要高性能多精度算法，可以通过调用本地方法使用```GMP```。使用本地方法存在严重的缺点：
    * 本地语言不安全，使用本地方法的应用程序可能会受到内存毁坏错误的影响。
    * 本地语言更加依赖平台，因此使用本地方法的应用程序可移植性较差。
    * 本地方法可能会降低性能，因为垃圾收集器无法自动跟踪本地内存使用情况且进出本地代码会产生相关的成本。
    * 本地方法可阅读性差，编写难度大。

> 明智审慎地进行优化
  * 不为性能牺牲合理的架构。在可能的情况下，在架构的单个组件中本地化设计决策，可以在不影响系统其余部分的情况下更改单个决策。但这不意味着在程序完成之前可以忽略性能问题，对于架构缺陷，若不重写系统，就不可能解决限制性能的问题。在系统完成之后再改变设计的某个基本方面可能导致结构不良的系统难以维护，因此必须在设计过程中考虑性能。
  * 尽量避免限制性能的设计决策。设计中难以更改的组件是指定组件之间以及与外部交互的组件，这些组件中最主要的是```API```、线路层协议和持久数据格式，它们不仅难以或不可能在事后更改，而且所有这些组件都可能对系统能够达到的性能造成重大限制。
  * 不为获得良好的性能而改变```API```。
  * 利用分析工具找到性能问题的根源，并对系统的相关部分进行优化，优先检查算法的选择，其次再进行底层优化，在每次优化更改后需要测试性能，以达到调优的目的。

> 遵守被广泛认可的命名约定
  * ```Java```平台有一组完善的命名约定，其中许多约定包含在```《The Java Language Specification》``` ```[JLS]```。命名约定分为：排版和语法。
  * 排版约定：
    * 包名和模块名，是分层的，组件之间用句号分割。组件应该由小写字母组成。任何在组织外部使用的包，名称都以组织的```Internet```域名开头，并将组件颠倒，如```com.google```。以```java```和```javax```开头的标准库和可选包是这个规则的例外，用户不能创建名称以```java```或```javax```开头的包或模块。包名的其余部分应该由描述包的一个或多个组件组成，组件名称通常为8个或更少的字符，建议使用有意义的缩写，如```util```。许多包的名称只有一个组件，该类组件适用于大型工具包，这些工具包的大小要求将其分解为非正式的层次结构，如```java.util.concurrent.atomic```。
    * 类和接口名称，包括枚举类型和注解类型，由一个或多个单词组成，每个单词的首字母大写，如```List```或```FutureTask```。缩略语应该避免使用，若使用可选择全部大写或只有首字母大写的方式，如：```HTTPURL```或```HttpUrl```。
    * 方法和字段名称，遵循与类和接口相同的排版约定，但方法或字段名的首字母应该是小写，如```remove```。静态常量字段是例外，它的名称由一个或多个大写单词组成，由下划线分割，如```NEGATIVE_INFINITY```。
    * 局部变量名称，遵循与成员名称相同的排版约定，但允许使用缩写，即允许使用单个字符或短字符序列，它们的含义取决它们出现的上下文，如```i```、```phoneNum```。输入参数是一种特殊的局部变量，由于它们是方法文档的组成部分，故命名需要更加谨慎。
    * 类型参数名称，通常由单个大写字母组成。最常见的类型：```T```表示任意类型、```E```表示集合的元素类型、```K```和```V```表示```Map```的键和值的类型、```X```表示异常、```R```表示函数返回类型、任意类型的序列可以是```T、U、V```或```T1、T2、T3```。
  * 语法约定：
    * 包没有语法命名约定。
    * 可实例化的类，包括枚举类型，通常使用一个或多个名词短语命名，如```Thread```、```PriorityQueue```。不可实例化的类，通常使用复数名词命名，如```Collections```。接口的名称类似于类，集合或比较器，或者以```able```或```ible```结尾的形容词，如```Runnable```、```Accessible```。注解类型用途比较多，名词、动词、介词和形容词都比较常见，如```Inject```、```BindingAnnotation```。
    * 执行操作的方法通常用动词或动词短语命名，如```append```。返回布尔值的方法名词通常以单词```is```或```has```开头，后面紧接名词、名词短语或用作形容词的单词短语，如```isDigit```。返回被调用对象的非布尔函数或属性的方法通常使用以```get```开头的名词、名词短语或动词短语。转换对象类型的实例方法通常使用```toType```约定，如```toString```。返回与接收对象类型不同的视图的实例方法通常使用```asType```约定，如```asList```。返回与调用它们的对象具有相同值的基本类型的方法通常称为类型值，如```intValue```。静态工厂方法的常见名称包括```from```、```of```、```valueOf```、```instance```、```getInstance```、```newInstance```、```getType```和```newType```。
    * 字段名通常使用名称或名称短语命名。
    * 局部变量的语法约定类似字段名的语法约定。