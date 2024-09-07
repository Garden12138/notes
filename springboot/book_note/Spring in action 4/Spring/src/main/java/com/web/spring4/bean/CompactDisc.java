package com.web.spring4.bean;

import java.util.List;

/**
 * CD接口
 * @author Garden
 * 2018年3月5日
 */
public interface CompactDisc {
	
	public void play();

	public void audiencePlay(String audienceName,int age);
	
	public List<String> getSongsList();
	
	public void setSongsList(List<String> songsList);
}
