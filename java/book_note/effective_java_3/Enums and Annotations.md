## EffectiveJava3

### 枚举与注解

> 使用枚举类型替代整型常量
  * 在枚举类型出现之前，常使用整型常量或字符串常量枚举模式，这种枚举模式存在很多缺点：
    ```
    public static final int APPLE_FUJI = 0;
    public static final int APPLE_PIPPIN = 1; 
    public static final int APPLE_GRANNY_SMITH = 2; 

    public static final int ORANGE_NAVEL = 0; 
    public static final int ORANGE_TEMPLE = 1; 
    public static final int ORANGE_BLOOD = 2;
    ```
    * 没有提供类型安全的方式，在方法传递中，允许不同类型传递，如```APPLE_```传递给需要```ORANGE_```的方法、```==``` 运算符的比较以及直接进行运算```int result = APPLE_ - ORANGE_```。
    * 没有名称空间，不同的类型需要使用前缀进行区分，如```APPLE_```与```ORANGE_```。
    * 程序脆弱，因为常量枚举模式是编译时常量，所以它们的值被编译到使用它们的客户端上，如果值发生改变，则必须重新编译客户端。
    * 没有打印值、迭代常量等方式。
  * 枚举可以解决上述问题，枚举是由一组固定常量组成的一种类型，比如一年的四季、太阳系的行星，都是枚举类型的典例，
    ```
    public enum Apple { 
        FUJI, PIPPIN, GRANNY_SMITH 
    } 

    public enum Orange { 
        NAVEL, TEMPLE, BLOOD 
    }
    ```
    枚举类型基本思想：通过公共静态```final```属性为每个枚举常量导出一个实例的类。没有可访问的构造方法，客户端既不能创建枚举类型的实例，也不能继承它，枚举类型是实例控制的，它们是单例的泛形化。常用的枚举类型声明方式：
    ```
    // 定义枚举 
     public enum Season {
         //定义枚举成员并实例化
         SPRING(1),SUMMER(2),AUTUMN(3),WINTER(4);
         //定义新变量
         private final int code;
         //定义新构造方法
         private Season(int code) {
             this.code = code;
         }
         //定义新方法
         public int getCode() {
             return this.code;
         }
     }
    ```
    枚举类型还允许添加任意属性和方法，并实现任何接口，可以增强枚举类型，如提供一个物体在地球上的质量，计算并显示该物体在八大行星上的重量：
    ```
    // Enum type with data and behavior 
    public enum Planet {
        MERCURY(3.302e+23, 2.439e6), 
        VENUS (4.869e+24, 6.052e6), 
        EARTH (5.975e+24, 6.378e6),
        MARS (6.419e+23, 3.393e6), 
        JUPITER(1.899e+27, 7.149e7), 
        SATURN (5.685e+26, 6.027e7), 
        URANUS (8.683e+25, 2.556e7),
        NEPTUNE(1.024e+26, 2.477e7); 
        
        private final double mass; // In kilograms 
        private final double radius; // In meters 
        private final double surfaceGravity; // In m / s^2 
        private static final double G = 6.67300E-11; // Universal gravitational constant in m^3 / kg s^2 
        
        // Constructor 
        Planet(double mass, double radius) { 
            this.mass = mass; 
            this.radius = radius; 
            surfaceGravity = G * mass / (radius * radius); 
        }
        
        public double mass() { 
            return mass; 
        } 
        public double radius() { 
            return radius; 
        } 
        public double surfaceGravity() { 
            return surfaceGravity; 
        } 
        public double surfaceWeight(double mass) { 
            return mass * surfaceGravity; // F = ma 
        } 
    }

    // test main
    public class WeightTable { 
        public static void main(String[] args) { 
            double earthWeight = Double.parseDouble(args[0]); double mass = earthWeight / Planet.EARTH.surfaceGravity();
            for (Planet p : Planet.values()) 
                System.out.printf("Weight on %s is %f%n", p, p.surfaceWeight(mass)); 
        } 
    }

    // console
    Weight on MERCURY is 69.912739 
    Weight on VENUS is 167.434436 
    Weight on EARTH is 185.000000 
    Weight on MARS is 70.226739 
    Weight on JUPITER is 467.990696 
    Weight on SATURN is 197.120111 
    Weight on URANUS is 167.398264 
    Weight on NEPTUNE is 210.208751
    ``` 
    枚举类型使用有用的抽象：
    ```
    public enum Operation { 
        PLUS("+") { 
            public double apply(double x, double y) { 
                return x + y; 
            } 
        },
        MINUS("-") { 
            public double apply(double x, double y) { 
                return x - y; 
            } 
        },
        TIMES("*") { 
            public double apply(double x, double y) { 
                return x * y; 
            } 
        },
        DIVIDE("/") {
            public double apply(double x, double y) { 
                return x / y; 
            } 
        };
        
        private final String symbol; 
        
        Operation(String symbol) { 
            this.symbol = symbol; 
        } 
        
        @Override 
        public String toString() { 
            return symbol; 
        } 
        
        public abstract double apply(double x, double y);
    }

    // test main
    public static void main(String[] args) { 
        double x = Double.parseDouble(args[0]); 
        double y = Double.parseDouble(args[1]);
        for (Operation op : Operation.values()) 
            System.out.printf("%f %s %f = %f%n", x, op, y, op.apply(x, y)); 
    }

    // console
    2.000000 + 4.000000 = 6.000000 
    2.000000 - 4.000000 = -2.000000 
    2.000000 * 4.000000 = 8.000000 
    2.000000 / 4.000000 = 0.500000
    ```
    枚举类型具有自动生成```ValueOf(String)```方法，即常量名称自动转换为常量值，如上述```op```枚举实例对象自动转换成```+```字符，这需要在枚举类型中重写```toString```方法，相对应的，可考虑编写```fromString```方法，将自定义字符转换为枚举实例对象：
    ```
    private static final Map<String, Operation> stringToEnum = Stream.of(values()).collect( toMap(Object::toString, e -> e)); 
    
    Optional<Operation> fromString(String symbol) { 
        return Optional.ofNullable(stringToEnum.get(symbol));
    }
    ```
    枚举类型可使用嵌套枚举的方式，解决多个在特定方法中```switch```方法使用带来的难以维护的问题，如计算工作日与周末不同的加班之后的工资：
    ```
    public enum PayrollDay { 
        MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, 
        SATURDAY(PayType.WEEKEND), SUNDAY(PayType.WEEKEND); 
        
        private final PayType payType; 
        
        PayrollDay(PayType payType) { 
            this.payType = payType; 
        } 
        PayrollDay() { 
            this(PayType.WEEKDAY); 
        }
        
        public int pay(int minutesWorked, int payRate) {
            return payType.pay(minutesWorked, payRate); 
        } 
        
        private enum PayType { 
            WEEKDAY { 
                int overtimePay(int minsWorked, int payRate){
                    return minsWorked <= MINS_PER_SHIFT ? 0 : (minsWorked - MINS_PER_SHIFT) * payRate / 2; 
                } 
            },
            WEEKEND { 
                int overtimePay(int minsWorked, int payRate){
                    return minsWorked * payRate / 2; 
                } 
            };
            
            abstract int overtimePay(int mins, int payRate);
             
            private static final int MINS_PER_SHIFT = 8 * 60; int pay(int minsWorked, int payRate) { 
                int basePay = minsWorked * payRate; 
                return basePay + overtimePay(minsWorked, payRate); 
            } 
        } 
    }
    ```

