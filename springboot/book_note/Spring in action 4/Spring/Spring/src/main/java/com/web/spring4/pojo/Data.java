package com.web.spring4.pojo;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

public class Data {
    @NotNull
    @Size(min=2,max=3)
	private  String id;
    @NotNull
    @Size(min=2,max=3)
	private  String message;
    @NotNull
    @Size(min=2,max=3)
	private  String time;
	public Data() {
		super();
	}
	public Data(String id, String message, String time) {
		super();
		this.id = id;
		this.message = message;
		this.time = time;
	}
	public String getId() {
		return id;
	}
	public void setId(String id) {
		this.id = id;
	}
	public String getMessage() {
		return message;
	}
	public void setMessage(String message) {
		this.message = message;
	}
	public String getTime() {
		return time;
	}
	public void setTime(String time) {
		this.time = time;
	}
	@Override
	public String toString() {
		return "Data [id=" + id + ", message=" + message + ", time=" + time + "]";
	}
}
