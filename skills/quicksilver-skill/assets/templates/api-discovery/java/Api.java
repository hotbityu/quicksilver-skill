package com.jeedsoft.quicksilver.integration.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Api
{
	String value() default "";

	/**
	 * use {@link #value} instead
	 */
	String path() default "";

	String description() default "";

	String since() default "";

	ApiRequestFormat requestFormat() default ApiRequestFormat.DEFAULT;

	ApiRequestFormat responseFormat() default ApiRequestFormat.DEFAULT;
	
	boolean isTokenRequired() default true;

	boolean isInherited() default true;
	
	boolean isFullPowers() default false;
	
	boolean isAlwaysEnabled() default false;

	ApiAttribute[] input() default {};
	
	ApiAttribute[] output() default {};
}
