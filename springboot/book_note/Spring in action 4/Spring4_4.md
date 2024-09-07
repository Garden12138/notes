# Spring4

## 面向切面编程

#### 了解面向切面编程

* 横切关注点：影响应用多处的功能，如日志，事务，安全功能。
* 切面：横切关注点可以被模块化为特殊的类，这些类称为切面。
* 面向切面编程：将业务关注点与其他必须关注点隔离，使业务模块能够更专心的处理本身核心业务，不必关注非核心业务
的编程方式。
* 面向切面（AOP）术语：
  * 连接点（Join point）：应用程序执行过程中能够插入切面的一个点。
  * 切点（Pointcut）:匹配通知所要织入的一个或多个连接点。
  * 通知（Advice）：描述切面所要完成的工作以及何时工作。
  * 切面（Aspect）：切点和通知的结合。
  * 引入（Introduction）：向现有类添加新属性以及方法。
  * 织入（Weaving）：将切面应用到目标对象并创建新的代理对象的过程。
* Spring对AOP的支持
  * 基于代理的经典Spring AOP（使用注解）
  * 纯POJO切面（使用XML）
  * @AspectJ注解驱动的切面
  * 注入式AspectJ切面
  * PS：
    * Spring在运行时通知对象，运行期把切面织入到Spring管理的bean中，代理类封装了目标类，并拦截被通知方法的调用，先执行切面逻辑，再把调用转发到真正的bean。
    * Spring AOP只支持方法级别的连接点，AspsctJ和JBoss除了支持方法级别的连接点还提供属性以及构造器连接点。
* 切点指示器
  * arg()：限制连接点匹配参数为指定类型的执行方法
  * @args()：限制连接点匹配参数由指定注解标注的执行方法
  * execution()：用于匹配是连接点的执行方法
  * this()：限制连接点匹配AOP代理的bean引用为指定类型的类
  * target()：限制连接点匹配目标对象为指定类型的类
  * @Target()：限制连接点匹配特定的执行对象，这些对象对应的类要具有指定类型的注解
  * within()：限制连接点匹配指定的类型
  * @within()：限制连接点匹配指定注解所标注的类型
  * @annotation：限制匹配带有指定注解的连接点
  * bean()

* 切点表达式
  * execution(* 全限定类名.方法名(..) )
  * *号代表返回类型，..代表任意参数

#### 使用注解创建切面

* 定义切面：使用注解@Aspect声明切面，@Pointcut声明切点，@Before(前置通知)、@After(后置通知)、@AfterReturning(返回通知)、@AfterThrowing(异常通知)、@Around(环绕通知)声明通知。

```
package com.web.spring4.aspect;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.AfterThrowing;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.aspectj.lang.annotation.Pointcut;
@Aspect    /*声明切面*/  
public class Audience {

	@Pointcut("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	public void play(){

	}

	@Pointcut("execution(** com.web.spring4.bean.impl.JayChouAlbum.audiencePlay(String,int)) "
			+ "&& args(audienceName,age)")
	public void audiencePlay(String audienceName,int age){

	}

	/*声明通知，切点表达式声明切点*/
	//前置通知
//	@Before("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	@Before("play()")
	public void openCDPlayer(){
		System.out.println("CDPlayer opening...");
	}

//	@Before("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	@Before("play()")
	public void putCDIntoPlayer(){
		System.out.println("putting CD into CDPlayer");
	}
//	@Before("audiencePlay(audienceName,age)")
//	@Before(value="audiencePlay(audienceName,age)")
//	@Before(value="audiencePlay(audienceName,age)",argNames="audienceName,age")
//	public void putCDIntoPlayer(String audienceName,int age){
//		System.out.println(age+ "岁的"+ audienceName +"putting CD into CDPlayer");
//	}

	//返回通知
//	@AfterReturning("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	@AfterReturning("play()")
	public void praise(){
		System.out.print("this song sound good,qwq");
	}

	//异常通知
//	@AfterThrowing("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	@AfterThrowing("play()")
	public void makeComplaints(){
		System.out.println("this song is suck,:)");
	}

	//环绕通知
	@Around("play()")
	public void action(ProceedingJoinPoint jp){
		try{
			System.out.println("CDPlayer opening...");
			System.out.println("putting CD into CDPlayer");
			jp.proceed();
			System.out.print("this song sound good,qwq");
		}catch(Throwable e){
			System.out.println("this song is suck,:)");
		}
	}
//	@Around(value="audiencePlay(audienceName,age)",argNames="audienceName,age")
//	public void action(String audienceName,int age,ProceedingJoinPoint jp){
//		try{
//			System.out.println("CDPlayer opening...");
//			System.out.println("putting CD into CDPlayer");
//			jp.proceed();
//			System.out.print("this song sound good,qwq");
//		}catch(Throwable e){
//			System.out.println("this song is suck,:)");
//		}
//	}
}

```

