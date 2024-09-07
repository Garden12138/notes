package com.web.spring4.test;

import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.List;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import com.web.spring4.aspect.CDUtilAspect;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.impl.JayChouAlbum;
import com.web.spring4.config.CDConfig;
import com.web.spring4.utils.CDUtil;
/**
 * 面向切面编程测试
 * @author Garden
 * 2018年3月19日
 */
@RunWith(SpringJUnit4ClassRunner.class)
//@ContextConfiguration(classes=CDConfig.class)
@ContextConfiguration("classpath:/config.xml")
public class CDPlayerTest7 {
	
	@Autowired
	private CompactDisc jayChouAlbum;
	
	@Test
	public void cdShouldNotBeNull(){
//		jayChouAlbum.play();
		jayChouAlbum.audiencePlay("曾佳达",19);
	}
	
	@Test
	public void cdShouldNotBeNull1(){
		CDUtil cdUtil = (CDUtil)jayChouAlbum;
		cdUtil.addSongs();
	}
}
