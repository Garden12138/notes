## EffectiveJava3

#### 所有对象的公共方法

> 重写equals方法时遵守通用约定
  * Object是一个具体的，为继承而设计的类，其所有非final方法equals，hashCode，toString，clone等为被子类重写而设计，都有清晰的通用约定。任何类重写这些方法时都需遵守通用约定，否则将会阻止其他依赖于约定的类与此类一起正常工作。
  * 无需重写类的equals方法：
    * 每个类的实例都是固定唯一的，如Thread类。
    * 类无需提供一个逻辑相等的功能。
    * 父类已经重写equals方法，且父类行为完全适合于该子类，如大多数Set从AbstractSet继承了equals实现。
    * 类是私有的或包级私有的，可以确定它的equals方法永远不会被调用。
  * 需重写类的equals方法：
    * 类需提供一个逻辑相等的功能且父类没有重写过equals方法。如值类Integer或String，重写equals方法不仅能够发现它们在逻辑上是否相等，而且重写过equals的实例可作为Map的键（Key），或者Set里面的元素，但使用实例控制的值类不需要重写equals方法，枚举类型属于这个类别。
  * 重写equals方法遵守的通用约定
    * 自反性：对于任何非空引用x，x.equals(x)必须返回ture。
    * 对称性：对于任何非空引用x和y，如果且仅当y.equals(x)返回true时，x.equals(y)必须返回true。
    * 传递性；对于任何非空引用x、y和z，如果x.equals(y)返回true，y.equals(z)返回true，则x.equals(z)必须返回true。
    * 一致性：对于任何非空引用x和y，如果在equals比较中使用的信息没有修改，则x.equals(y)的多次调用必须始终返回true或返回false。
    * 非空性：对于任何非空引用x，x.equals(null)必须返回false。
  * 重写equals方法步骤
    * 使用 == 运算符检查参数是否为该对象的引用，如果是，返回true。
    * 使用 ```instanceof```运算符检查参数是否具有正确的类型，如果不是，则返回false，一般正确的类型是equals方法所在的那个类，如果类实现了一个接口，该接口可改进equals约定以允许实现接口的类进行比较。
    * 参数转换为正确的类型。
    * 检查参数属性是否与该对象对应属性相匹配，如果匹配，则返回true，否则返回false。对于非float或double的基本类型，使用 == 运算符进行比较；对于float或double的基本类型，使用Float.compare(float,float)方法和Double.compare(double,double)方法进行比较；对于对象引用属性，递归地调用equals方法；对于数组属性，将这些准则应用于每个元素或重载Arrays.equals方法
    ```
    public class OverrideEqualsClass {
        ...
        @Override
        public boolean equals(Object o) {
            if (o == this) {
                return true;
            }
            if (!(o instanceof OverrideEqualsClass)) {
                return false;
            }
            OverrideEqualsClass oec = (OverrideEqualsClass)o;
            return oec.field = field;
        }
        ...
    }
    ```
  * 注意事项
    * 当重写equals方法时，同时也要重写hashCode方法。
    * 重写equals的方法尽量简单。
    * 在equals方法声明中，不要将参数Object替换为其他类型。
    * 重写equals方法的类应该尽量遵循优先使用组合而不是继承的规则。
      ```
      public class ColorPoint { 
          // Point原先为ColorPoint父类
          private final Point point; 
          private final Color color; 
          public ColorPoint(int x, int y, Color color) { 
              point = new Point(x, y); 
              this.color = Objects.requireNonNull(color); 
          }
          @Override
          public boolean equals(Object o) { 
              if (!(o instanceof ColorPoint)) 
                  return false; 
                  ColorPoint cp = (ColorPoint) o; 
                  return cp.point.equals(point) && cp.color.equals(color); 
        }
      }
      ```

> 重写equals方法时同时重写hashcode方法

> 始终重写 toString 方法

> 谨慎地重写 clone 方法

> 考虑实现Comparable接口