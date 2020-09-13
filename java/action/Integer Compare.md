## 包装整型Integer的值比较方式

> 等值符号 ==

* 适用场景
  ```
  #非实例化构造且比较值于 -128 ～ 127 之间

  #example:
    Integer i1 = 127;
    Integer i2 = 127;
    System.out.println(i1 == i2);
    Integer i3 = 128;
    Integer i4 = 128;
    System.out.println(i3 == i4);
  #console:
    true
    false
  ```
* 解释
  ```
  #整型int向其包装类型Integer装箱时，即调用Intger.valueOf(int i)，会优先判断整型数值是否在缓存池区间内，若是则直接返回，否则使用构造方法构建Intger。从缓存池取出的对象相同，数值相等。

  //编译为字节码（.class）后，编码代码：
  Integer integer1 = Integer.valueOf(127);
  Integer integer2 = Integer.valueOf(127);
  System.out.println((integer1 == integer2));
  Integer integer3 = Integer.valueOf(128);
  Integer integer4 = Integer.valueOf(128);
  System.out.println((integer3 == integer4));

  //Intger.valueOf(int i)实现：
  public static Integer valueOf(int i) {
    if (i >= IntegerCache.low && i <= IntegerCache.high)
        return IntegerCache.cache[i + (-IntegerCache.low)];
    return new Integer(i);
  }
  ```

> equals
  * 适用场景
    ```
    #所有整型包装类对象之间值的比较，都可以使用 equals 方法比较
    
    #example：
      Integer i1 = new Integer(128);
      Integer i2 = new Integer(128);
      System.out.println((i1.equals(i2)));
      Integer i3 = 128;
      Integer i4 = 128;
      System.out.println((i3.equals(i4)));
    #console：
      true
      true
    ```

> compareTo
  * 适用场景
    ```
    #所有整型包装类对象之间值的比较，都可以使用 compareTo 方法比较，Integer类实现Comparable接口

    #example：
      Integer i1 = new Integer(128);
      Integer i2 = new Integer(128);
      System.out.println((i1.compareTo(i2)));
    #console：
      0
    ```
  * 解释
    ```
    # 调用compareTo方法后返回值分别为-1，0，1，-1表示前者（即调用者）小于后者，0表示前者等于后者，1表示前者大于后者

    //compareTo源码：
    public int compareTo(Integer anotherInteger) {
        return compare(this.value, anotherInteger.value);
    }
    public static int compare(int x, int y) {
        return (x < y) ? -1 : ((x == y) ? 0 : 1);
    }
    ```

> 直接运算
  * 适用场景
    ```
    #所有整型包装类对象之间值的比较，都可以使用运算符 - 进行减法运算比较

    #example：
      Integer i1 = new Integer(128);
      Integer i2 = new Integer(128);
      System.out.println((i1 - i2) == 0);
    #console：
      true
    ```
  * 解释
    ```
    #包装类对象之间的运算时，优先自动拆箱再做运算，若运算结果为0，则两者值相等
    ```

> intValue
  * 适用场景
    ```
    #所有整型包装类对象之间值的比较，都可以使用 intValue 获取int值进行比较

    #example：
      Integer i1 = new Integer(128);
      Integer i2 = new Integer(128);
      System.out.println(i1.intValue() == i2.intValue());
    #console
      true
    ```

> 异或
  * 适用场景
    ```
    #所有整型包装类对象之间值的比较，都可以使用异或逻辑运算结果进行比较

    #example：
      Integer i1 = new Integer(128);
      Integer i2 = new Integer(128);
      System.out.println((i1 ^ i2) == 0);
    #console：
      true
    ```
  * 解释
    ```
    #异或是一个数学逻辑运算，若两个值相同，异或结果为0，若两个值不相同则异或结果为1，比如：1异或0结果为1，1异或1结果为0
    ```

> 小结
  * 最常使用的比较方式为equals，intValue，异或运算，compareTo以及直接运算，==比较方式只适用于非实例化构造且值于 -128 ～ 127 之间的比较。