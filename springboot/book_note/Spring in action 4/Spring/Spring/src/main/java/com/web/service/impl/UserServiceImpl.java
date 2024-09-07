package com.web.service.impl;

import javax.annotation.Resource;

import org.springframework.stereotype.Service;

import com.web.service.UserService;
import com.web.dao.*;
@Service
public class UserServiceImpl implements UserService{

	@Resource
	private UserEntityDao UserEntityDao;

	@Override
	public void addUser(String username, String password) {
		// TODO Auto-generated method stub
		UserEntityDao.addUser(username, password);
	}
	
}
