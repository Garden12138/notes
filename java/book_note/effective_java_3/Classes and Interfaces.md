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
  * 设计不可变类是类最小化可变性的方式。不可变类是其实例不能被修改的类，每个实例的所有信息在对象的生命周期中是固定的。```Java```平台类库包含许多不可变类，包括```String```类、```Integer```等基本类型包装类以及```BigInteger```类和```BigDecimal```类。不可变类比可变类更易于设计、实现和使用，不易出错且安全。
  * 设计不可变类，遵循以下规则：
    * 所有字段设置为```private```。防止客户端获取字段引用的可变对象的访问权限并直接修改这些对象状态。
    * 所有字段设置为```final```。通过系统强制执行的方式，表明不可变。
    * 不提供修改对象状态的方法。
    * 确保这个类不能被继承。防止恶意子类假装对象的状态修改，从而破坏类的不可变行为，通常是通过```final```修饰符修饰类或私有构造方法提供公有静态工厂方法构造。
    * 确保对任何可变组件都是互斥访问。若不可变类有任何引用可变对象的字段，请确保不可变类的客户端无法获取这些对象引用，切勿将可变属性初始化为客户端提供对象引用，或从访问方法返回属性，在构造方法、访问方法和```readObject```方法进行防御性拷贝。
    ```
    // 遵循不可变类规则构造的复数类
    public final class Complex{
      private final double re;
      private final double im;

      public Complex(double re, double im) {
        this.re = re;
        this.im = im;
      }

      public double realPart() {
        return re;
      }
      public double imaginaryPart() {
        return im;
      }
      // 函数式方法，方法返回将操作数应用于函数的结果，结果将以新实例返回，该实例状态未改变
      public Complex plus(Complex c) {
        return new Complex(re + c.re, im + c.im);
      }
    }
    ```
  * 不可变类的优点
    * 不可变类对象始终保持创建时初始状态，状态永远不变，提供了原子失败机制。
    * 不可变类对象线程安全。线程之间不需要同步，多个线程访问时不会遭到破坏，故不可变对象可以被自由共享，比如常用的值可提供公共的静态```final```常量：
      ```
      public static fianl Complex ZERO = new Complex(0,0);
      public static fianl Complex ONE = new Complex(1,0);
      ```
    * 
    * 不可变类对象为其他对象提供了很好的构件，如```Map```的键和```Set```的元素。
  * 不可变类的缺点
    * 不可变类的主要缺点时对于每个不同的值都需要一个单独的对象，创建这些对象代价可能很高，比如大型对象的场景下，改变百万位的```BigInteger```的低位：
      ```
      BigInteger moby = ...;
      moby = moby.flipBit(0);
      ```
      ```flipBit```方法创建了一个新的百万位```BigInteger```实例，时间与空间上将付出很大代价。像这种执行一个多步操作，每个操作生成一个新对象且除了最终结果之外丢弃所有对象，将会产生性能问题，这类的工作可交由包级私有的可变伙伴类负责，如```String```类的可变伙伴类```StringBuilder/StringBuffer```。
  * 使用私有构造方法与公共静态工厂方法代替```final```修饰类
    ```
    public final class Complex{
      private final double re;
      private final double im;

      private Complex(double re, double im) {
        this.re = re;
        this.im = im;
      }

      public static Complex valueOf(double re, double im) {
        return new Complex(re,im);
      }

      public double realPart() {
        return re;
      }
      public double imaginaryPart() {
        return im;
      }
      // 函数式方法，方法返回将操作数应用于函数的结果，结果将以新实例返回，该实例状态未改变
      public Complex plus(Complex c) {
        return new Complex(re + c.re, im + c.im);
      }
    }
    ```
  * 假设不可变类可能出现改变情况使用保护性拷贝避免状态被改变后丢失
    ```
    public static Complex safeInstance(Complex val) {
      return val.getClass() == Complex.class ? val : new Complex(val.toByteArray());
    }
    ```

