## EffectiveJava3

#### 泛型

> 不要使用原始类型
  * 一个类或接口声明时有一个或多个类型参数，称为泛型类或泛型接口，泛型类和泛型接口统称为泛型类型，如接口```List<E>```。
  * 参数化类型，由类或接口后跟与泛型类型形式参数类型相对应的实际参数类型，使用尖括号包含，如接口```List<String>```，表示其元素类型为String的列表。
  * 原始类型，由泛型类型定义，是没有任何类型参数的泛型类型，如接口```List<String>```的原始类型```List```。原始类型主要为了兼容没有泛型类型之前的代码。
  * 使用原始类型合法的，但不应该使用，如果使用原始类型，则会丧失泛型所有安全性以及表达上的优势，如
    ```
    // 声明原始类型集合属性
    private final Collection stamps = ...;
    // 添加实例对象Coin
    stamps.add(new Coin()); // "unchecked call warning"
    // 从集合中检索实例对象Coin
    for (Iterator i = stamps.iterator(); i.hasNext();) {
      Stamp stamp = (Stamp)i.next(); // "Throws ClassCastException"
      ...
    }
    ```
    编辑时出现警告但仍可编译，运行时抛出异常。若使用泛型类型，添加不同的实例对象在编译时产生错误信息，调整完正确类型实例对象后，编译器在编译时插入不可见的强制类型转换以保证运行时检索元素不会出现```ClassCastException```异常情况。
    ```
    private final Collection<Stamp> stamps = ...;
    ```
  * 原始类型不应该作为形式参数，如果作为形参，泛型类型可作为实参传递给原始类型，丢失类型安全性，如集合允许插入任意对象的设计：
    ```
  
    private static void unsafeAdd(List list, Object o) { 
        list.add(o); 
    }
    public static void main(String[] args) { 
        List<String> strings = new ArrayList<>(); 
        unsafeAdd(strings, Integer.valueOf(42)); 
        String s = strings.get(0); // Has compiler-generated cast 
    }
    ```
    可以使用参数化类型：
    ```
    private static void safeAdd(List<Object> list, Object o) { 
        list.add(o); 
    }
    public static void main(String[] args) { 
        List<Object> objects = new ArrayList<>(); 
        safeAdd(objects, Integer.valueOf(42)); 
        Integer i = (Integer) objects.get(0); 
    }
    ```
  * 处理未知元素类型且无关紧要的集合，不应该使用原始类型，安全替代方式是使用无限制通配符类型，它是一种泛型类型，代表不需要关心实际类型参数，用问号代替，如```Set<E>```的无限制通配符类型```Set<?>```。将任意元素放入原始类型集合中，会破坏集合的类型不变性，而将任意元素放入无限制通配符中，会编译错误，避免运行时类型错误问题。
    ```
    static int numElementsInCommon(Set<?> s1, Set<?> s2) { 
        int result = 0;
        for (Object o1 : s1) { 
          if (s2.contains(o1)) { 
            result++; 
          }
        }
        return result; 
    }
    ```
  * 字面值中可以使用原始类型，如```List.class```，```String[].class```，```int.class```都是合法的，参数化类型```List<String>.class```是非法的。
  * 与运算符```instanceof```时使用原始类型，因为泛型类型信息在运行时进行擦除，在无限制通配符类型以外的参数化类型是非法的，且无限制通配符类型不会对运算符产生影响，使用```instanceof```的首选方法：
    ```
    if (o instanceof Set) {
      Set<?> set = (Set<?>) o;
      ...
    }
    ```
  * 术语参考
    | 术语 | 中文含义 | 例子 |
    | :----: | :----: | :----: |
    | Parameterized type | 参数化类型 | ```List<String>``` |
    | Actual type parameter | 实际类型参数 | ```String``` |
    | Generic type | 泛型类型 | ```List<E>``` |
    | Formal type parameter | 形式类型参数 | ```E``` |
    | Unbounded wildcard type | 无限制通配符类型 | ```List<?>``` |
    | Raw type | 原始类型 | ```List``` |
    | Bounded type parameter | 限制通配符参数 | ```<E extends Number>``` |
    | Recursive type bound | 递归类型限制 | ```<T extends Comparable<T>>``` |
    | Bounded wildcard type | 限制通配符类型 | ```List<? extends Number>``` |
    | Generic method | 泛型方法 | ```static <E> List<E> asList(E[] a)``` |
    | Type token | 类型令牌 | ```List.class``` |

> 消除非检查警告
  * 使用泛型编程，容易造成编译器发出非检查警告，如未经检查的强制转换警告、未经检查的方法调用警告、未经检查的参数化可变长度类型警告以及未经检查的转换警告。
  * 消除非检查警告的方式：
    * 对警告代码进行订正，确保警告消失。
      ```
      // warning: [unchecked] unchecked conversion
      Set<Object> set = new HashSet();
      // 订正
      Set<Object> set = new HashSet<>();
      ```
    * 如果不能消除警告，在证明引发警告的代码是安全类型的前提下，可以使用注解@SuppressWarnings("unchecked")抑制警告。注解@SuppressWarnings("unchecked")可用于任何声明，作用域从单个局部变量到整个类，使用该注解抑制警告的正确方式是作用于局部变量、短方法或构造方法上，作用范围尽可能小，避免其他警告被抑制。
      ```
      public <T> T[] toArray(T[] a) { 
        if (a.length < size) { 
          // This cast is correct because the array we're creating 
          // is of the same type as the one passed in, which is T[]. @SuppressWarnings("unchecked") 
          T[] result = (T[]) Arrays.copyOf(elements, size, a.getClass()); 
          return result; 
        }
        System.arraycopy(elements, 0, a, 0, size); 
        if (a.length > size) 
            a[size] = null; 
        return a; 
      }
      ```

