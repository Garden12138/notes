package com.web.spring4.test;

import static org.junit.Assert.*;

import javax.annotation.Resource;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.MediaPlayer;
import com.web.spring4.bean.impl.JayChouAlbum;
import com.web.spring4.bean.impl.JayChouAlbum2;
import com.web.spring4.config.CDPlayerConfig;
import com.web.spring4.config.CDPlayerConfig2;
import com.web.spring4.bean.impl.*;
@RunWith(SpringJUnit4ClassRunner.class)
//@ContextConfiguration(classes=CDPlayerConfig.class)
//@ContextConfiguration(value = { "classpath:config.xml" })
@ContextConfiguration(classes=CDPlayerConfig2.class)
public class CDPlayerTest {
	
//	@Resource
//	private CompactDisc cd;

	@Resource
	private JayChouAlbum cd1;
	
	@Resource
	private JayChouAlbum2 cd2;
	
	@Resource
//	private MediaPlayer CDPlayer;
	private CDPlayer CDPlayer;
	
	/*自动化装配Bean测试*/
	@Test
	public void cdShouldNotBeNull(){
		//assertNotNull(cd);
		assertNotNull(cd1);
		cd1.play();
		assertNotNull(cd2);
		cd2.play();
		System.out.println("---end--");
		CDPlayer.play();
	}
	
	/*基于Java装配Bean测试*/
	@Test
	public void cdShouldNotBeNull2(){
		assertNotNull(cd1);
		cd1.play();
		assertNotNull(cd2);
		cd2.play();
		CDPlayer.play();
	}

}
