## EffectiveJava3

#### 序列化

> 优先选择 Java 序列化的替代方案
  * ```Java```序列化有一定的风险，虽然能够实现分布式对象但代价较大，如不可见的构造函数、```API```与实现之间模糊的界线，还可能出现正确性、性能、安全性和维护方面的问题。序列化的根本问题在于它的可攻击范围太大，难以维护且问题在不断增多，可以通过调用```ObjectInputStream```上的```readObject```方法反序列化对象，这个方法可以用来实例化类路径上实现```Serializable```接口的任何类型的对象，在反序列化字节流的过程中，此方法可以执行来自任何这些类型的代码，因此所有这些类型的代码都在攻击范围内。攻击范围可涉及```Java```平台库、第三方库和应用程序本身中的类。在反序列化过程中调用潜在危险活动的方法称为```gadget```，若不使用任何```gadget```，通过对需要长时间才能反序列化的短流进行反序列化发起拒绝服务攻击，这种流被称为反序列化炸弹。
  * ```Java```序列化的替代方案：
    * 永远不反序列化任何东西。
    * 使用跨平台结构数据表示，如```JSON```和```Protocal Buffers```。前者设计用于浏览器与服务器通信，后者设计用于服务器之间存储和交换数据化结构。```JSON```和```Protocal Buffers```最显著的区别是```JSON```基于文本，可读性好，```Protocal Buffers```是二进制，效率高，但也提供了一种文本表示```pbtxt```。
    * 对于遗留系统，不能完成避免```Java```序列化，最佳实践是永远不反序列化不可信的数据。
    * 若无法避免反序列化且不能保证反序列化数据的安全性，可以使用```Java9```中添加的对象反序列化筛选并将其移植，该工具运行指定一个过滤器，该过滤器在反序列化数据流之前应用于数据流，它在类粒度上运行，运行接受或拒绝某些类，在默认情况下拒绝其他类并接受假定安全的类列表（白名单）。

> 非常谨慎地实现 Serializable
  * 类的实例序列化只需实现```Serializable```接口即可，虽然使类序列化的即时代价可忽略不计，但长期代价通常是巨大的：
    * 一旦类的实例被发布，则会降低更改该类实现的灵活性。当类实现```Serializable```接口，其字节流编码（或序列化形式）成为其导出```API```的一部分。如果不使用自定义序列化形式，则使用默认形式，则序列化形式将永远绑定在类的初始内部实现上，类中私有包以及私有实例字段将成为导出```API```的一部分，此时最小化字段作用域作为信息隐藏工具，将失去其有效性。如果接受默认的序列化形式然后更改类的内部实现，则会导致与序列化形式不兼容（串行版本```UID``` ```serialVersionUID```），试图使用类的旧版本序列化实例，再使用新版本反序列化实例的客户端程序将会失败，可以在维护原始序列形式的同时更改内部实现（使用```ObjectOutputStream.putFields```或```ObjectInputStream.readFields```）但这将在源代码上留下明显的缺陷。
    * 增加了出现```bug```和安全漏洞的可能性。反序列化是一个隐藏构造函数，具有其他构造函数存在的所有问题。依赖默认的反序列化机制，会让对象轻易遭受不变性破坏和非法访问。
    * 增加与发布类的新版本相关的测试负担。当一个可序列化的类被修改时，需要检查是否可以自爱新版本中序列化一个实例，并在旧版本中反序列化它。所需的测试量与可序列化类的数量以及版本的数量成正比。
  * 谨慎实现```Serializable```接口：
    * 如果一个类要参与一个框架，该框架依赖于```Java```序列化进行对象传输或持久化，对于类来说实现```Serializable```接口是非常重要的。如果类```A```要成为类```B```的一个组件，类```B```则必须实现```Serializable```接口，若类```A```可序列化，它将更容易被使用。```Java```类库也实现```Serializable```接口，如：```BigInteger```和```Instant```等值类、集合类，表示活动实体（如线程池）的类很少情况适合实现```Serializable```接口。
    * 为继承而设计的类很少情况适合实现```Serializable```接口，接口也很少情况适合拓展它。如果一个类或接口的存在主要是为了参与一个要求所有参与者都实现```Serializable```接口的框架，那么类和接口实现或拓展```Serializable```可能是有意义的。为继承而设计的类如```Throwable```类和```Component```类，正因为实现了```Serializable```接口，```Throwable```支持```RMI```可以将异常从服务器发送到客户端；```Component```支持发送、保存和恢复```GUI```。
    * 如果实现一个带有实例字段的类，它同时是可序列化和可扩展的，那么需要注意：
      * 如果字段值上有任何不变量，需要防止子类覆盖```finalize```方法，可以通过覆盖```finalize```并声明它为```final```。
      * 如果类的实例字段初始化值（整数类型为0，布尔值类型为```false```，对象引用类型为```null```），则必须添加```readObjectNoData```方法：
        ```
        private void readObjectNoData() throws InvalidObjectException { 
            throw new InvalidObjectException("Stream data required"); 
        }
        ```
    * 内部类不应该实现```Serializable```，但静态成员类可以实现。    

