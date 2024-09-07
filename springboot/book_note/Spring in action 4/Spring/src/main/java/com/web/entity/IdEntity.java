package com.web.entity;

import java.io.Serializable;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.MappedSuperclass;

import org.hibernate.annotations.GenericGenerator;

/**
 * uuid 共享体
 * @author Garden
 * 2017年4月28日
 */
@MappedSuperclass
public class IdEntity implements Serializable{
	
	@Id
	@GeneratedValue(generator = "tableGenerator")
	@GenericGenerator(name = "tableGenerator", strategy = "uuid")
	@Column(name = "f_id", nullable = false, length = 32, unique = true)
	private String id;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}
}
