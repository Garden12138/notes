package com.web.spring4.bean.impl;

import java.util.List;

import org.springframework.stereotype.Component;

import com.web.spring4.bean.CompactDisc;

/**
 * CD实现类-周杰伦专辑
 * @author Garden
 * 2018年3月5日
 */
//@Component
public class JayChouAlbum4 implements CompactDisc{

	private List<String> songs;
	private String artist;
	
	public JayChouAlbum4() {
		super();
	}
	

	public JayChouAlbum4(List<String> songs, String artist) {
		super();
		this.songs = songs;
		this.artist = artist;
	}
	
	public List<String> getSongs() {
		return songs;
	}

	public void setSongs(List<String> songs) {
		this.songs = songs;
	}

	public String getArtist() {
		return artist;
	}

	public void setArtist(String artist) {
		this.artist = artist;
	}

	@Override
	public void play() {
		// TODO Auto-generated method stub
		System.out.println("正在播放：第一首 "+ songs.get(0) + "-" +artist);
	}


	@Override
	public void audiencePlay(String audienceName,int age) {
		// TODO Auto-generated method stub
		
	}


	@Override
	public List<String> getSongsList() {
		// TODO Auto-generated method stub
		return this.songs;
	}


	@Override
	public void setSongsList(List<String> songsList) {
		// TODO Auto-generated method stub
		this.songs.addAll(songsList);
	}
	
}
