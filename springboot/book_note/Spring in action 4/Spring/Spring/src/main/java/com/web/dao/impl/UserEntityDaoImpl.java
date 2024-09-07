package com.web.dao.impl;

import java.util.ArrayList;
import java.util.List;

import javax.annotation.Resource;

import org.hibernate.SessionFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import com.web.dao.UserEntityDao;

@Repository
public class UserEntityDaoImpl implements UserEntityDao{
	
	@Resource(name="jdbcTemplate")
	private JdbcTemplate jdbcTemplate;
	
	@Autowired
	SessionFactory sessionFactory;

	@Override
	public void addUser(String username, String password) {
		// TODO Auto-generated method stub
		List<Object[]> batchArgs=new ArrayList<Object[]>();
		batchArgs.add(new Object[]{"1",username,password});
		String sql = "insert into tb_user (f_id,f_username,f_password) values(?,?,?)";
		jdbcTemplate.batchUpdate(sql, batchArgs);
	}
}