> 考虑使用自定义的序列化形式
  * 编写类时通常将精力集中在设计```API```上，这意味着发布一次性实现，在将来的版本中可能会替换它。如果该类还实现```Serializable```接口且使用默认的序列化形式，在将来更改替换时反序列话将会出现问题，这种情况发生在```Java```库中的几个类上，包括```BigInteger```。
  * 考虑使用默认的序列化形式：
    * 从正确性、性能和灵活性的角度综合看，生成的编码是合理的，如设计自定义序列化形式生成的编码与默认序列化形式生成的编码很大程度上相同时，考虑使用默认的序列化形式。
    * 如果对象的逻辑内容与物理表示相同，默认的序列化形式是合适的。如表示人名的类：
      ```
      // Good candidate for default serialized form 
      public class Name implements Serializable { 
          /*** Last name. Must be non-null. 
          * @serial 
          */ 
          private final String lastName; 
          
          /*** First name. Must be non-null. 
          * @serial 
          */ 
          private final String firstName; 
          
          /*** Middle name, or null if there is none. 
          * @serial
           */ 
          private final String middleName;
          
          ... // Remainder omitted 
      }
      ```
      逻辑上该类表示姓名由姓、名、中间名组成。物理上```Name```的实例字段包含姓、名、中间名。认为默认的序列化形式是合适的，通常也必须提供```readObject```方法来确保安全性和不变性，该方法必须保证字段```lastName```和```firsttName```是非空的。```lastName```、```firstName```和```middleName```字段是私有的，因为它们定义了类的序列化形式的公共```API```，所以必须使用```@serial```文档注解进行文档化。
  * 设计一个字符串列表：
    ```
    public final class StringList implements Serializable { 
        private int size = 0; 
        private Entry head = null; 
        
        private static class Entry implements Serializable { 
            String data; 
            Entry next; 
            Entry previous; 
        }
        
        ... // Remainder omitted 
    }
    ```
    逻辑上这个类表示字符串序列，物理上则表示双向链表，如果使用默认的序列化形式，该序列化形式将镜像除链表中的所有项以及这些项的双向链接。
    
    当对象的逻辑内容与物理表示有很大差异时，使用默认的序列化形式有以下缺点：
      * 它将导出的```API```永久地绑定至当前的内部实现。
      * 它会占用过多的空间。
      * 它会消耗过多的时间。
      * 它可能导致堆栈溢出。

    使用列表中的字符串数量以及字符串本身，合理自定义序列化形式：
      ```
      public final class StringList implements Serializable {
          private transient int size = 0; 
          private transient Entry head = null; 
        
        private static class Entry { 
            String data; 
            Entry next; 
            Entry previous; 
        }
        
        public final void add(String s) { ... }

        private synchronized void writeObject(ObjectOutputStream s) throws IOException { 
            s.defaultWriteObject(); 
            s.writeInt(size); 
            // Write out all elements in the proper order.
            for (Entry e = head; e != null; e = e.next)
                s.writeObject(e.data); 
        }

        private void readObject(ObjectInputStream s) throws IOException, ClassNotFoundException { 
            s.defaultReadObject(); 
            int numElements = s.readInt(); 
            // Read in all elements and insert them in list
            for (int i = 0; i < numElements; i++) 
                add((String) s.readObject()); 
        }
      }
      ```
      使用自定义序列化表单，大多数或所有实例字段都应该标记```transient```修饰符，表示从类的默认序列化形式表单中省略该实例字段，在反序列化实例时，这些实例字段将初始化为默认值（对象引用字段为```null```、数字基本类型字段为0，布尔字段为```false```），故需要提供一个```readObject```方法或延迟初始化的方式将实例字段恢复为可接受的值。```writeObject```方法与```readObject```方法应该使用```@serialData```文档注解表示方法时序列化形式的公共```API```。必须对序列化对象操作强制执行同步，保证线程安全。
  * 无论选择哪种序列化形式，都需要在编写的每个可序列化类中声明显式的序列版本```UID```。消除序列版本```UID```成为不兼容性的潜在来源且提高性能，避免在运行时因未提供序列版本      ```UID```计算生成。声明序列版本```UID```，在类中新增一行：
    ```
    private static final long serialVersionUID = randomLongValue;
    ```

