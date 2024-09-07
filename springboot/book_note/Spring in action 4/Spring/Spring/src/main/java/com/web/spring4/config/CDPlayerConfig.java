package com.web.spring4.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

import com.web.spring4.bean.impl.JayChouAlbum;
import com.web.spring4.bean.impl.JayChouAlbum2;
/**
 * 组件扫描配置
 * @author Garden
 * 2018年3月5日
 */
@Configuration
//@ComponentScan("com.web.spring4.bean")
//@ComponentScan("com.web.spring4.bean.impl")
//@ComponentScan(basePackages="com.web.spring4.bean.impl")
//@ComponentScan(basePackages={"com.web.spring4.bean.impl"})
//@ComponentScan(basePackageClasses={JayChouAlbum.class,JayChouAlbum2.class})
@ComponentScan(basePackageClasses={JayChouAlbum.class})
public class CDPlayerConfig {

}
