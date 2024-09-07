package com.web.spring4.bean.impl;

import javax.annotation.Resource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import com.web.spring4.annotation.JCA;
import com.web.spring4.annotation._1;
import com.web.spring4.annotation._2;
import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.MediaPlayer;
/**
 * 播放器实现类-CD播放器
 * @author Garden
 * 2018年3月5日
 */
//@Component
public class CDPlayer implements MediaPlayer{

	@Resource
//	@Qualifier("jayChouAlbum2")    /*限定符即字符串为Bean ID*/
//	@QualiZfier("JCA")
	@JCA
	@_2
	private CompactDisc cd1;
	
//	@Autowired /*@Resource不可用于构造函数*/
//	@Qualifier("jayChouAlbum2")  /*@Qualifier不能用于构造函数*/
	public CDPlayer(CompactDisc compactDisc) {
		super();
		this.cd1 = compactDisc;
	}
	

	public CDPlayer() {
		super();
	}


//	@Resource /*setter构造必需含有空构造函数*/
//	@Qualifier("jayChouAlbum2")
	public void setCd1(CompactDisc cd1) {
		this.cd1 = cd1;
	}

	@Override
	public void play() {
		// TODO Auto-generated method stub
		cd1.play();
	}

}
