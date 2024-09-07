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
import com.web.spring4.config.CDPlayerConfig3;
import com.web.spring4.bean.impl.*;
/***
 * 条件化装配Bean测试
 * @author Garden
 * 2018年3月13日
 */
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes=CDPlayerConfig3.class)
public class CDPlayerTest5 {
	
//	@Resource
//	private JayChouAlbum jayChouAlbum;
	
	@Resource
	private JayChouAlbum2 jayChouAlbum2;
	
	/*自动化装配Bean测试*/
	@Test
	public void cdShouldNotBeNull(){
//		jayChouAlbum.play();
		jayChouAlbum2.play();
	}

}
