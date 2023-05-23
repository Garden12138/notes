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
  
* 引入依赖：

  ```bash
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
  </dependency>
  ```

  ```spring-boot-starter-test```依赖默认集成```JUnit Jupiter```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-22_17-21-27.png)

* 单元测试：
  
  * 对需进行单元测试的服务类使用快捷键```shift + ctrl + t```，创建单元测试类：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-22_17-25-44.png)

  * 单元测试类添加```@SpringBootTest```注解，依赖注入服务类的```bean```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-22_17-33-41.png)

  * 使用注解```@Test```注解声明测试方法，编写测试逻辑后执行测试：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-22_17-34-34.png) 

> JUnit5 常用测试注解

* ```@DisplayName```注解，为测试类或测试方法定义客户端展示名称：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_14-41-37.png)

* ```@Disabled```注解，令测试类或测试方法不可用：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_14-44-53.png)

* ```@BeforeAll```注解，在当前测试类所有测试方法执行前会优先执行，修饰方法必须为静态：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_14-54-57.png)

* ```@BeforeEach```注解，在当前测试类每个测试方法执行前会优先执行：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_14-58-05.png)

* ```@AfterAll```注解，在当前测试类所有测试方法执行后再执行，修饰方法必须为静态：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_15-07-18.png)

* ```AfterEach```注解，在当前测试类每个测试方法执行后再执行：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-23_15-20-13.png) 

> JUnit5 新特性使用