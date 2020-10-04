## Java枚举类型

> 出现原由
  * 在Java枚举类型出现之前，枚举使用场景的设计方案是定义常量类并在该类定义静态常变量作为枚举类型，如下：
    ```
    public class Season {
        public static final int SPRING = 1;
        public static final int SUMMER = 2;
        public static final int AUTUMN = 3;
        public static final int WINTER = 4;
    }
    ```
    这种方式称为int枚举模式，这种模式安全性不安全，可读性差。比如设计一个方法，要求传入枚举类型的某个值，由于使用int类型，无法保证传入的值为合法，故不安全；在使用枚举的多数场景，都需要打印枚举成员，将int枚举常量打印的结果为一组数字，意义上不大，我们常使用String常量代替int常量，这些字符串常量提供了可打印的字符串但最终容易导致性能问题，因为它比较依赖字符串的比较操作。
    ```
    private String getChineseSeason(int season){
        StringBuffer result = new StringBuffer();
        switch(season){
            case Season.SPRING :
                result.append("春天");
                break;
            case Season.SUMMER :
                result.append("夏天");
                break;
            case Season.AUTUMN :
                result.append("秋天");
                break;
            case Season.WINTER :
                result.append("冬天");
                break;
            default :
                result.append("地球没有的季节");
                break;
        }
        return result.toString();
    }
    ```
    故在Java1.5发行版开始，就提供了一种可以替代的解决方案，可避免int和String枚举模式的缺点，枚举类型（enum type）。

> 枚举概念
  * 枚举是一种类型，表示一个有限的集合类型，在维基百科的定义为：
    ```
    在数学和计算机科学理论中，一个集的枚举是列出某些有穷序列集的所有成员的程序，或者是一种特定类型对象的计数。这两种类型经常（但不总是）重叠。枚举是一个被命名的整型常数的集合，枚举在日常生活中很常见，例如表示星期的SUNDAY、MONDAY、TUESDAY、WEDNESDAY、THURSDAY、FRIDAY、SATURDAY就是一个枚举。
    ```

> 枚举定义
  * 枚举类型是指由一组固定的常量组成的合法类型。Java中使用关键字enum来定义一个枚举类型，定义如下：
    ```
    public enum Season {
        SPRING,SUMMER,AUTUMN,WINER;
    }
    ```
  * 定义特点：
    * 使用关键字enum，声明类型名称，如Season；
    * 多个固定允许的值，代表枚举成员，如春夏秋冬四季的英文名称；
    * 可以定义在类级别也可嵌套在Java类中；
    * 可以定义新变量，新方法以及实现多个接口；

> 枚举常用方法
  * 常用方法API
  
    | 方法名称 | 描述 |
    | :---- | :---- |
    | values() | 以数组形式返回枚举类型的所有成员 |
    | valueOf() | 获取指定参数字符串的枚举成员实例 |
    | ordinal() | 获取枚举成员的索引位置 |
    | compareTo() | 比较枚举类型的两个成员在定义时的顺序，返回索引间的差值 |

  * 使用示例：
    ```
    // values()
    public enum ValuesMethod {
        //定义枚举成员
        MEMBER1,MEMBER2,MEMBER3;

        //定义调用示例方法
        public static void main(String[] args) {
            for (int i = 0; i < ValuesMethod.values().length; i++) {
                System.out.println("枚举成员：" + ValuesMethod.values()[i]);
            }
        } 
    }
    ```
    ```
    // valueOf()
    public enum ValueOfMethod {
        //定义枚举成员
        MEMBER1,MEMBER2,MEMBER3;

        //定义调用示例方法
        public static void main(String[] args) {
            ValueOfMethod member1 = ValueOfMethod.valueOf("MEMBER1");
            System.out.println("枚举成员：" + member1);
        } 
    }
    ```
    ```
    // ordinal()
    public enum OrdinalMethod {
        //定义枚举成员
        MEMBER1,MEMBER2,MEMBER3;

        //定义调用示例方法
        public static void main(String[] args) {
            ValueOfMethod member1 = ValueOfMethod.valueOf("MEMBER1");
            System.out.println("枚举成员：" + member1 + "的索引位置：" + member1.ordinal());
        } 
    }
    ```
    ```
    // compareTo()
    public enum CompareToMethod {
        //定义枚举成员
        MEMBER1,MEMBER2,MEMBER3;

        //定义调用示例方法
        public static void main(String[] args) {
            CompareToMethod member1 = CompareToMethod.valueOf("MEMBER1");
            CompareToMethod member2 = CompareToMethod.valueOf("MEMBER2");
            System.out.println(member1.compareTo(member2));
        } 
    }
    ```

