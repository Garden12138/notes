package com.web.spring4.test;

import static org.junit.Assert.*;

import javax.annotation.Resource;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import com.web.spring4.bean.impl.*;
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(value = { "classpath:config.xml" })
public class CDPlayerTest2 {

//	@Resource
//	private JayChouAlbum jayChouAlbum;
	
//	@Resource
//	private CDPlayer cDPlayer;
	
//	@Resource
//	private JayChouAlbum3 jayChouAlbum3;
	
	@Resource
	private JayChouAlbum4 jayChouAlbum4;
	
//	@Resource
//	private CDPlayer2 cDPlayer2;
	
	/*基于XML装配Bean测试*/
	@Test
	public void cdShouldNotBeNull3(){
//		jayChouAlbum.play();
//		cDPlayer.play();
//		jayChouAlbum3.play();
		jayChouAlbum4.play();
//		cDPlayer2.play();
	}

}
