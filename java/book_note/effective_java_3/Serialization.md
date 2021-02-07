## EffectiveJava3

#### 序列化

> 优先选择 Java 序列化的替代方案

> 非常谨慎地实现 Serializable

> 考虑使用自定义的序列化形式

> 保护性的编写 readObject 方法

> 对于实例控制，枚举类型优于 readResolve

> 考虑用序列化代理代替序列化实例