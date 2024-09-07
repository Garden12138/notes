package com.web.entity.test;

import static org.junit.Assert.*;

import javax.annotation.Resource;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import com.web.service.*;
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(value = { "classpath:SpringMVC.xml", "classpath:/SpringDataSource.xml" })
public class UserEntityUnit {

	@Resource
	private UserService UserService;
	
	@Test
	public void test() {
		System.out.println("JUnit Test");
	}
	
	@Test
	public void addUserTest(){
		String username = "曾佳达";
		String password = "123456";
		UserService.addUser(username, password);
	}
}
