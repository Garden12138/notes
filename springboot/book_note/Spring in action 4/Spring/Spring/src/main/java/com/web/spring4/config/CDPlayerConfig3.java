package com.web.spring4.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.condition.ChooseJayChouAlbum;
import com.web.spring4.bean.impl.*;

/**
 * JavaConfig - 条件化装配Bean 
 * @author Garden
 * 2018年3月13日
 */
@Configuration
public class CDPlayerConfig3 {

	/*声明简单的bean*/
	@Bean
	@Conditional(ChooseJayChouAlbum.class)
	public  CompactDisc jayChouAlbum(){
		return new JayChouAlbum();
	}
	
	@Bean
	public  CompactDisc jayChouAlbum2(){
		return new JayChouAlbum2();
	}

}