> 组合优于继承
  * 继承是实现代码重用的一种方式，但使用不当易造成程序脆弱。继承违反封装，子类依赖于其父类的实现细节来保证其正确的功能，父类的实现细节可能从发布版本不断变化，如果是这样，子类可能会被破坏，因此子类必须与其父类一起根据发布版本变化，故子类与父类确实存在子父类关系时才考虑使用继承，但如果子类与父类不在同一个包且父类不是为继承而设计的，考虑使用组合的方式代替继承。
  * 使用继承方式编写可以查询历史添加元素总数的```Set```
    ```
    public class InstrumentedHashSet<E> extends HashSet<E> {
      private int addCount = 0;

      public InstrumentedHashSet() {
      }

      public InstrumentedHashSet(int initCap, float loadFactor) {
        super(initCap, loadFactor);
      }

      @Override
      public boolean add(E e) {
        addCount++;
        return super.add(e);
      }

      // supper.addAll()方法会调用重写的add()方法，会造成添加元素总数累加计算多一倍，故不需要重写该方法
      //@Override
      //public boolean addAll(Collection<? extends E> c) {
        //addCount += c.size();
        //return super.addAll(c);
      //}

      public int getAddCount(){
        return addCount;
      }
    }
    ```
  * 使用组合方式编写可以查询历史添加元素总数的```Set```
    ```
    public class ForwardingSet<E> implements Set<E> {
      private final Set<E> s;

      public ForwardingSet(Set<E> s) {
        this.s = s;
      }

      public boolean add(E e) {
        retunr s.add(e);
      }

      public boolean addAll(Collection<?> c) {
        return c.addAll(c);
      }
      ...
    }
    public class InstrumentedHashSet<E> extends ForwardingSet<E> {
      private int addCount = 0;

      public InstrumentedHashSet(Set<E> s) {
        super(s);
      }

      @Override
      public boolean add(E e) {
        addCount++;
        return super.add(e);
      }

      @Override
      public boolean addAll(Collection<? extends E> c) {
        addCount += c.size();
        return super.addAll(c);
      }

      public int getAddCount(){
        return addCount;
      }
    }
    ```

> 要么设计继承并提供文档说明，要么禁用继承
  * 为继承设计的类需要提供文档说明，文档说明可重写方法的自用性，即必须指明方法调用了哪些可重写方法，调用可重写方法顺序以及每次调用的结果，如```java.util.AbstractCollection```
    ```
    /**
     * Removes from this list all of the elements whose index is between
     * {@code fromIndex}, inclusive, and {@code toIndex}, exclusive.
     * Shifts any succeeding elements to the left (reduces their index).
     * This call shortens the list by {@code (toIndex - fromIndex)} elements.
     * (If {@code toIndex==fromIndex}, this operation has no effect.)
     *
     * <p>This method is called by the {@code clear} operation on this list
     * and its subLists.  Overriding this method to take advantage of
     * the internals of the list implementation can <i>substantially</i>
     * improve the performance of the {@code clear} operation on this list
     * and its subLists.
     *
     * <p>This implementation gets a list iterator positioned before
     * {@code fromIndex}, and repeatedly calls {@code ListIterator.next}
     * followed by {@code ListIterator.remove} until the entire range has
     * been removed.  <b>Note: if {@code ListIterator.remove} requires linear
     * time, this implementation requires quadratic time.</b>
     *
     * @param fromIndex index of first element to be removed
     * @param toIndex index after last element to be removed
     */
    protected void removeRange(int fromIndex, int toIndex) {
        ListIterator<E> it = listIterator(fromIndex);
        for (int i=0, n=toIndex-fromIndex; i<n; i++) {
            it.next();
            it.remove();
        }
    }
    ```
  * 为继承设计的类构造方法绝不能直接或间接调用可重写方法
  * 测试为继承设计的类的方法是编写子类
  * 限制不安全的子类化的方式可选择禁用继承，禁用继承的方式有：
    * 声明类为```final```
    * 所有构造方法都私有或包级私有且添加公共静态工厂方法代替公共构造

