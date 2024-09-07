package com.web.spring4.config;

import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;
/**
 * Web应用初始类
 * @author Garden
 * 2018年3月25日
 */
public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer{

	/*加载ContextLoaderListener 数据层组件（bean，数据源等）*/
	@Override
	protected Class<?>[] getRootConfigClasses() {
		// TODO Auto-generated method stub
		return new Class<?>[] {RootConfig.class};
	}

	/*加载DispatcherServlet web组件（bean，映射处理器，控制器，视图解析器）*/
	@Override
	protected Class<?>[] getServletConfigClasses() {
		// TODO Auto-generated method stub
		return new Class<?>[] {WebConfig.class};
	}

	/*将DispatcherServlet映射到'/'*/
	@Override
	protected String[] getServletMappings() {
		// TODO Auto-generated method stub
		return new String[] {"/"};
	}

}
