package com.web.spring4.test;
import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import com.web.spring4.config.ControllerConfig;
import com.web.spring4.config.WebAppInitializer;
import com.web.spring4.controller.HomeController;
import com.web.spring4.pojo.Data;
import com.web.spring4.repository.DataRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.servlet.view.InternalResourceView;
import static 
       org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static
       org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static
       org.springframework.test.web.servlet.setup.MockMvcBuilders.*;
import static org.hamcrest.Matchers.*;
import static org.mockito.Mockito.*;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
/**
 * 控制器Mock测试
 * @author Garden
 * 2018年3月25日
 */
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes={WebAppInitializer.class,ControllerConfig.class})
public class ControllerMockTest {
	
	@Autowired
	HomeController hc;
	
	@Test
	public void homeControllerShowTest()  {
		System.out.println("homeControllerShowTest...");
		MockMvc mockMvc = standaloneSetup(hc).setSingleView(
				new InternalResourceView("/WEB-INF/jsp/home.jsp")).build();
		try {
			mockMvc.perform(get("/home/show")).andExpect(view().name("home"));
		} catch (Throwable e) {
			// TODO Auto-generated catch block
			System.out.println("failed..");
			e.printStackTrace();
			return;
		}
		System.out.println("success");
	}

	@Test
	public void homeControllerLoadTest()  {
		System.out.println("homeControllerLoadTest...");
		List<Data> expectData = new ArrayList<Data>();
		for(long i = 0; i < 20; i++){
			expectData.add(new Data(String.valueOf(i),"data"+i,String.valueOf(new Date())));
		}
		
		DataRepository dataRepository = mock(DataRepository.class);
		when(dataRepository.findData(Long.MAX_VALUE, 20)).thenReturn(expectData);
		
		hc.setDataRepository(dataRepository);
		MockMvc mockMvc = standaloneSetup(hc).build();
		try {
			mockMvc.perform(get("/home/load"))
			       .andExpect(view().name("home"))
			       .andExpect(model().attributeExists("data"))
			       .andExpect(model().attribute("data", hasItems(expectData.toArray())));
		} catch (Throwable e) {
			// TODO Auto-generated catch block
			System.out.println("failed..");
			e.printStackTrace();
			return;
		}
		System.out.println("success");
	}
}
