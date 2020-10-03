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
    # values()
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
    # valueOf()
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
    # ordinal()
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
    # compareTo()
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

> 面试相关