* 声明切面为bean：建议使用JavaConfig
* 启动AspectJ自动代理：使用@EnableAspectJAutoProxy启动AspectJ自动代理

```
package com.web.spring4.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import com.web.spring4.aspect.Audience;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.impl.JayChouAlbum;
@Configuration
@EnableAspectJAutoProxy
public class CDConfig {

	@Bean
	public CompactDisc jayChouAlbum(){
		return new JayChouAlbum();
	}

	@Bean
	public Audience audience(){
		return new Audience();
	}
}
```


#### 使用XML创建切面

* 声明切面：使用元素< aop:config >声明AOP配置，< aop:aspect >声明切面，< aop:pointcut >声明切点，< aop:before >(前置)、< aop:after >(后置)、< aop:after-returning >(返回)、< aop:after-throwing >(异常)、< aop:around >(环绕)声明通知。

```
<aop:config>
    <aop:aspect ref="audience">
    <aop:pointcut expression="execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))"
                  id="play"/>
    <aop:pointcut expression=
    "execution(** com.web.spring4.bean.impl.JayChouAlbum.audiencePlay(String,int))
                              and args(audienceName,age)" id="audiencePlay"/>
        <aop:before pointcut-ref="play" method="openCDPlayer"/>
        <aop:before pointcut-ref="play" method="putCDIntoPlayer"/>
        <aop:after-returning pointcut-ref="play" method="praise"/>
        <aop:after-throwing pointcut-ref="play" method="makeComplaints"/>
        <aop:around pointcut-ref="play" method="action"/>
        <!-- <aop:before pointcut-ref="audiencePlay" method="putCDIntoPlayer"/> -->
    </aop:aspect>
</aop:config>
```

* 声明切面为bean
* 启动AspectJ自动代理：使用元素< aop:aspectj-autoproxy >启动AspectJ自动代理

```
<aop:aspectj-autoproxy />
<bean id="audience" class="com.web.spring4.aspect.Audience" />
```

#### 利用AOP为现有类添加新功能

* 原理：Spring在创建带有@Aspect的bean的时候会创建一个代理类，当调用者（实例化对象）调用被通知方法时，代理先拦截调用，先进行代理逻辑再调用被通知方法。故可以利用AOP引入新接口以及其实现的代理，即引入代理是现有代理的子类，调用时直接进行强制类型转换，调用被引入的新方法。
[![微信图片_20180320202646.png](https://i.loli.net/2018/03/20/5ab0fe1848b13.png)](https://i.loli.net/2018/03/20/5ab0fe1848b13.png)

* 代码实现

```
-- java
package com.web.spring4.aspect;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.DeclareParents;
import com.web.spring4.utils.CDUtil;
import com.web.spring4.utils.impl.CDUtilImpl;
/**
* CD工具类切面
* @author Garden
* 2018年3月19日
*/
@Aspect
public class CDUtilAspect {
@DeclareParents(value="com.web.spring4.bean.CompactDisc+",defaultImpl=CDUtilImpl.class)
public static CDUtil cdUtil;
}

-- xml
<bean id="CDUtilImpl" class="com.web.spring4.utils.impl.CDUtilImpl"/>
<aop:config>
    <aop:aspect>
        <aop:declare-parents types-matching="com.web.spring4.bean.CompactDisc+"
                             implement-interface="com.web.spring4.utils.CDUtil"
                             delegate-ref="CDUtilImpl"/>
    </aop:aspect>
</aop:config>
```

```
-- java
@Bean
public CDUtilAspect cdUtilAspect(){
  return new CDUtilAspect();
}

-- xml
<bean id="CDUtilAspect" class="com.web.spring4.aspect.CDUtilAspect"/>
```

```
@Test
public void cdShouldNotBeNull1(){
  CDUtil cdUtil = (CDUtil)jayChouAlbum;
  cdUtil.addSongs();
}
```
