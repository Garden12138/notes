package com.web.spring4.config;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.context.annotation.PropertySource;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.core.env.Environment;

import com.web.spring4.aspect.Audience;
import com.web.spring4.aspect.CDUtilAspect;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.impl.JayChouAlbum;
import com.web.spring4.bean.impl.JayChouAlbum3;

@Configuration
//@PropertySource("classpath:/data.properties")
@EnableAspectJAutoProxy
public class CDConfig {
	
//	@Autowired
//	private Environment env;
	
	@Bean
	public CompactDisc jayChouAlbum(){
		return new JayChouAlbum();
	}
	
//	@Bean
//	public CompactDisc jayChouAlbum3(){
//		return new JayChouAlbum3(env.getProperty("album.songs"),env.getProperty("album.artist"));
//	}
	
//	@Bean
//	public static PropertySourcesPlaceholderConfigurer placeholderCongigurer(){
//		return new PropertySourcesPlaceholderConfigurer();
//	}
	
//	@Bean
//	public CompactDisc jayChouAlbum3(@Value("${album.songs}") String songs
//			,@Value("${album.artist}") String artist){
//		return new JayChouAlbum3(songs,artist);
//	}
	
	@Bean
	public Audience audience(){
		return new Audience();
	}
	
	@Bean
	public CDUtilAspect cdUtilAspect(){
		return new CDUtilAspect();
	}
}
