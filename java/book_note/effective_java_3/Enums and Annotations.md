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

> 使用EnumSet替代位属性

> 使用EnumMap替代序数索引

> 使用接口模拟可扩展的枚举

> 注解优于命名模式

> 始终使用Override注解

>  使用标记接口定义类型