> 使用实例属性替代序数
  * 许多枚举类型与单个```int```值关联，所有枚举都有一个```ordinal```序数方法，它返回每个枚举常量类型的数值位置，这时可能会从序数中派生一个关联的```int```值：
    ```
    public enum Ensemble { 
        SOLO, DUET, TRIO, 
        QUARTET, QUINTET, SEXTET, 
        SEPTET, OCTET, NONET, 
        DECTET; 
        
        public int numberOfMusicians() { 
            return ordinal() + 1; 
        } 
    }
    ```
    这样子将难以维护```int```值，如果重新编排位置或者从中插入新枚举类型，```int```值将发生变化。
  * 使用将```int```值保存实例属性的方式替代序数方式：
    ```
    public enum Ensemble { 
        SOLO(1), DUET(2), TRIO(3), 
        QUARTET(4), QUINTET(5), SEXTET(6), 
        SEPTET(7), OCTET(8), DOUBLE_QUARTET(8), 
        NONET(9), DECTET(10), TRIPLE_QUARTET(12); 
        
        private final int numberOfMusicians; 
        
        Ensemble(int size) { 
            this.numberOfMusicians = size; 
        } 
        
        public int numberOfMusicians() { 
            return numberOfMusicians; 
        } 
    }
    ```

> 使用EnumSet替代位域
  * 如果枚举类型的元素主要用于集合中，传统上使用```int```枚举模式，如将2的不同次幂赋值给每个常量：
    ```
    public class Text { 
        public static final int STYLE_BOLD = 1 << 0; // 1 
        public static final int STYLE_ITALIC = 1 << 1; // 2 
        public static final int STYLE_UNDERLINE = 1 << 2; // 4 
        public static final int STYLE_STRIKETHROUGH = 1 << 3; // 8 

        // Parameter is bitwise OR of zero or more STYLE_ constants 
        public void applyStyles(int styles) { ... } 
    }
    ```
    这种表示方式允许位运算将几个常量合并到一个称为位域的集合中：
    ```
    text.applyStyles(STYLE_BOLD | STYLE_ITALIC);
    ```
    位域表示还允许你使用按位算术有效地执行集合运算，如并集和交集，但是位域具有```int```枚举常量等的所有缺点。
    使用```EnumSet```代替位域，```EnumSet```能够有效地从单个枚举类型中提取值的集合：
    ```
    public class Text { 
        public enum Style { BOLD, ITALIC, UNDERLINE, STRIKETHROUGH } 
        
        // Any Set could be passed in, but EnumSet is clearly best 
        public void applyStyles(Set<Style> styles) { ... } 
    }
    ```
    ```EnumSet```使用静态工厂方法创建枚举类型的元素集合，```EnumSet```实现了接口```Set```：
    ```
    text.applyStyles(EnumSet.of(Style.BOLD, Style.ITALIC));
    ```

