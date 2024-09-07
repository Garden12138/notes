package com.web.spring4.bean.condition;

import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.core.type.AnnotatedTypeMetadata;

public class ChooseJayChouAlbum implements Condition{

	@Override
	public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
		// TODO Auto-generated method stub
		Object ob = context.getBeanFactory().getBean("jayChouAlbum2");
		return null == ob ? false : true;
	}

}
