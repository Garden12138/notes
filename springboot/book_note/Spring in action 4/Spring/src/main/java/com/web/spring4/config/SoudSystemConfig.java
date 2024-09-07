package com.web.spring4.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.ImportResource;

@Configuration
//@Import({CDConfig.class,CDPlayerConfig2.class})
@Import(CDPlayerConfig2.class)
@ImportResource("classpath:config.xml")
public class SoudSystemConfig {

}