> 使用EnumMap替代序数索引
  * 使用```ordinal```方法来索引数组或列表，设计一个植物类，植物类包含名称以及生命周期；一组植物类代表公园，设计且输出一个公园所有生命周期的植物有哪些：
    ```
    // 植物类
    public class Plant { 
        enum LifeCycle { ANNUAL, PERENNIAL, BIENNIAL }
        final String name;
        final LifeCycle lifeCycle; 
        
        Plant(String name, LifeCycle lifeCycle) { 
            this.name = name; 
            this.lifeCycle = lifeCycle; 
        }
        
        @Override 
        public String toString() { 
            return name; 
        } 
    }

    // 输出一个公园所有生命周期的植物，索引0代表ANNUAL，1代表PERENNIAL，2代表BIENNIAL
    Set<Plant>[] plantsByLifeCycle = (Set<Plant>[]) new Set[Plant.LifeCycle.values().length];
    
    for (int i = 0; i < plantsByLifeCycle.length; i++) 
        plantsByLifeCycle[i] = new HashSet<>();

    for (Plant p : garden) 
        plantsByLifeCycle[p.lifeCycle.ordinal()].add(p);

    for (int i = 0; i < plantsByLifeCycle.length; i++) { 
        System.out.printf("%s: %s%n", Plant.LifeCycle.values()[i], plantsByLifeCycle[i]); 
    }
    ```
    这种方法有效当充满问题：
      * 数组不兼容泛型，出现未检查类型的转换，不干净地编译。
      * 不清楚数组索引具体代表哪个枚举类型，需要手动标记输出。
      * 数组索引使用```int```值，不提供枚举的类型安全性，容易使用错误的值造成```ArrayIndexOutOfBoundsException```异常。
    解决这些问题使用```EnumMap```：
    ```
    Map<Plant.LifeCycle, Set<Plant>> plantsByLifeCycle = new EnumMap<>(Plant.LifeCycle.class);
    
    for (Plant.LifeCycle lc : Plant.LifeCycle.values()) 
        plantsByLifeCycle.put(lc, new HashSet<>());
    
    for (Plant p : garden) 
       plantsByLifeCycle.get(p.lifeCycle).add(p); 
    
    System.out.println(plantsByLifeCycle);
    ```
    除了解决上述问题外，运行速度与原始版本相当。
    使用```Java8 Stream```特性可修改为：
    ```
    System.out.println(
        Arrays.stream(garden)
            .collect(groupingBy(p -> p.lifeCycle, () -> new EnumMap<>(LifeCycle.class), toSet()))
    );
    ``` 

