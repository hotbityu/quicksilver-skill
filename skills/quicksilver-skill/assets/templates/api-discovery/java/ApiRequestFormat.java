package com.jeedsoft.quicksilver.integration.annotation;

public enum ApiRequestFormat
{
	JSON("json"), XML("xml"), TEXT("text"), DEFAULT("default");
	
	private String name;
	
	private ApiRequestFormat(String name)
	{
		this.name = name;
	}
	
	@Override
	public String toString()
	{
		return name;
	}
}