> 接口优于抽象类
  * 接口与抽象类，允许多个实现的类，两者都包含抽象方法与实现方法（```Java```8中引入接口的默认方法，```default methods```）,一个主要的区别是抽象类的实现通过继承（```extends```）完成，接口则直接实现（```implements```）完成；抽象类允许构建层级类型的框架，而接口允许构建非层级类型的框架。
     ```
     // 抽象类
     public abstract class AbstractCollection<E> implements Collection<E> {
       
       protected AbstractCollection() {}
       
       public abstract Iterator<E> iterator();
      
       public abstract int size();
      
       public boolean isEmpty() {
         return size() == 0;
       }
       ...
     }
     ```
     ```
     // 接口
     public interface Iterable<T> {

       Iterator<T> iterator();

       default void forEach(Consumer<? super T> action) {
         Objects.requireNonNull(action);
         for (T t : this) {
           action.accept(t);
         }
       }
       ...
     }
     ```
  * 接口优于抽象类，一个类不能继承多个抽象父类，只能层级继承，此过程中可能其中一个抽象父类没有在层级结构中找到合适的插入位置，层级继承后，无论后代是否合适，所有后代都进行子类化，而类可以实现多个接口，实现多个接口的声明方法。相比抽象类，接口更加安全，灵活且易拓展。
  * 接口与抽象类组合使用构建骨架实现类（```AbstractInterface```）,接口定义类型，提供默认方法，而骨架实现类在原始接口方法的顶层实现剩余的非原始接口方法，如[```AbstractList```](https://docs.oracle.com/javase/8/docs/api/)

> 为接口添加新方法
  * ```Java```8之前在现有实现类的情况下为接口添加方法，现有实现类也必须添加方法实现，否则将导致编译时错误；```Java```8中，在接口中允许添加默认方法，该方法允许在实现接口的类直接使用，不必实现默认方法，但这种为接口添加方法的方式存在风险，编写默认方法需要保留每个可能的实现的所有不变量，如```Collection```的```removeIf```默认方法在```Apache```的```SynchronizedCollection```实现中失败，```SynchronizedCollection```类的基本承诺是它的所有方法在委托给包装类集合类之前在一个锁定对象上进行同步，而```SynchronizedCollection```未重写```removeIf```方法，它将继承```removeIf```的默认实现，这样子无法保证它的承诺，可能出现在客户端的另一个线程同时修改包装类集合的情况下调用```SynchronizedCollection```的```removeIf```方法，会导致```ConcurrentModificationException```等异常。
    ```
    default boolean removeIf(Predicate<? super E> filter) {
      Objects.requireNonNull(filter);
      boolean removed = false;
      final Iterator<E> each = iterator();
      while (each.hasNext()) {
        if (filter.test(each.next())) {
          each.remove();
          removed = true;
        }
      }
      return removed;
    }
    ```
  * 如果现有接口的实现不会受到接口默认方法实现的破坏，可以选择在接口中添加默认方法，其他情况下应该尽量避免使用这种方式。

> 接口仅用来定义类型
  * 当类实现接口时，该接口当作一种类型可以用来引用类的实例。
    ```
    private UserService userService;
    ...
    userService.getUserInfo();
    ...
    ```
  * 接口不能用来仅定义常量，常量接口不包含任何方法，只包含静态final属性，输出常量，这种方式的目的在于使用这些常量的类实现接口以避免需要用类名限定常量名。
    ```
    public interface PhysicalConstants { 
      // Avogadro's number (1/mol) 
      static final double AVOGADROS_NUMBER = 6.022_140_857e23; 
      // Boltzmann constant (J/K) 
      static final double BOLTZMANN_CONSTANT = 1.380_648_52e-23; 
      // Mass of the electron (kg) 
      static final double ELECTRON_MASS = 9.109_383_56e-31; 
    }
    ```
    使用常量接口的缺点：
      * 类内部使用常量属于实现细节，实现常量接口会导致这个实现细节暴露于类导出的API中。
      * 若在未来版本中修改类使其不使用常量，为了保持二进制兼容性，仍然需要实现接口。
      * 若一个非final类实现常量接口，其所有子类的命名空间都会受到常量污染。
    常量接口的代替方式：
      * 若常量与现有类关系紧密，常量可直接在现有类维护。
      * 使用枚举类型维护常量。
      * 使用不可实例化的工具类维护常量。

> 类层次结构优于标签类

> 支持使用静态成员类而不是非静态类

> 将源文件限制为单个顶级类