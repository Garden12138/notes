# Spring4

## Spring Web Flow

#### Spring Web Flow概况

* 适用背景：web应用程序逐渐面向用户，控制用户的方向，遵循流程并引导他们一步步地访问应用程序。故基于流程的开发的技术逐渐发展。Spring Web Flow 是Spring MVC的扩展，支持开发基于流程的应用程序（如外卖订单应用程序）。

* 了解流程
  * 流程的组件：流程由三大主要元素定义的：状态，转移和流程数据。
    * 状态：流程中事件发生的地点
      * 视图状态：暂停流程并邀请用户参与流程，即为用户展示视图。流程定义XML文件里定义视图状态如下：
      ```
      <!-- 简单定义视图状态，视图名为id -->
      <view-state id="welcome" />
      ```
      ```
      <!-- 指定视图名定义视图状态 -->
      <view-state id="welcome" view="greeting" />
      ```
      ```
      <!-- 表单绑定对象定义视图状态 -->
      <view-state id="welcome" model="flowScope.paymentDetails" />
      ```
      * 行为状态：逻辑发生的地方，一般会触发Spring所管理bean的一些方法并根据方法调用的执行结果转移至另一个状态。
      ```
      <action-state id="saveOrder">
          <!-- expression属性为SpEl表达式，值为bean的方法。可以使用result属性表示方法调用的执行结果 -->
          <evaluate expression="pizzaFlowAction.saveOrder(order)" />
          <!-- 转移至状态id为thankYou状态 -->
          <transition to="thankYou" />
      </action-state>
      ```
      * 决策状态：将流程分成两个方向，基于流程数据的评估（评估一个Boolean类型的表达式）结果确定流程的方向。      
      ```
      <decision-state id="checkDeliverytArea">、
      <!-- test属性为SpEl表达式，值为bean的返回类型为Boolean的方法，then与else属性为下一个状态ID -->
          <if test="pizzaFlowAction.checkDeliverytArea(customer.zipCode)"
              then="addCustomer"
              else="checkDeliverytArea"/>
      </decision-state>
      ```
      * 子流程状态：在当前正在运行的流程上下文中启动一个新的流程。
      ```
      <!-- subflow属性为子流程定义文件 -->
      <subflow-state id="order" subflow="pizza/order">
          <!-- 子流程的输入 -->
          <input name="order" value="order" />
          <!-- on属性表示子流程结束状态 -->
          <transition on="orderCreated" to="payment" />
      </subflow-state>
      ```
      * 结束状态：终止流程的状态。
      ```
      <!-- 简单的结束状态 -->
      <end-state id="customerReady" />
      ```
      ```
      <!-- 指定视图的结束状态。添加"externalRedirect:"前缀，重定向至外部页面；添加"flowRedirect:"前缀，重定向至另一个流程 -->
      <end-state id="customerReady" view="" />
      ```
    * 转移：用于链接状态，将一个状态转移至另一个状态
    ```
    <!-- 当前状态的默认转移选项 -->
    <transition to="customerReady" />
    ```
    ```
    <!-- 基于事件触发的转移选项，on属性指定触发转移的事件 -->
    <transition on="phoneEntered" to="lookupCustomer" />
    ```
    ```
    <!-- 基于异常抛出的转移选项 -->
    <transition on-exception="com.springinaction.pizza.service.CustomerNotFoundException" to="registrationForm" />
    ```
    ```
    <!-- 全局转移,整个流程多个状态中都可以复用的转移 -->
    <global-transition>
        <transition on="cancel" to="endState" />
    </global-transition>
    ```
    * 流程数据：表明流程当前的状态。流程数据保存在变量中，变量可以在流程的各个地方进行引用。
      * 使用< var >元素声明变量。变量作用域始终为Flow。
      ```
      <var name="customer" class="com.springinaction.pizza.domain.Customer" />
      ```
      * 使用< evaluate >元素声明变量，一般用于行为状态或视图状态。变量作用域可自定义。
      ```
      <evaluate result="viewScope.toppingList" expression="T(com.springinaction.pizza.domain.Topping).asList()" />
      ```
      * 使用< set >元素声明变量
      ```
      <set name="flowScope.pizza" value="new com.springinaction.pizza.domain.Pizza()" />
      ```
      * 定义流程数据的作用域。变量作用域可自定义。
        * Conversation：最高层级的流程开始时创建，于最高层级的流程结束时销毁。被最高层级的流程和其所有的子流程所共享。
        * Flow：流程开始时创建，于流程结束时销毁。只有在创建它的流程中是可见的。
        * Request：当一个请求进入流程时创建，于流程返回时销毁。
        * Flash：流程开始时创建，于流程结束时销毁。在视图状态渲染后也会销毁。
        * View：进入视图状态是创建，于退出视图状态时销毁。只有视图状态内是可见的。

#### 配置Spring Web Flow

* Spring Web Flow构建于Spring MVC基础之上，故需在Spring应用上下文中配置bean来处理流程请求并执行流程。因Spring Web Flow目前不支持JavaConfig，故只能基于XML配置。
* 步骤：
  * 于定义Spring应用上下文配置文件声明Spring Web Flow命名空间
  ```
  <?xml version="1.0" encoding="UTF-8"?>
  <beans xmlns="http://www.springframework.org/schema/beans"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xmlns:flow="http://www.springframework.org/schema/webflow-config"
   xmlns:p="http://www.springframework.org/schema/p"
   xmlns:context="http://www.springframework.org/schema/context"
   xsi:schemaLocation="http://www.springframework.org/schema/webflow-config
   http://www.springframework.org/schema/webflow-config/spring-webflow-config-2.3.xsd
   http://www.springframework.org/schema/beans
   http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
   http://www.springframework.org/schema/context
   http://www.springframework.org/schema/context/spring-context-3.0.xsd">
  ```
  * 装配流程执行器：流程执行器，驱动流程的执行。当用户进入一个流程石，流程执行器为用户创建并启动一个流程执行实例。
  ```
  <flow:flow-executor id="flowExecutor" />
  ```
  * 配置流程注册表：流程注册表，加载流程定义并让流程执行器能够使用他们。
  ```
  <flow:flow-registry id="flowRegistry" base-path="/WEB-INF/flows">
      <flow:flow-location-pattern value="/**/*-flow.xml" />
  </flow:flow-registry>
  ```
  * 配置流程请求处理：FlowHandlerMapping帮助DispatcherServlet将请求发送至Spring Web Flow
  ```
  <bean class="org.springframework.webflow.mvc.servlet.FlowHandlerMapping">
      <property name="flowRegistry" ref="flowRegistry" />
  </bean>
  ```
  * 配置流程响应处理：FlowHandlerAdapter，响应发送的流程请求并对其进行处理。
  ```
  <bean class="org.springframework.webflow.mvc.servlet.FlowHandlerAdapter">
      <property name="flowExecutor" ref="flowExecutor" />
  </bean>
  ```
* [具体Demo参考](https://github.com/Garden12138/Spring4/tree/master/spring-single-demo/SpringPizza)
