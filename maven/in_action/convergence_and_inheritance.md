## Maven in action
#### 聚合与继承
> 聚合与继承
  * 概念
    * 随着应用程序复杂度逐渐提高，开发常使用分模块的方式降低程序复杂性，Maven项目在实际应用中也可划分模块，Maven利用能够将各模块聚合在一起构建的聚合特性和能够抽取各模块相同构建统一配置的继承特性实现项目模块化的功能。
  * 聚合
    * 通过创建一个打包方式为pom以及使用module元素声明任意数量模块的聚合模块来实现聚合。
      ```
      <?xml version="1.0" encoding="UTF-8"?>
      <project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

      <modelVersion>4.0.0</modelVersion>

      <groupId>com.garden</groupId>
      <artifactId>platform</artifactId>
      <version>1.0-SNAPSHOT</version>
      <packaging>pom</packaging>

      <name>platform</name>

      <modules>
        <!-- 相对于当前POM文件的各子模块的POM文件路径 -->
        <module>platform-dependency</module>
        <module>platform-register</module>
        <module>platform-business</module>
        <module>platform-banner</module>
        <module>platform-sdk</module>
      </modules>
      </project>
      ```
    * 聚合构建的原理
      * 首先解析聚合模块POM，分析要构建的模块，并计算出一个反应堆（所有模块组成的一个构建结构）构建顺序，然后根据这个顺序构建各个模块。
  * 继承
  * 聚合与继承的关系
  * 约定优于配置
  * 反应堆