> 使用接口模拟可扩展的枚举
  * 枚举类型不可扩展，只当枚举类型包含抽象方法等抽象行为时，可使用接口方式代替实现，从而实现枚举类型的扩展目的：
    ```
    public interface Operation { 
        double apply(double x, double y); 
    }
    
    public enum BasicOperation implements Operation { 
        PLUS("+") { 
            public double apply(double x, double y) { 
                return x + y; 
            } 
        },
        MINUS("-") { 
            public double apply(double x, double y) { 
                return x - y; 
            } 
        },
        TIMES("*") { 
            public double apply(double x, double y) { 
                return x * y; 
            } 
        },
        DIVIDE("/") { 
            public double apply(double x, double y) { 
                return x / y; 
            } 
        };
        
        private final String symbol; 
        
        BasicOperation(String symbol) { 
            this.symbol = symbol; 
        }
        
        @Override 
        public String toString() { 
            return symbol; 
        } 
    }
    ```
    接口是可扩展的，用于表示枚举类型中抽象的行为，可以定义另外一个实现此接口的枚举类型：
    ```    
    public enum ExtendedOperation implements Operation { 
        EXP("^") { 
            public double apply(double x, double y) { 
                return Math.pow(x, y); 
            } 
        },
        REMAINDER("%") { 
            public double apply(double x, double y) { 
                return x % y; 
            } 
        };
        
        private final String symbol; 
        
        BasicOperation(String symbol) { 
            this.symbol = symbol; 
        }
        
        @Override 
        public String toString() { 
            return symbol; 
        } 
    }
    ```
* 扩展枚举类型可以传递给基本枚举类型：
  ```
  // 使用限度的类型令牌
  private static <T extends Enum<T> & Operation> void test(Class<T> opEnumType, double x, double y) {
      for (Operation op : opEnumType.getEnumConstants()) 
          System.out.printf("%f %s %f = %f%n", x, op, y, op.apply(x, y)); 
  }

  public static void main(String[] args) { 
      double x = Double.parseDouble(args[0]); 
      double y = Double.parseDouble(args[1]); 
      test(ExtendedOperation.class, x, y); 
  }

  // 使用限定通配符类型
  private static void test(Collection<? extends Operation> opSet, double x, double y) {
      for (Operation op : opSet) 
          System.out.printf("%f %s %f = %f%n", x, op, y, op.apply(x, y)); 
  }

  public static void main(String[] args) { 
      double x = Double.parseDouble(args[0]); 
      double y = Double.parseDouble(args[1]); 
      test((Arrays.asList(ExtendedOperation.values()), x, y); 
  }
  ```

