package com.web.spring4.test;
import static org.junit.Assert.*;
import javax.annotation.Resource;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import com.web.spring4.bean.impl.*;
import com.web.spring4.config.DataSourceConfig;
/***
 * Profile Bean测试
 * @author Garden
 * 2018年3月13日
 */
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes=DataSourceConfig.class)
//@ActiveProfiles("pro")
public class DataSourceConfigTest {

	@Autowired    /*顺序扫描*/
	private String dataSource;   
	
	@Test
	public void test(){
		System.out.println(dataSource.toString());
	}

}
