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
