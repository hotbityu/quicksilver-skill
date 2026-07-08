package com.jeedsoft.quicksilver.base.type;

import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.json.JSONObject;

import java.util.Iterator;
import java.util.Map;

public class XmlResult implements ApiResult
{
	private Document xml;

	public static final String DEFAULT_ROOT_TAG_NAME = "xml";
	
	public XmlResult()
	{
		initialize();
	}

	public Document getXml()
	{
		if (xml == null) {
			initialize();
		}
		return xml;
	}
	
	public XmlResult setXml(Document xml)
	{
		this.xml = xml;
		return this;
	}

	public XmlResult put(String key, Object value)
	{
		Element root = xml.getRootElement();
		Element element = root.element(key);
		if (element != null) {
			root.remove(element);
		}
		element = root.addElement(key);
		if (value == null) {
			element.addAttribute("isNull", "true");
		}
		else {
			element.setText(value.toString());
		}
		return this;
	}

	public XmlResult putAll(JSONObject json)
	{
		for (Iterator<?> keys = json.keys(); keys.hasNext();) {
			String key = (String)keys.next();
			put(key, json.opt(key));
		}
		return this;
	}

	public XmlResult putAll(Map<String, Object> map)
	{
		for (Map.Entry<String, Object> entry: map.entrySet()) {
			put(entry.getKey(), entry.getValue());
		}
		return this;
	}
	
	public String toString()
	{
		return xml.asXML();
	}
	
	private void initialize()
	{
		xml = DocumentHelper.createDocument();
		xml.addElement(DEFAULT_ROOT_TAG_NAME);
	}
}