> 保护性的编写readObject方法
  * 如果需要极力维护其约束条件和不可变性的类支持序列化或反序列化，则需要编写保护性的```readObject```方法。如不可变的日期范围类，它包含可变的私有变量```Date```，该类构造器支持保护性的拷贝```Date```对象：
    ```
    public final class Period { 
        private final Date start; 
        private final Date end; 
        
        public Period(Date start, Date end) { 
            this.start = new Date(start.getTime()); 
            this.end = new Date(end.getTime()); 
            if (this.start.compareTo(this.end) > 0) 
                throw new IllegalArgumentException(start + " after " + end); 
        }
        
        public Date start () { 
            return new Date(start.getTime()); 
        }
        
        public Date end () { 
            return new Date(end.getTime()); 
        }
        
        public String toString() { 
            return start + " - " + end; 
        }
    }
    ```
    该对象的物理表示与逻辑内容相同，所以可以使用默认的序列化形式，在类声明中增加```implements Serializable```，但是这将导致对象失去不变性。因为反序列化时使用默认的```readObject```方法构造对象，没有检查参数的有效性和对参数进行保护性拷贝，以致攻击者可以通过修改序列化后的字节流以及额外的引用引用对象引用，使得可以修改类的不变量：
    ```
    public class MutablePeriod { 
        // A period instance 
        public final Period period; 
        // period's start field, to which we shouldn't have access 
        public final Date start; 
        // period's end field, to which we shouldn't have access
        public final Date end; 
        
        public MutablePeriod() { 
            try {
                ByteArrayOutputStream bos = new ByteArrayOutputStream(); ObjectOutputStream out = new ObjectOutputStream(bos); 
                // Serialize a valid Period instance 
                out.writeObject(new Period(new Date(), new Date())); 
                /** Append rogue "previous object refs" for internal * Date fields in Period. For details, see "Java * Object Serialization Specification," Section 6.4. 
                */
                byte[] ref = { 0x71, 0, 0x7e, 0, 5 }; 
                // Ref #5 
                bos.write(ref); 
                // The start field 
                ref[4] = 4; 
                // Ref # 4 
                bos.write(ref); 
                // The end field 
                // Deserialize Period and "stolen" Date references ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bos.toByteArray())); 
                period = (Period) in.readObject(); 
                start = (Date) in.readObject(); 
                end = (Date) in.readObject(); 
            }catch (IOException | ClassNotFoundException e) { 
                throw new AssertionError(e); 
            } 
        } 
    }
    ```
    ```
    public static void main(String[] args) { 
        MutablePeriod mp = new MutablePeriod(); 
        Period p = mp.period; 
        Date pEnd = mp.end; 
        // Let's turn back the clock 
        pEnd.setYear(78);
        System.out.println(p); 
        // Bring back the 60s! 
        pEnd.setYear(69); 
        System.out.println(p); 
    }
    ```
    ```
    Wed Nov 22 00:21:29 PST 2017 - Wed Nov 22 00:21:29 PST 1978 
    Wed Nov 22 00:21:29 PST 2017 - Sat Nov 22 00:21:29 PST 1969
    ```
    对```readObject```方法进行参数有效性检查以及不可变变量的保护性拷贝，保护性拷贝必须在有效性检查之前进行，为了使用保护性字段，取消```final```关键字修饰：
    ```
    private void readObject(ObjectInputStream s) throws IOException, ClassNotFoundException { 
        s.defaultReadObject(); 
        // Defensively copy our mutable components 
        start = new Date(start.getTime()); 
        end = new Date(end.getTime()); 
        // Check that our invariants are satisfied 
        if (start.compareTo(end) > 0) 
            throw new InvalidObjectException(start +" after "+ end); 
    }
    ```
  * 编写健壮的```readObject```方法：
    * 类中的对象引用字段必须保持未私有属性，要保护性的拷贝这些字段的每个对戏。
    * 对于任何约束条件，如果检查失败就抛出```InvalidObjectException```异常。这些检查动作必须在所有保护性拷贝之后。
    * 如果整个对象在被反序列化之后必须进行验证，就应该使用```ObjectInputValidation```接口。
    * 无论是直接方法还是间接方法，都不要调用类中任何可被覆盖的方法。

