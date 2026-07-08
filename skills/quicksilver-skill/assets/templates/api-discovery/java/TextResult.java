package com.jeedsoft.quicksilver.base.type;

public class TextResult implements ApiResult
{
	private String text = "";

	public TextResult()
	{
	}

	public String getText()
	{
		return text;
	}
	
	public TextResult setText(String text)
	{
		this.text = text;
		return this;
	}
	
	public String toString()
	{
		return text;
	}
}
