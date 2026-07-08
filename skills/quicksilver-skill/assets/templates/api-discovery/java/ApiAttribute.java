package com.jeedsoft.quicksilver.integration.annotation;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(RetentionPolicy.RUNTIME)
public @interface ApiAttribute
{
	String name();
	
	String type();
	
	int dimension() default 1;
	
	String elementType() default "";
	
	boolean required() default false;
	
	String defaultValue() default "";
	
	String description() default "";
}