> 对于实例控制，枚举类型优于 readResolve
  * 对于单例模式的类，增加```implements Serializable```声明，会返回一个新建的实例，这个新建的实例不同于类初始化时创建的实例，无论使用默认的序列化形式，还是自定义的序列化形，使用默认的```readObject```或是显式的```readObject```都无关。可以使用```readResolve```或枚举类型控制实例控制，但枚举类型优于```readResolve```。单例类如下：
    ```
    public class Elvis { 
        public static final Elvis INSTANCE = new Elvis(); 

        private Elvis() { ... } 
        
        public void leaveTheBuilding() { ... } 
    }
    ```
  * 使用```readResolve```解决单例类反序列化破坏单例模式的问题：
    ```
    private Object readResolve() { 
        return INSTANCE; 
    }
    ```
    ```readResolve```特性使用另一个实例代替用```readObject```创建的实例，在序列化之后，新建对象的```readResolve```方法会被调用，该方法返回的对象将取代新建的对象，新建的对线的引用将不会被保留，成为垃圾回收的对象。该方法忽略了被反序列化的对象，只返回类初始化创建的特殊```Elvis```实例，故```Elvis```实例的反序列化形式不应该包含任何实际数据，所有实例字段都应该被声明为```transient```。

    如果依赖```readResolve```进行实例控制，带有对象引用类型的所有实例字段都必须声明为```transient```。否则当对象引用字段的内容在```readResolve```之前被反序列化，它允许攻击者制作的流指向最初被反序列化的单例对象引用：
    ```
    // 单例类
    public class Elvis implements Serializable { 
        public static final Elvis INSTANCE = new Elvis(); 
        
        private Elvis() { } 
        
        private String[] favoriteSongs = { 
            "Hound Dog", "Heartbreak Hotel" 
        }; 
        
        public void printFavorites() { 
            System.out.println(Arrays.toString(favoriteSongs)); 
        }
        
        private Object readResolve() { 
            return INSTANCE; 
        } 
    }
    ```
    ```
    //攻击类
    public class ElvisStealer implements Serializable { 
        static Elvis impersonator; 
        private static final long serialVersionUID = 0; 
        private Elvis payload; 
        
        private Object readResolve() { 
            // Save a reference to the "unresolved" Elvis instance impersonator = payload; 
            // Return object of correct type for favoriteSongs field 
            return new String[] { "A Fool Such as I" }; 
        } 
    }
    ```
    ```
    //攻击程序
    public class ElvisImpersonator { 
        // Byte stream couldn't have come from a real Elvis instance! 
        private static final byte[] serializedForm = { 
            (byte) 0xac, (byte) 0xed, 0x00, 0x05, 0x73, 0x72, 0x00, 0x05, 0x45, 0x6c, 0x76, 0x69, 0x73, (byte) 0x84, (byte) 0xe6, (byte) 0x93, 0x33, (byte) 0xc3, (byte) 0xf4, (byte) 0x8b, 0x32, 0x02, 0x00, 0x01, 0x4c, 0x00, 0x0d, 0x66, 0x61, 0x76, 0x6f, 0x72, 0x69, 0x74, 0x65, 0x53, 0x6f, 0x6e, 0x67, 0x73, 0x74, 0x00, 0x12, 0x4c, 0x6a, 0x61, 0x76, 0x61, 0x2f, 0x6c, 0x61, 0x6e, 0x67, 0x2f, 0x4f, 0x62, 0x6a, 0x65, 0x63, 0x74, 0x3b, 0x78, 0x70, 0x73, 0x72, 0x00, 0x0c, 0x45, 0x6c, 0x76, 0x69, 0x73, 0x53, 0x74, 0x65, 0x61, 0x6c, 0x65, 0x72, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01, 0x4c, 0x00, 0x07, 0x70, 0x61, 0x79, 0x6c, 0x6f, 0x61, 0x64, 0x74, 0x00, 0x07, 0x4c, 0x45, 0x6c, 0x76, 0x69, 0x73, 0x3b, 0x78, 0x70, 0x71, 0x00, 0x7e, 0x00, 0x02 
        };
        
        public static void main(String[] args) { 
            // Initializes ElvisStealer.impersonator and returns 
            // the real Elvis (which is Elvis.INSTANCE) 
            Elvis elvis = (Elvis) deserialize(serializedForm); 
            Elvis impersonator = ElvisStealer.impersonator; 
            elvis.printFavorites(); 
            impersonator.printFavorites();
        } 
    }
    ```
    这个程序会产生如下输出：
    ```
    [Hound Dog, Heartbreak Hotel] 
    [A Fool Such as I]
    ```
    可以通过将```favoriteSongs```字段声明为```transient```，可以修复这个问题。

  * 使用枚举类型解决单例类反序列化破坏单例模式的问题：
    ```
    // Enum singleton - the preferred approach 
    public enum Elvis { 
        INSTANCE; 
        
        private String[] favoriteSongs = { 
            "Hound Dog", "Heartbreak Hotel" 
        }; 
        
        public void printFavorites() {
            System.out.println(Arrays.toString(favoriteSongs)); 
        } 
    }
    ```
  * 应该尽可能的使用枚举类型来实施实例控制的约束条件。如果做不到，同时又需要一个即可序列化又可以实例受控的类，就必须提供一个```readResolve```方法，并确保该类的所有实例化字段都被基本类型，或者是```transient```。

