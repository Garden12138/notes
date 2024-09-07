package com.web.spring4.repository;

import java.util.List;

import com.web.spring4.pojo.Data;

public interface DataRepository {
	
	List<Data> findData(long max,int count);
	
}
