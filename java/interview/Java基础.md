#### Java基础

> 面向对象
  * 三大特性
    * 封装。利用抽象数据类型将数据和基于数据的操作封装在一起，使其构成一个不可分割的独立实体。数据被保护在抽象数据类型内部（私有成员变量），隐藏内部实现细节，对外只提供访问方法：
      ```
      public class Person {
          
          private String name;
          private int gender;
          private int age;
          
          public String getName() {
              return name;
          }
          
          public String getGender() {
              return gender == 0 ? "man" : "woman";
          }
          
          public void work() {
              if (18 <= age && age <= 50) {
                  System.out.println(name + " is working very hard!");
          } else {
              System.out.println(name + " can't work any more!");
            }
          }
      }
      ```
      优点：
        * 减少耦合，可以独立开发、测试、优化、修改以及使用
        * 减轻维护负担，可以更容易被开发者理解，在调试时可以不影响其他模块
        * 有效调节性能
        * 提供软件的重用性
        * 降低构建大型系统的风险，即使整个系统不可用，独立的模块却可能是有用
    * 继承。继承实现了```IS-A```关系，如```Cat```和```Animal```是一种```IS-A```关系，故```Cat```继承了```Animal```，从而获得了```Animal```的非```private```属性。继承应该遵循里斯替换原则，子类对象必须能给替换掉所有的父类对象，如可以使用```Animal```引用```Cat```对象，这种父类引用指向子类对象的方式称为向上转型。
      ```
      Animal animal = new Cat();
      ```
    * 多态。多态分为编译时多态和运行时多态。编译时主要指方法的重载；运行时多态指定义的对象引用所指向的具体类型在运行时才确定，实现运行时多态需要同时满足继承、重写和向上转型：
      ```
      public class Instrument {
          public void play() {
              System.out.println("Instrument is playing...");
          }
      }
      
      public class Wind extends Instrument {
          public void play() {
              System.out.println("Wind is playing...");
          }
      }
      
      public class Percussion extends Instrument {
          public void play() {
              System.out.println("Percussion is playing...");
          }
      }
      
      public class Music {
          public static void main(String[] args) {
              List<Instrument> instruments = new ArrayList<>();
              instruments.add(new Wind());
              instruments.add(new Percussion());
              for(Instrument instrument : instruments) {
                  instrument.play();
              }
          }
      }
      ```
  * 类图
    * 泛化关系。用来描述继承关系，在```Java```中使用```extends```关键字。
      ```
      @startuml
      
      title Generalization

      class Vehical
      class Car
      class Truck

      Vehical <|-- Car
      Vehical <|-- Truck

      @enduml
      ```
    * 实现关系。用来描述实现接口，在```Java```中使用```implements```关键字。
      ```
      @startuml
      
      title Realization
      
      interface MoveBehavior
      class Fly
      class Run
      
      MoveBehavior <|.. Fly
      MoveBehavior <|.. Run
      
      @enduml
      ```
    * 聚合关系。用来描述整体与部分的关系，整体和部分不是强依赖，整体不存在，部分仍存在。如电脑由主机、鼠标以及键盘等聚合而成。
      ```
      @startuml
      
      title Aggregation
      
      class Computer
      class Keyboard
      class Mouse
      class Screen
      
      Computer o-- Keyboard
      Computer o-- Mouse
      Computer o-- Screen
      
      @enduml
      ```
    * 组合关系。用来描述整体与部分的关系，整体和部分是强依赖，整体不存在，部分则不存在。如公司由多个部门组成，公司不存在则部门不存在。
      ```
      @startuml
      
      title Composition
      
      class Company
      class DepartmentA
      class DepartmentB
      
      Company *-- DepartmentA
      Company *-- DepartmentB
      
      @enduml
      ```
    * 关联关系。用来描述不同类对象之间的静态关系，与运行过程的状态无关。如一个班级有多个学生的1对```n```关系。
      ```
      @startuml
      
      title Association
      
      class School
      class Student
      
      School "1" - "n" Student
      
      @enduml
      ```
    * 依赖关系。用来描述不同类对象之间在运行过程的作用关系。如```A```类和```B```类是依赖关系的主要三种形式：
      * ```A```类是```B```类方法中的一个参数。
      * ```A```类是```B```类某方法的局部变量。
      * ```A```类像```B```类发送消息，从而影响```B```类发生变化。
      ```
      @startuml
      
      title Dependency
      
      class Vehicle {
          move(MoveBehavior)
      }

      interface MoveBehavior {
          move()
      }

      note "MoveBehavior.move()" as N

      Vehicle ..> MoveBehavior

      Vehicle .. N

      @enduml
      ```

> 语言基础
  * 数据类型
    * 包装类型。对应的八个基本类型：
      ```
      boolean/1b
      byte/8b
      char/16b
      short/16b
      int/32b
      float/32b
      long/64b
      double/64b
      ```
      包装类型与基本类型之间的赋值使用自动装箱与自动拆箱完成:
      ```
      Integer x = 2; //装箱
      int y = x; //拆箱
      ```
    * 缓存池。```new Integer(123)```与```Integer.valueOf(123)```区别在于：
      * ```new Integer(123)```每次都会创建一个新对象。
      * ```Integer.valueOf(123)```会优先使用缓存池中的对象，多次调用会取得同一个对象的引用：
        ```
        public static Integer valueOf(int i) {
          if (i >= IntegerCache.low && i <= IntegerCache.high)
              return IntegerCache.cache[i + (-IntegerCache.low)];
          return new Integer(i);
        }
        ```
        在```Java8```中，Integer的缓存池大小默认为-128～127。```valueOf```方法会应用在缓存池范围进行自动装箱中，多个```Integer```实例引用相同的对象并且值相同：
        ```
        Integer m = 123;
        Integer n = 123;
        System.out.println(m == n); // true
        ```
        基本类型对应缓存池范围：
        ```
        boolean values true and false 
        all byte values 
        short values between -128 and 127 
        int values between -128 and 127 
        char in the range \u0000 to \u007F
        ```

> 泛型机制

> 注解机制

> 异常机制

> 反射机制

> SPI机制

> 图谱

> Q/A