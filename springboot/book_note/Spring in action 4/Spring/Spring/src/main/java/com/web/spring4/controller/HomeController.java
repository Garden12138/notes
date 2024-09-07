package com.web.spring4.controller;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.Errors;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import com.web.spring4.pojo.Data;
import com.web.spring4.repository.DataRepository;

/**
 * 主控制器
 * @author Garden
 * 2018年3月25日
 */
@Controller
@RequestMapping(value={"/home"})
public class HomeController {

	private DataRepository dataRepository;
	public DataRepository getDataRepository() {
		return dataRepository;
	}
	public void setDataRepository(DataRepository dataRepository) {
		this.dataRepository = dataRepository;
	}

	@RequestMapping(value={"/show"},method=RequestMethod.GET)
	public String showHomePage(Map model){
		model.put("params", new Data("","",""));
		return "home";
	}
	
	@RequestMapping(value={"/load"},method=RequestMethod.GET)
	public String loadHomePage(Map model,Model res,HttpServletRequest request){
		//model.put("data", dataRepository.findData(Long.MAX_VALUE, 20));
		List<Data> expectData = new ArrayList<Data>();
		for(long i = 0; i < 20; i++){
			expectData.add(new Data(String.valueOf(i),"data"+i,String.valueOf(new Date())));
		}
		//model.put("data", expectData);
		//res.addAttribute("data", expectData);
		request.setAttribute("data", expectData);
		//request.getSession().setAttribute("data", expectData);
		return "home";
	}
	
	@RequestMapping(value={"/getQueryParams"},method=RequestMethod.GET)
	public String getQueryParams(Map model,
			@RequestParam(value="max",defaultValue="20") long max,
			@RequestParam(value="count",defaultValue="20") int count){
		model.put("params","max="+max+"&"+"count="+count);
		return "home";
	}
	
	@RequestMapping(value={"/getPathParams/{max}/{count}"},method=RequestMethod.GET)
	public String getPathParams(Map model,
			@PathVariable long max,
			@PathVariable int count){
		model.put("params","max="+max+"&"+"count="+count);
		return "home";
	}
	
	@RequestMapping(value={"/getFormParams"},method=RequestMethod.POST)
	public String getFormParams(Map model,@Valid Data data,Errors errors){
		System.out.println(errors.hasErrors());
		if(errors.hasErrors()){
			System.out.print("----------");
			return "index";
		}
		model.put("params",data);
		return "home";
	}
	
	@RequestMapping(value={"/showFormbindtagRespo"},method=RequestMethod.GET)
	public String showFormBindTagRespoPage(Map model){
		model.put("params", new Data("","",""));
		return "formbindtagrespo";
	}
	
	@RequestMapping(value={"/getFormParamsByFormBindTagRespo"},method=RequestMethod.POST)
	public String getFormParamsByFormBindTagRespo(Map model,@Valid Data data,Errors errors){
		System.out.println(errors.hasErrors());
		if(errors.hasErrors()){
			System.out.print("----------");
			return "index";
		}
		model.put("params",data);
		return "formbindtagrespo";
	}
	
	@RequestMapping(value={"/showUniversalTagRespo"},method=RequestMethod.GET)
	public String showUniversalTagRespoPage(Map model){
		return "universaltagrespo";
	}
	
	@RequestMapping(value={"/showTestPage"},method=RequestMethod.GET)
	public String showTestPage(Map model){
		return "test";
	}
}