> 注解优于命名模式
  * 过去通常使用命名模式来指示程序元素（方法），使用工具或框架对其进行特殊处理。如```JUnit3```测试框架要求测试方法名以```test```为前缀，使用命名模式的缺点：
    * 拼写错误导致测试失败，没有报错提示，也不会执行测试，导致错误的安全感。
    * 无法确保它们是仅用于适当范围的程序元素。如以类名为方法名称，希望能够测试类的所有方法，实际上不会执行测试。
    * 没有提供将参数值与程序元素相关联的方法。
  * 注解类型解决了以上问题，```JUnit4```使用注解类型，如注解```@Test```,用来指定自动运行的简单测试，并且抛出异常表示测试失败。```@Test```的定义如下：
    ```
    @Retention(RetentionPolicy.RUNTIME) 
    @Target(ElementType.METHOD) 
    public @interface Test { 

    }
    ```
    注解```@Retention```与```@Target```为元注解，```@Retention(RetentionPolicy.RUNTIME) ```指示```@Test```应该在运行时保留，```@Target(ElementType.METHOD)```指示```@Test```应用作用在方法上。```@Test```仅在无参静态方法中使用，但在实例方法或有参方法上，程序依然可以正常编译，由```JUnit4```在运行时处理这个问题。
    ```
    public class TestDemo {

        @Test
        public static void t1() {

        }
        @Test
        public void t2() {

        }

    }
    ```
    ```@Test```注解对```TestDemo```类的语义没有直接影响，只提供信息供测试框架等相关程序使用，如```JUnit4```，也可以自定义测试器使用：
    ```    
    public class RunTests { 
        
        public static void main(String[] args) throws
        Exception { 
            int tests = 0;
            int passed = 0; 
            // 获取命令行输入完全限定类名
            Class<?> testClass = Class.forName(args[0]);
            // 遍历指定类所有方法
            for (Method m : testClass.getDeclaredMethods()) {
                // 处理使用@Test声明的方法
                if (m.isAnnotationPresent(Test.class)) { 
                    tests++; 
                    try {
                        // 调用方法
                        m.invoke(null); 
                        // 记录通过数
                        passed++; 
                    } catch (InvocationTargetException wrappedExc) { 
                        // 捕获调用异常，输出异常
                        Throwable exc = wrappedExc.getCause(); 
                        System.out.println(m + " failed: " + exc); 
                    } catch (Exception exc) { 
                        // 捕获除调用异常外的异常，输出异常
                        System.out.println("Invalid @Test: " + m); 
                    } 
                } 
            }
            
            System.out.printf("Passed: %d, Failed: %d%n", passed, tests - passed); 
        }

    }
    ```
    该测试器支持命令行上接受完全限定类名，输出该类测试通过数以及失败数。
    若在抛出指定异常时才记录测试通过，需要另写一个新的注解类型```TestWithException```：
    ```
    @Retention(RetentionPolicy.RUNTIME) 
    @Target(ElementType.METHOD) 
    public @interface TestWithException { 

        Class<? extends Throwable> value(); 

    }
    ```
    以及对应客户端、测试器：
    ```
    public class TestWithExceptionDemo {

        @TestWithException(ArithmeticException.class)
        public static void t1() {
            int i = 0; 
            i = i / i;
        }
        @TestWithException(ArithmeticException.class)
        public void t2() {
            int[] a = new int[0]; 
            int i = a[1];
        }

    }

    public class RunTestWithExceptions { 
        
        public static void main(String[] args) throws
        Exception { 
            int tests = 0;
            int passed = 0; 
            // 获取命令行输入完全限定类名
            Class<?> testClass = Class.forName(args[0]);
            // 遍历指定类所有方法
            for (Method m : testClass.getDeclaredMethods()) {
                // 处理使用TestWithException声明的方法
                if (m.isAnnotationPresent(TestWithException.class)) { 
                    tests++; 
                    try {
                        // 调用方法
                        m.invoke(null); 
                        System.out.printf("Test %s failed: no exception%n", m);
                    } catch (InvocationTargetException wrappedExc) { 
                        // 获取调用异常
                        Throwable exc = wrappedEx.getCause(); 
                        // 获取声明异常类型
                        Class<? extends Throwable> excType = m.getAnnotation(TestWithException.class).value();
                        if (excType.isInstance(exc)) {
                            // 若捕获异常为声明异常类型，则测试通过
                            passed++;
                        } else {
                            System.out.printf( "Test %s failed: expected %s, got %s%n", m, excType.getName(), exc);
                        }
                    } catch (Exception exc) { 
                        // 捕获除调用异常外的异常，输出异常
                        System.out.println("Invalid @Test: " + m); 
                    } 
                } 
            }
            
            System.out.printf("Passed: %d, Failed: %d%n", passed, tests - passed); 
        }

    }
    ```
    可以声明注解类型值为数组形式，以支持多种异常中符合其一则测试通过的场景：
    ```
    // 声明注解类型
    @Retention(RetentionPolicy.RUNTIME) 
    @Target(ElementType.METHOD) 
    public @interface TestWithException { 
        Class<? extends Throwable>[] value(); 
    }
    // 客户端调用，使用花括号将元素括起来，并用逗号分隔
    public class TestWithExceptionDemo {

        @TestWithException({ArithmeticException.class, IndexOutOfBoundsException.class})
        public void t1() {
            int[] a = new int[0]; 
            int i = a[1];
        }

    }
    // 测试器
    public class RunTestWithExceptions { 
        
        public static void main(String[] args) throws
        Exception { 
            int tests = 0;
            int passed = 0; 
            // 获取命令行输入完全限定类名
            Class<?> testClass = Class.forName(args[0]);
            // 遍历指定类所有方法
            for (Method m : testClass.getDeclaredMethods()) {
                // 处理使用@TestWithException声明的方法
                if (m.isAnnotationPresent(TestWithException.class)) { 
                    tests++; 
                    try {
                        // 调用方法
                        m.invoke(null); 
                        System.out.printf("Test %s failed: no exception%n", m);
                    } catch (InvocationTargetException wrappedExc) { 
                        // 获取调用异常
                        Throwable exc = wrappedEx.getCause(); 
                        int oldPassed = passed;
                        // 获取声明异常类型
                        Class<? extends Throwable>[] excTypes = m.getAnnotation(TestWithException.class).value();
                        for (Class<? extends Throwable>[] excType : excTypes) {
                            if (excType.isInstance(exc)) {
                                // 若捕获异常为声明异常类型，则测试通过
                                passed++;
                                break;
                            }
                        }
                        if (passed == oldPassed) {
                            System.out.printf("Test %s failed: %s %n", m, exc);
                        }
                    } catch (Exception exc) { 
                        // 捕获除调用异常外的异常，输出异常
                        System.out.println("Invalid @Test: " + m); 
                    } 
                } 
            }
            
            System.out.printf("Passed: %d, Failed: %d%n", passed, tests - passed); 
        }

    }
    ```
    可以使用```@Repeatable```元注解来注解类型，代表注解类型可重复使用，以支持多种异常中符合其一则测试通过的场景：
    ```
    // 声明注解类型
    @Retention(RetentionPolicy.RUNTIME) 
    @Target(ElementType.METHOD) 
    @Repeatable(TestWithExceptionContainer.class)
    public @interface TestWithException { 
        Class<? extends Throwable> value(); 
    }
    // 声明注解类型容器，用于存放注解类型数组
    @Retention(RetentionPolicy.RUNTIME) 
    @Target(ElementType.METHOD) 
    public @interface TestWithExceptionContainer { 
        TestWithException[] value(); 
    }
    // 客户端调用，使用花括号将元素括起来，并用逗号分隔
    public class TestWithExceptionDemo {
        
        @TestWithException(ArithmeticException.class)
        @TestWithException(IndexOutOfBoundsException.class)
        public void t1() {
            int[] a = new int[0]; 
            int i = a[1];
        }

    }
    // 测试器
    public class RunTestWithExceptions { 
        
        public static void main(String[] args) throws
        Exception { 
            int tests = 0;
            int passed = 0; 
            // 获取命令行输入完全限定类名
            Class<?> testClass = Class.forName(args[0]);
            // 遍历指定类所有方法
            for (Method m : testClass.getDeclaredMethods()) {
                // 处理使用@TestWithException与@TestWithExceptionContainer声明的方法
                if (m.isAnnotationPresent(TestWithException.class) || m.isAnnotationPresent(TestWithExceptionContainer.class)) { 
                    tests++; 
                    try {
                        // 调用方法
                        m.invoke(null); 
                        System.out.printf("Test %s failed: no exception%n", m);
                    } catch (InvocationTargetException wrappedExc) { 
                        // 获取调用异常
                        Throwable exc = wrappedEx.getCause(); 
                        int oldPassed = passed;
                        // 获取声明异常类型
                        TestWithException[] excTypes = m.getAnnotationsByType(TestWithException.class);
                        for (Class<? extends Throwable>[] excType : excTypes) {
                            if (excType.isInstance(exc)) {
                                // 若捕获异常为声明异常类型，则测试通过
                                passed++;
                                break;
                            }
                        }
                        if (passed == oldPassed) {
                            System.out.printf("Test %s failed: %s %n", m, exc);
                        }
                    } catch (Exception exc) { 
                        // 捕获除调用异常外的异常，输出异常
                        System.out.println("Invalid @Test: " + m); 
                    } 
                } 
            }
            
            System.out.printf("Passed: %d, Failed: %d%n", passed, tests - passed); 
        }

    }
    ```
  * 若需要将信息标记源代码且不修改源代码定义，适当使用注解类型。