> 列表优于数组
  * 列表与数组的不同：
    * 数组是协变的，如类```SubClass```是类```SuperClass```的子类，则数组类型```SubClass[]```是数组类型```SuperClass[]```的子类；泛型列表是不变的，```List<SubClass>```与```List<SuperClass>```是不同的类型。
      ```
      // 协变的数组易出现运行时错误
      Object[] obs = new Long[1];
      obs[0] = "str";  // Runtime Fail: Throws ArrayStoreException
      // 不变的泛型列表编译时报错
      List<Object> obs = new ArrayList<Long>();  // Compile Fail：Incompatible types 
      ```
    * 数组是具体化的，运行时知道并强制执行它们的元素类型，如上诉抛出的```Throws ArrayStoreException```；泛型列表通过擦除实现（擦除是允许泛型类型与不使用泛型类型的遗留代码自由互操作），编译时执行类型约束，并在运行时擦除类型信息。
  * 创建泛型类型数组（```new List<E>[]```）、参数化类型数组（```new List<String>[]```）、类型参数数组（```new E[]```）是非法的，列表与数组存在差异，所有将在编译时导致创建错误。
  * 当在强制转换为数组类型时，得到泛型数组创建错误，或是未经检查的强制转换警告时，最佳解决方案通常是使用集合类型```List<E>```而不是数组类型```E[]```。
    ```
    // 编写一个Chooser类实现游戏骰子
    // 没有泛型的简单实现，缺点：每次调用方法返回值都需要强制转化为所需类型，如果类型错误则强制转换失败
    public class Chooser { 
      private final Object[] choiceArray; 
      public Chooser(Collection choices) { 
        choiceArray = choices.toArray(); 
      }
      public Object choose() { 
        Random rnd = ThreadLocalRandom.current(); 
        return choiceArray[rnd.nextInt(choiceArray.length)]; 
      } 
    }
    // 使用泛型数组的简单实现，缺点：存在强制转化警告， unchecked cast：required: T[], found: Object[]
    public class Chooser<T> { 
      private final T[] choiceArray; 
      public Chooser(Collection<T> choices) { 
        choiceArray = (T[])choices.toArray(); 
      }
      public Object choose() { 
        Random rnd = ThreadLocalRandom.current(); 
        return choiceArray[rnd.nextInt(choiceArray.length)]; 
      } 
    }
    // 实现泛型列表的简单实现
    public class Chooser<T> { 
      private final List<T> choiceArray; 
      public Chooser(Collection<T> choices) { 
        choiceArray = new ArrayList<>(choices);
      }
      public Object choose() { 
        Random rnd = ThreadLocalRandom.current(); 
        return choiceArray.get(rnd.nextInt(choiceArray.size())));
      } 
    }
    ```

> 优先考虑泛型
  * 除了参数化声明并使用JDK提供的泛型类型以及方法，项目实践中存在自定义泛型类型以及方法的情况，如简单的堆栈实现：
    ```
    // 元素类型为Object类型
    public class Stack {
      private Object[] elements; 
      private int size = 0; 
      private static final int DEFAULT_INITIAL_CAPACITY = 16;

      public Stack() {
        elements = new Object[DEFAULT_INITIAL_CAPACITY];
      }

      public void push(Object e) { 
        ensureCapacity(); 
        elements[size++] = e; 
      }

      // 客户端必须强制转换返回的对象，运行时可能发生强制转换异常
      public Object pop() { 
        if (size == 0) 
            throw new EmptyStackException(); 
        Object result = elements[--size]; 
        elements[size] = null;
        return result; 
      }

      ...
    }
    // 元素类型为泛型类型，构造方法初始化数组时使用Object类型强转泛型类型E
    public class Stack<E> {
      private E[] elements; 
      private int size = 0; 
      private static final int DEFAULT_INITIAL_CAPACITY = 16;
      
      // 数组元素保存在私有属性，不会返回给客户端且不作为方法传递，故是安全的，使用注解@SuppressWarnings("unchecked")抑制强制类型转换警告
      @SuppressWarnings("unchecked")
      public Stack() {
        elements = (E)new Object[DEFAULT_INITIAL_CAPACITY];
      }

      public void push(E e) { 
        ensureCapacity(); 
        elements[size++] = e; 
      }

      public E pop() { 
        if (size == 0) 
            throw new EmptyStackException(); 
        E result = elements[--size]; 
        elements[size] = null;
        return result; 
      }

      ...
    }
    // 元素类型为泛型类型，私有数组声明为Object类型
    public class Stack<E> {
      private Object[] elements; 
      private int size = 0; 
      private static final int DEFAULT_INITIAL_CAPACITY = 16;
      
      public Stack() {
        elements = new Object[DEFAULT_INITIAL_CAPACITY];
      }

      public void push(E e) { 
        ensureCapacity(); 
        elements[size++] = e; 
      }

      public E pop() { 
        if (size == 0) 
            throw new EmptyStackException(); 
        // 因E是不可具体化的，无法在运行时进行强制转换，故是安全的，使用注解@SuppressWarnings("unchecked")抑制强制类型转换警告
        @SuppressWarnings("unchecked")
        E result = (E)elements[--size]; 
        elements[size] = null;
        return result; 
      }

      ...
    }
    ```
  * 泛型类型比需要在客户端代码中强制转换的类型更安全。当设计新的类型时，确保它们不需要强制转换的情况下使用，优先使用泛型类型。

> 优先使用泛型方法

> 使用限定通配符来增加API的灵活性

> 合理地结合泛型和可变参数

> 优先考虑类型安全的异构容器