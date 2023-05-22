## 集成 JUnit5

> JUnit5 简介

* ```JUnit5```主要由三个不同子项目的几个不同模块组成：```JUnit Platform```、```JUnit Jupiter```、```JUnit Vintage```：
  
  * ```JUnit Platform```：它是在```JVM```上启动测试框架的基础，不仅支持```Junit```自制的测试引擎，其他测试引擎也都可以接入。
  * ```JUnit Jupiter```： 提供了```JUnit5```的新的编程模型，是```JUnit5```新特性的核心。内部包含了一个测试引擎，用于在```Junit Platform```上运行。
  * ```JUnit Vintage```: 由于```JUint```已发展多年，为兼容旧项目，```JUnit Vintage```提供了兼容```JUnit4.x```，```Junit3.x```的测试引擎。```SpringBoot 2.4```以上版本移除了默认对```JUnit Vintage```的依赖，若需兼容```JUnit4```需要自行引入：

    ```bash
    <dependency>
        <groupId>org.junit.vintage</groupId>
        <artifactId>junit-vintage-engine</artifactId>
        <scope>test</scope>
        <exclusions>
            <exclusion>
                <groupId>org.hamcrest</groupId>
                <artifactId>hamcrest-core</artifactId>
            </exclusion>
        </exclusions>
    </dependency>
    ```
 
> SpringBoot 使用 JUnit5

> JUnit5 常用测试注解

> JUnit5 新特性使用