> 始终使用Override注解
  * ```Java```类库中包含许多注解类型，其中最常用的是```@Override```，此注解只能作用于方法上，表示该方法重写父类方法，始终使用该注解，避免出现严重```BUG```。如设计一个双字母类，在添加到不重复集合时使用双字母判断唯一：
    ```
    // 不使用@Override
    public class Bigram {

        private final char first;
        private final char second;

        public Bigram(char first, char second) {
            this.first = first;
            this.second = second;
        }

        public boolean equals(Bigram b) {
            return b.first = first && b.second = second;
        }

        public int hashCode() {
            return 31 * first + second;
        }

    }

    // 使用@Override
    public class Bigram {

        private final char first;
        private final char second;

        public Bigram(char first, char second) {
            this.first = first;
            this.second = second;
        }

        @Override
        public boolean equals(Object o) {
            if (!(o instanceof Bigram)) {
                return false;
            }
            Bigram b = (Bigram) o;
            return b.first = first && b.second = second;
        }

        @Override
        public int hashCode() {
            return 31 * first + second;
        }

    }
    ```
    不使用```@Override```并没有重写父类```Object```的```equals```、```hashCode```方法，只是重载，在将其添加至不重复集合时，依旧使用父类的```Object```的```equals```、```hashCode```方法进行唯一判断，进而导致添加重复的严重问题。
* 始终使用```Override```注解：
  * 重写父类的方法（重写抽象父类的抽象方法时可以不使用）
  * 实现接口的具体方法

> 使用标记接口定义类型