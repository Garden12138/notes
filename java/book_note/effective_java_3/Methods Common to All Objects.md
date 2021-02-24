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
            return oec.field == field;
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

> 重写equals方法同时重写hashCode方法时遵守通用约定
  * 在每个类中重写```equals```方法同时需要重写```hashCode```方法，否则违反了```hashCode```的通用约定，阻止了在```HashMap```和```HashSet```这样的集合正常工作，通用约定如下：
    * 若未修改```equals```方法用以比较的信息，在应用程序的一次执行过程中对一个对象重复调用```hashCode```方法，必须始终保持返回相同的值；在应用程序的多次执行过程中，每个执行过程在该对象获取的结果值可以不同。
    * 若两个对象根据```equals```方法比较是相等的，那么两个对象调用```hashCode```方法获取结果值是相同的。
    * 若两个对象根据```equals```方法比较是不相等的，那么两个对象调用```hashCode```方法获取结果值可以是不同的（建议保持不同，不相等对象生成不同的结果可提高散列表的性能）。
  * 重写```hashCode```方法步骤
    * 声明一个```int```类型的变量```result```，并将其初始化为对象中第一个重要属性```c```（重要属性为重写equals方法中比较的属性）的哈希码。
    * 对于对象中剩余的重要属性```f```：
      * 判断属性```f```类型，若为基本类型，使用```Type.hashCode(f)```方法计算（```Type```为属性```f```的包装类）；若为对象引用，并且该类的```equals```方法通过递归调用```equals```来比较属性，递归调用```hashCode```方法，如果需要更复杂的比较，则计算此字段的范式，并在范式上调用```hashCode```，如果该字段的值为空，则使用0（通常使用0表示）；若为数组，将它看作每个重要元素都是一个独立属性，递归计算每个重要元素的哈希码，如果数组没有重要元素，则使用一个常量表示（通常不用0表示），如果所有元素都重要，则使用```Arrays.hashCode方法```。
      * 将当前计算结果与上述哈希计算结果合并，```result = 31 * result + hashCode(f)```
    * 返回```result```
    ```
    @Override
    public int hashCode() {
      int result = Short.hashCode(areaCode);
      result = 31 * result + Short.hashCode(prefix);
      result = 31 * result + Short.hashCode(lineNum);
      return result;
      // 性能不重要的情况可以使用以下
      // return Objects.hash(lineNum,prefix,areaCode);
    }
    ```
  * 注意事项
    * 对于一个不可变类，重复计算哈希码代价很大，可考虑在对象中缓存哈希码。
      ```
      // 初始化值默认为0
      private int hashCode;
      @Override
      public int hashCode() {
        int result = hashCode;
        if (0 ==  result) {
          result = Short.hashCode(areaCode);
          result = 31 * result + Short.hashCode(prefix);
          result = 31 * result + Short.hashCode(lineNum);
          hashCode = result;
        }
        return result;
      }
      ```
    * 不要试图从哈希码计算中排除重要的属性来提高性能。
    * 不要为```hashCode```返回的值提供详细规范，以便可以灵活改变哈希函数提供性能。

> 始终重写 toString 方法
  * Object类提供了```toString```方法的实现，返回的字符串由类名跟符号和哈希码的无符号十六位进制表示组成（如 ```DemoClass@163b91```），返回内容对于用户不友好，因此```toString```通用约定建议所有子类重写这个方法。重写这个方法推荐输出该类所有属性信息。
    ```
    public class BookCase {
      private String name;
      private List<String> books;
      @Override
      public String toString() {
        return "BookCase{" + "name='" + name + '\'' +", books=" + books +'}';
      }
    }
    ```

> 谨慎地重写 clone 方法
  * ```clone```方法机制存在缺陷，需在合理的范围内使用。实现克隆的一个方式是类实现```Cloneable```接口，重写```Object```类的```clone```方法，将返回该对象的逐个属性拷贝，该接口不包含任何方法，但决定了```Object```的受保护```clone```方法实现的行为，遵循了一个复杂不可执行的文档协议，由此产生的机制是危险和不受语言影响的。
  * ```clone```方法机制存在薄弱的通用约定
    * 创建并返回此对象的副本，对于任何对象```x```，表达式```x.clone().getClass() == x.getClass()```为```true```，表达式```x.clone() != x```为```true```，表达式```x.clone().equals.(x)```为```true```，但它们不是绝对要求。
    * 根据约定，这个方法返回的对象应该通过调用```super.clone()```方法获得。如果一个类和它所有的父类（```Object```类除外）都遵守这个约定，那么```x.clone().getClass() == x.getClass()```一定为```true```。
    * 根据约定，返回的对象应该独立于被克隆对象。为实现这种独立性，可能需修改由```super.clone()```返回的对象的一个或多个属性。
  * 谨慎重写```clone```方法
    * 对象每个属性包含原始值或不可变对象引用
      ```
      public class ChildrenClass implements Cloneable {
        private int field1;
        private String field2;
        @Override
        public ChildrenClass clone() {
          try {
            return (ChildrenClass)super.clone();
          } catch(CloneNotSupportedException e) {
            throw new AssertionError();
          }
        }
      }
      ```
    * 对象包含可变对象引用
      ```
      public class ChildrenClass implements Cloneable {
        private int field1;
        private String field2;
        private Object[] field3;
        private int size;
        private void ensureCapacity() {
          if (field3.length == size) {
            field3.length = Arrays.copyOf(field3, 2 * size + 1);
          }
        }
        @Override
        public ChildrenClass clone() {
          try {
            ChildrenClass res = (ChildrenClass)super.clone();
            res.field3 = field3.clone();
            return res;
          } catch(CloneNotSupportedException e) {
            throw new AssertionError();
          }
        }
      }
      ```
    * 对象包含深度可变对象引用
      ```
      public class HashTable implements Cloneable { 
        private Entry[] buckets = ...; 
        private static class Entry {
          final Object key; 
          Object value; 
          Entry next; 
          Entry(Object key, Object value, Entry next) { 
            this.key = key; 
            this.value = value; 
            this.next = next; 
          }
          Entry deepCopy() { 
            Entry result = new Entry(key, value, next);
            for (Entry p = result; p.next != null; p = p.next) 
                p.next = new Entry(p.next.key, p.next.value, p.next.next); 
            return result; 
          }
        }
        
        @Override 
        public HashTable clone() { 
          try {
            HashTable result = (HashTable) super.clone(); 
            result.buckets = new Entry[buckets.length];
          for (int i = 0; i < buckets.length; i++) 
              if (buckets[i] != null) 
                  result.buckets[i] = buckets[i].deepCopy(); 
          return result; 
          } catch (CloneNotSupportedException e) { 
            throw new AssertionError(); 
          } 
        }
      }
      ```
  * 使用更良好的复制方式代替重写```clone```方法
    * 复制构造方法
      ```
      public ChildrenClass(ChildrenClass childrenClass) {
        ...
      }
      ```
    * 复制静态工厂方法
      ```
      public static ChildrenClass newInstance(ChildrenClass childrenClass) {
        ...
      }
      ```

> 考虑实现Comparable接口