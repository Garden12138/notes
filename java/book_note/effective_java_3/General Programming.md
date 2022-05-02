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