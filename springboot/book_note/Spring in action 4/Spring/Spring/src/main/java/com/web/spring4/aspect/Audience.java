package com.web.spring4.aspect;


import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.AfterThrowing;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.aspectj.lang.annotation.Pointcut;

/**
 * 切面：观众类
 * @author Garden
 * 2018年3月19日
 */
//@Aspect    /*声明切面*/  
public class Audience {
	
//	@Pointcut("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
	public void play(){
		
	}
	
//	@Pointcut("execution(** com.web.spring4.bean.impl.JayChouAlbum.audiencePlay(String,int)) "
//			+ "&& args(audienceName,age)")
	public void audiencePlay(String audienceName,int age){
		
	}
	
	/*声明通知，切点表达式声明切点*/
	//前置通知
//	@Before("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
//	@Before("play()")
	public void openCDPlayer(){
		System.out.println("CDPlayer opening...");
	}
	
//	@Before("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
//	@Before("play()")
//	public void putCDIntoPlayer(){
//		System.out.println("putting CD into CDPlayer");
//	}
//	@Before("audiencePlay(audienceName,age)")
//	@Before(value="audiencePlay(audienceName,age)")
//	@Before(value="audiencePlay(audienceName,age)",argNames="audienceName,age")
	public void putCDIntoPlayer(String audienceName,int age){
		System.out.println(age+ "岁的"+ audienceName +"putting CD into CDPlayer");
	}
	
	//返回通知
//	@AfterReturning("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
//	@AfterReturning("play()")
	public void praise(){
		System.out.print("this song sound good,qwq");
	}
	
	//异常通知
//	@AfterThrowing("execution(** com.web.spring4.bean.impl.JayChouAlbum.play(..))")
//	@AfterThrowing("play()")
	public void makeComplaints(){
		System.out.println("this song is suck,:)");
	}
	
	//环绕通知
//	@Around("play()")
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
