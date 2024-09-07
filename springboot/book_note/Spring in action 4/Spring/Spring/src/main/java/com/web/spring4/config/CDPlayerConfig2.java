package com.web.spring4.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Profile;

import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.MediaPlayer;
import com.web.spring4.bean.impl.*;

/**
 * JavaConfig
 * @author Garden
 * 2018年3月6日
 * 基于Java配置装配Bean
 */
@Configuration
//@Import(CDConfig.class)
public class CDPlayerConfig2 {

	/*声明简单的bean*/
//	@Bean
//	public  CompactDisc jayChouAlbum(){
//		return new JayChouAlbum();
//	}
//	
//	@Bean
//	public  CompactDisc jayChouAlbum2(){
//		return new JayChouAlbum2();
//	}
	
	/*声明依赖关系的bean*/
//	@Bean
//	public CDPlayer cDPlayer(){
//		return new CDPlayer(jayChouAlbum());
//	}
	
	@Bean
	public CDPlayer cDPlayer(CompactDisc compactDisc){
		return new CDPlayer(compactDisc);
	}

}
