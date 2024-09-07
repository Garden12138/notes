package com.web.spring4.config;

import org.springframework.context.MessageSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.context.support.ReloadableResourceBundleMessageSource;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.config.annotation.DefaultServletHandlerConfigurer;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.view.InternalResourceViewResolver;
import org.springframework.web.servlet.view.tiles3.TilesConfigurer;
import org.springframework.web.servlet.view.tiles3.TilesViewResolver;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.spring3.SpringTemplateEngine;
import org.thymeleaf.spring3.view.ThymeleafViewResolver;
import org.thymeleaf.templateresolver.ServletContextTemplateResolver;
import org.thymeleaf.templateresolver.TemplateResolver;

/**
 * web组件配置类
 * @author Garden
 * 2018年3月25日
 */
@Configuration
@EnableWebMvc    /*启用Spring MVC*/
@Import(ControllerConfig.class)    /*启动组件扫描，
                                                                            主要扫描控制器以及其他组件*/
public class WebConfig extends WebMvcConfigurerAdapter{    /*继承抽象类，
                                                                                                                              实现配置默认servlet拦截方法*/
//	@Bean
//	public ViewResolver viewResolver(){    /*配置JSP视图解析器*/
//		InternalResourceViewResolver resolver = new InternalResourceViewResolver();
//		resolver.setPrefix("/WEB-INF/jsp/");
//		resolver.setSuffix(".jsp");
//		resolver.setExposeContextBeansAsAttributes(true);
//		resolver.setViewClass(org.springframework.web.servlet
//				.view.JstlView.class);    /*设置返回View为JSTLView*/ 
//		return resolver;
//	}
	
//	@Bean
//	public ViewResolver viewResolver(){    /*配置Tiles视图解析器*/
//		return new TilesViewResolver();
//	}
//	
//	@Bean
//	public TilesConfigurer tilesConfigurer(){    /*配置解析tiles定义*/
//		TilesConfigurer tiles = new TilesConfigurer();
//		tiles.setDefinitions(new String[]{
//				"WEB-INF/layout/tiles.xml"
//		});
//		tiles.setCheckRefresh(true);
//		return tiles;
//	}
	
	  @Bean
	  public ViewResolver viewResolver(
			  SpringTemplateEngine templateEngine) {    /*配置Thymeleaf视图解析器*/
	    ThymeleafViewResolver viewResolver = new ThymeleafViewResolver();
	    viewResolver.setTemplateEngine(templateEngine);
	    viewResolver.setCharacterEncoding("utf-8");
	    return viewResolver;
	  }
	  
	  @Bean
	  public SpringTemplateEngine templateEngine(
			  TemplateResolver templateResolver) {    /*配置模板引擎*/
	    SpringTemplateEngine templateEngine = new SpringTemplateEngine();
	    templateEngine.setTemplateResolver(templateResolver);
	    return templateEngine;
	  }

	  @Bean
	  public TemplateResolver templateResolver() {    /*配置模板解析器*/
		  TemplateResolver templateResolver = 
				new ServletContextTemplateResolver();
	    templateResolver.setPrefix("/WEB-INF/html/");
	    templateResolver.setSuffix(".html");
	    templateResolver.setTemplateMode("HTML5");
	    templateResolver.setCharacterEncoding("utf-8");
	    return templateResolver;
	  }
	
	@Override
	public void configureDefaultServletHandling(
			DefaultServletHandlerConfigurer configurer) {    /*配置静态资源的处理，
			                                                                                                         将静态资源的请求转移至默认servlet*/
		configurer.enable();
	}
	
	@Bean
	public MessageSource messageSource(){    /*国际化信息配置*/
		ReloadableResourceBundleMessageSource messageSource = 
				new ReloadableResourceBundleMessageSource();
		messageSource.setBasename("classpath:/language");
		messageSource.setCacheSeconds(10);
		return messageSource;
	}
}
