package com.web.controller;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class TestController {
	
	@Autowired
	private String dataSource;
	
	@RequestMapping(value="/test")
	public String test(HttpServletRequest request,HttpServletResponse response){
		System.out.println("--------------");
		System.out.println(dataSource.toString());
		return "index";
	}
}
