package com.web.entity;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Table;
import com.web.entity.IdEntity;

@Entity
@Table(name = "tb_user")
public class UserEntity extends IdEntity{
	
	private static final long serialVersionUID = 8882805502574300840L;

	@Column(name = "f_username")
	private String username;
	
	@Column(name = "f_password")
	private String password;

	public UserEntity() {
		super();
	}

	public UserEntity(String username, String password) {
		super();
		this.username = username;
		this.password = password;
	}

	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	@Override
	public String toString() {
		return "UserEntity [username=" + username + ", password=" + password + "]";
	}


	
}
