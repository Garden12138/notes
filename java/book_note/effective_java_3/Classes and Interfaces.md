## EffectiveJava3

#### 类与接口

> 使类和成员的可访问性最小化
  * 设计良好的组件隐藏所有内部实现细节，将它的API与它的实现分离开，其他组件通过API进行通信。这种信息隐藏与封装的方式是软件设计的基本原则。
  * 信息隐藏与封装的重要原因
    * 解耦，将组成系统的组件分离出来，允许它们被独立地开发，测试，使用以及优化，加速系统并行开发，减轻维护负担，可以更快速调试或更换组件。
    * 重用，增加软件重用，松耦合的组件可在其他环境中使用。
    * 健壮，降低了构建大型系统的风险，即使系统不能运行，各个独立的组件也是可以的。
  * 使用访问控制机制进行信息隐藏，访问控制机制指定了类，接口和成员的可访问性，实体的可访问性取决于其声明的位置以及使用的访问修饰符。对于成员（字段、方法、嵌套类和嵌套接口），按照可访问性从小到大：
    * ```private``` -- 该成员只能在声明它的顶级类内访问。
    * ```package-private``` -- 该成员可以在声明它的包中的任何类访问。如果没有指定修饰符，这是默认访问级别（接口成员除外，它默认是公共的）。
    * ```protected``` -- 该成员可以在声明它的包中的任何类访问以及声明它的类的子类中访问。
    * ```public``` -- 该成员可以从任何地方被访问。
  * 使类和成员的可访问性最小化实践
    * 公共类的实例字段很少情况下使用```public```修饰，带有公共可变实例字段的类通常是线程不安全的。
      ```
      public String field; 

      |
      V

      private String field;
      ```
    * 公共类的静态字段经常结合```final```用于暴露常量，这种情况下使用```public```修饰。
      ```
      public static final String CONSTANT_YES = "1";
      public static final String CONSTANT_NO = "0";
      ```
    * 公共类的公共静态```final```数组（非零长度）字段总是可变的，客户端能够修改数组内容，会造成安全问题。
      ```
      public static final Thing[] VALUES = {...};

      |
      V
      
      private static final Thing[] PRIVATE_VALUES = {...};
      public static final List<Thing> VALUES = Colletions.unmodifiableList(Arrays.asList(PRIVATE_VALUES));

      //或

      private static final Thing[] PRIVATE_VALUES = {...};
      public static final Thing[] values() {
          return PRIVATE_VALUES.clone();
      }
      ```

> 在公共类中使用访问方法而不是公共属性
  * 如果一个类在其包外是可访问的且可变属性，则提供方法保留更改类内部表示的灵活性而不是直接暴露。
    ```
    public class Point {
        public double x;
        public double y;
    }

    |
    V

    public class Point {
        private double x;
        private double y;

        public Point(double x, double y) {
            this.x = x;
            this.y = y;
        }

        public double getX() {
            return x;
        }
        public double getY() {
            return y;
        }

        public void setX(double x) {
            this.x = x;
        }
        public void setY(double y) {
            this.y = y;
        }
    }
    ```
  * 如果一个类在其包外是可访问的且不可变属性，可暴露属性，虽然存在问题，但其危害较小。
    ```
    public final class Point {
        public final double x;
        public final double y;
    }
    ```
  * 如果一个类是包级私有或者是一个私有的内部类，可暴露属性，虽然客户端代码可绑定到类的内部表示，但是这些代码仅限于包含该类的包或者在该类内部。

> 最小化可变性

> 组合优于继承

> 要么设计继承并提供文档说明，要么禁用继承

> 接口优于抽象类

> 为后代设计接口

> 接口仅用来定义类型

> 类层次结构优于标签类

> 支持使用静态成员类而不是非静态类

> 将源文件限制为单个顶级类