> 考虑用序列化代理代替序列化实例
  * 实现```Serializable```接口会增加出错和出现安全问题的可能性。使用序列化代理模式可以减少这些风险：
    * 为可序列化的类设计一个私有的静态嵌套类，称为序列化代理，精确表示外围类的逻辑状态。它包含一个单独的构造器，参数类型为外围类，从它的参数重复制数据，不需要进行任何一致性校验或保护性拷贝。外围类以及其序列化代理都必须声明```Serializable```接口，序列化代理的默认序列化形式是外围类最好的序列化形式：
      ```
      private static class SerializationProxy implements Serializable {
          private final Date start; 
          private final Date end; 
          
          SerializationProxy(Period p) { 
              this.start = p.start; 
              this.end = p.end; 
          }
          
          private static final long serialVersionUID = 234098243823485285L;
      }
      ```
    * 将```writeReplace```方法添加至外围类。这个方法将产生一个```SerializationProxy```实例代替外围类的实例：
      ```
      private Object writeReplace() { 
          return new SerializationProxy(this); 
      }
      ```
    * 防止攻击者有可能伪造违反该类约束条件的示例，需要在外围类添加```readObject```方法抛出异常：
      ```
      // readObject method for the serialization proxy pattern 
      private void readObject(ObjectInputStream stream) throws InvalidObjectException { 
          throw new InvalidObjectException("Proxy required"); 
      }
      ```
    * 最后在```SerializationProxy```类添加一个```readResolve```方法，返回逻辑上等价的外围类，这个方法令序列化系统在反序列化时将序列化代理转为外围类的实例：
      ```
      // readResolve method for Period.SerializationProxy 
      private Object readResolve() { 
          return new Period(start, end); // Uses public constructor 
      }
      ```
  * 序列化代理方式可以阻止伪字节流的攻击以及内部字段的盗用攻击。使用这种方式，序列化代理模式的功能比保护性拷贝更加强大，允许反序列实例有着与原始序列化实例不同的类，这种方式在实际应用中提供便利，如序列化```EnumSet```枚举类型，它的枚举有60个元素，将这个枚举类型加5个元素后反序列化，结果当它序列化时，是```RegularEnumSet```实例，反序列化时是```JunmboEnumSet```实例：
    ```
    private static class SerializationProxy<E extends Enum<E>> implements Serializable { 
        private static final long serialVersionUID = 362491234563181265L; 
        
        // The element type of this enum set. 
        private final Class<E> elementType; 
        
        // The elements contained in this enum set. 
        private final Enum<?>[] elements; SerializationProxy(EnumSet<E> set){
            elementType = set.elementType; 
            elements = set.toArray(new Enum<?>[0]); 
        }
        
        private Object readResolve() { 
            EnumSet<E> result = EnumSet.noneOf(elementType);
            for (Enum<?> e : elements) 
                result.add((E) e);
            return result; 
        } 
    }
    ```
  * 序列化代理模式有局限性：
    * 它不能与可以被客户端拓展的类兼容。
    * 它不能与对象中包含循环的某些类兼容。
    * 性能开销增加。
  * 当必须在一个不能被客户端拓展的类上编写```readObject```或```writeObject```方法时，则应该考虑使用序列化代理模式。