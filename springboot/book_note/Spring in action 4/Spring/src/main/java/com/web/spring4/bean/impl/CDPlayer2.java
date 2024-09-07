package com.web.spring4.bean.impl;

import java.util.List;

import javax.annotation.Resource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.web.spring4.bean.CompactDisc;
import com.web.spring4.bean.MediaPlayer;

/**
 * 播放器实现类-CD播放器
 * 
 * @author Garden 2018年3月5日
 */
//@Component
public class CDPlayer2 implements MediaPlayer {

	private List<CompactDisc> cds;

	public CDPlayer2() {
		super();
	}

	public CDPlayer2(List<CompactDisc> cds) {
		super();
		this.cds = cds;
	}

	@Override
	public void play() {
		// TODO Auto-generated method stub
		cds.get(0).play();
	}

}
