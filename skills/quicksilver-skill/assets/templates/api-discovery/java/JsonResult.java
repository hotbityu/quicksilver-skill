package com.jeedsoft.quicksilver.base.type;

import com.jeedsoft.common.basic.util.JsonUtil;
import org.json.JSONObject;

import java.util.Iterator;
import java.util.Map;

public class JsonResult implements ApiResult
{
	private final JSONObject json = new JSONObject();

	public JsonResult()
	{
	}
	
	public JSONObject getJson()
	{
		return json;
	}

	public JsonResult put(String key, Object value)
	{
		JsonUtil.put(json, key, value);
		return this;
	}

	public JsonResult putAll(JSONObject json)
	{
		for (Iterator<?> keys = json.keys(); keys.hasNext();) {
			String key = (String)keys.next();
			JsonUtil.put(this.json, key, json.opt(key));
		}
		return this;
	}

	public JsonResult putAll(Map<String, Object> map)
	{
		for (Map.Entry<String, Object> entry: map.entrySet()) {
			JsonUtil.put(json, entry.getKey(), entry.getValue());
		}
		return this;
	}
	
	public String toString()
	{
		return json.toString();
	}
}
