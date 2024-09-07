package com.web.spring4.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration
public class DataSourceConfig {
	
	@Bean(name = "DataSource")
	@Profile("pro")
	public String proDataSource(){
		return "pro-dataSource";
	}
	
	@Bean(name = "DataSource")
	@Profile("dev")
	public String devDataSource(){
		return "dev-dataSource";
	}
	
}