> 枚举实践 
  * 规范的枚举类型
    ```
     // 定义枚举 
     public enum Season {
         //定义枚举成员并实例化
         SPRING(1),SUMMER(2),AUTUMN(3),WINTER(4);
         //定义新变量
         private int code;
         //定义新构造方法
         private Season(int code) {
             this.code = code;
         }
         //定义新方法
         public int getCode() {
             return this.code;
         }
     }
     // 定义传值类型为枚举类型的方法
     public String getChineseSeason(Season season) {
         StringBuffer result = new StringBuffer();
         switch(season) {
            case SPRING :
                 result.append("[中文：春天，枚举常量:" + season.name() + "，编码:" + season.getCode() + "]");
                 break;
            case SUMMER :
                 result.append("[中文：夏天，枚举常量:" + season.name() + "，编码:" + season.getCode() + "]");
                 break;
            case AUTUMN :
                 result.append("[中文：秋天，枚举常量:" + season.name() + "，编码:" + season.getCode() + "]");
                 break;
            case WINTER :
                 result.append("[中文：冬天，枚举常量:" + season.name() + "，编码:" + season.getCode() + "]");
                 break;
            default:
                result.append("地球上没有的季节 " + season.name());
                break;
         }
         return result.toString();
     }
     // 定义调用示例
    public void invokeDemo() {
        for (Season season : Season.values()) {
            System.out.println(getChineseSeason(season));
        }
        //System.out.println(getChineseSeason(5));
        //此处编译不通过，保证类型安全
    }
    ```
  * 枚举的单例实现
    * 饿汉式的单例
      ```
      // final不允许被继承
      public final class HungerSingleton {
          // 静态实例
          private static HungerSingleton instance = new HungerSingleton();
          // 私有构造方法不允许外部new
          private HungerSingleton() {}
          // 提供一个静态方法供外部获取单例
          public static HungerSingleton getInstance() {
              return instance;
          }
      }
      ```
    * 懒汉式的单例
      ```
      // final不允许被继承
      public final class DoubleCheckedSingleton {
          // 静态实例
          private static DoubleCheckedSingleton instance = new DoubleCheckedSingleton();
          // 私有构造方法不允许外部new
          private DoubleCheckedSingleton() {}
          // 提供一个静态方法供外部获取单例
          public static DoubleCheckedSingleton getInstance() {
              if (null == instance) {
                  synchronized (DoubleCheckedSingleton.class) {
                      if (null == instance) {
                          instance = new DoubleCheckedSingleton();
                      }
                  }
              }
              return instance;
          }
      }
      ```
    * 枚举的单例
      ```
      // final不允许被继承
      public final class EnumSingleton {
          // 私有构造方法不允许外部new
          private EnumSingleton() {}
          // 静态枚举构造单例
          private static enum SingletonFactory {
              //定义枚举成员 -单例枚举成员
              INSTANCE;
              //定义新变量 -单例对象
              private EnumSingleton enumSingleton;
              //定义新方法 -私有构造方法
              private SingletonFactory() {
                  enumSingleton = new EnumSingleton();
              }
              //定义新方法 -提供一个方法供外部获取单例
              public EnumSingleton getInstance() {
                  return enumSingleton;
              }
          }
          //提供一个静态方法供外部获取单例
          public static EnumSingleton getInstance() {
              return EnumSingleton.INSTANCE.getInstance();
          }
      }
      ```

> 面试相关
  * 枚举允许继承类？
    
    不允许，JVM在生成枚举时自动继承了Enum类，由于Java为单继承，故不再支持再继承额外的类。

  * 枚举允许被继承？

    不允许，JVM在生成枚举类时，声明为final。

  * 枚举可以用等号比较？
    
    可以，JVM会为每个枚举成员实例对应生成一个类对象，这个类对象是用public static final修饰的，在static代码块中初始化，是一个单例。

> 小结
  * 枚举类型一般用于枚举场景，比如switch，根据不同的枚举成员处理不同的业务逻辑；也适用于生成单例的场景。
  * 枚举成员常使用私有变量以及私有构造方法赋予成员属性。
  * 枚举成员对象是一个单例。

> 参考文献
  * [Java基础之Java枚举](https://juejin.im/post/6844904063935463437)