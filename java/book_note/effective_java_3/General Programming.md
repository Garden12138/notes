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

> 若需要精确答案就应避免使用 float 和 double 类型

> 基本数据类型优于包装类

> 当使用其他类型更合适时应避免使用字符串

> 当心字符串连接引起的性能问题

> 通过接口引用对象

> 接口优于反射

> 明智审慎地本地方法

> 明智审慎地进行优化

> 遵守被广泛认可的命名约定