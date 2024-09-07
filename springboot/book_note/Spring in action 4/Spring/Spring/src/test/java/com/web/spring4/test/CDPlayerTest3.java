package com.web.spring4.test;

import static org.junit.Assert.*;

import javax.annotation.Resource;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import com.web.spring4.bean.impl.CDPlayer;
import com.web.spring4.config.CDPlayerConfig;
import com.web.spring4.config.CDPlayerConfig2;
import com.web.spring4.config.SoudSystemConfig;
@RunWith(SpringJUnit4ClassRunner.class)
//@ContextConfiguration(classes=CDPlayerConfig2.class)
@ContextConfiguration(classes=SoudSystemConfig.class)
public class CDPlayerTest3 {

	@Resource
	private CDPlayer cdPlayer;
	
	@Test
	public void cdShouldNotBeNull4(){
		cdPlayer.play();
	}

}
