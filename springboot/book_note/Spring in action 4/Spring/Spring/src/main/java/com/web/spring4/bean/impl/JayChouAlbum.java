package com.web.spring4.bean.impl;

import java.util.Arrays;
import java.util.List;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

import com.web.spring4.annotation.JCA;
import com.web.spring4.annotation._1;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.condition.ChooseJayChouAlbum;

/**
 * CD实现类-周杰伦专辑
 * @author Garden
 * 2018年3月5日
 */
@Component
//@Primary
//@Qualifier("JCA")
//@Qualifier("_1")
//@JCA
//@_1
public class JayChouAlbum implements CompactDisc{

	private String songs[] = {"夜曲"};
	private String artist = "周杰伦";
	
	@Override
	public void play() {
		// TODO Auto-generated method stub
		System.out.println("正在播放："+ songs[0] + "-" +artist);
	}
	
	@Override
	public void audiencePlay(String audienceName,int age){
		System.out.println(age + "岁的" + audienceName + " 正在播放："+ songs[0] + "-" +artist);
	}

	@Override
	public List<String> getSongsList() {
		// TODO Auto-generated method stub
		return Arrays.asList(this.songs);
	}

	@Override
	public void setSongsList(List<String> songsList) {
		// TODO Auto-generated method stub
		List<String> songs = Arrays.asList(this.songs);
		songs.clear();
		songs.addAll(songsList);
		this.songs = (String[]) songs.toArray();
	}
}
