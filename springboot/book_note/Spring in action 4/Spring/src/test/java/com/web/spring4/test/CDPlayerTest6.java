package com.web.spring4.test;

import static org.junit.Assert.*;

import javax.annotation.Resource;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.MediaPlayer;
import com.web.spring4.bean.impl.JayChouAlbum;
import com.web.spring4.bean.impl.JayChouAlbum2;
import com.web.spring4.config.CDConfig;
import com.web.spring4.config.CDPlayerConfig;
import com.web.spring4.config.CDPlayerConfig2;
import com.web.spring4.config.CDPlayerConfig3;
import com.web.spring4.bean.impl.*;

@RunWith(SpringJUnit4ClassRunner.class)
//@ContextConfiguration(classes=CDConfig.class)
@ContextConfiguration("classpath:/config.xml")
public class CDPlayerTest6 {
	
	@Autowired
	private JayChouAlbum3 jayChouAlum3;
	
	@Autowired
	private JayChouAlbum4 jayChouAlbum4;
	
	@Test
	public void cdShouldNotBeNull(){
		jayChouAlum3.play();
		jayChouAlbum4.play();
	}

}
