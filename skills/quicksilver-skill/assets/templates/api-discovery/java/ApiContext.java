package com.jeedsoft.quicksilver.base.type;

import com.jeedsoft.common.basic.util.ObjectUtil;
import com.jeedsoft.quicksilver.account.model.Identity;
import com.jeedsoft.quicksilver.constant.QsTokenType;
import com.jeedsoft.quicksilver.i18n.LanguageHome;
import com.jeedsoft.quicksilver.integration.model.Token;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import org.apache.commons.fileupload2.core.FileItem;
import org.dom4j.Document;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class ApiContext extends BaseContext
{
	private static final ThreadLocal<ApiContext> threadInstance = new ThreadLocal<>();

	private Token token;

	private String path;

	private HttpServletRequest request = null;

	private HttpServletResponse response = null;

	private UUID onlineUserId = null;

	private UUID tokenId = null;

	private Identity identity = null;

	private JSONObject requestJson = new JSONObject();

	private Document requestXml = null;

	private String requestText = null;

	private List<FileItem> fileItems = null;

	private String language = LanguageHome.EN_US;

	private UUID userId = null;

	private ServiceContext serviceContext = null;

	private DaoContext daoContext = null;

	public ApiContext()
	{
	}

	public ApiContext(HttpServletRequest request, HttpServletResponse response)
	{
		this.request = request;
		this.response = response;
	}

	public static ApiContext getThreadInstance()
	{
		return threadInstance.get();
	}

	public static void setThreadInstance(ApiContext ac)
	{
		threadInstance.set(ac);
		ServiceContext.setThreadInstance(ac.getServiceContext());
		ac.getServiceContext().setSessionId(ac.getTokenId() == null ? null : ac.getTokenId().toString());
	}

	public Token getToken()
	{
		return token;
	}

	public void setToken(Token token)
	{
		this.token = token;
		this.userId = null;
		if (token != null && QsTokenType.USER.equals(token.getType())) {
			this.userId = token.getAccountId();
		}
	}

	public String getPath()
	{
		return path;
	}

	public void setPath(String path)
	{
		this.path = path;
	}

	public HttpServletRequest getRequest()
	{
		return request;
	}

	public void setRequest(HttpServletRequest request)
	{
		this.request = request;
	}

	public HttpServletResponse getResponse()
	{
		return response;
	}

	public void setResponse(HttpServletResponse response)
	{
		this.response = response;
	}

	public HttpSession getSession()
	{
		return request.getSession();
	}

	public JSONObject getRequestJson()
	{
		return requestJson;
	}

	public void setRequestJson(JSONObject requestJson)
	{
		this.requestJson = requestJson;
	}

	public Document getRequestXml()
	{
		return requestXml;
	}

	public void setRequestXml(Document requestXml)
	{
		this.requestXml = requestXml;
	}

	public String getRequestText()
	{
		return requestText;
	}

	public void setRequestText(String requestText)
	{
		this.requestText = requestText;
	}

	public FileItem getFileItem()
	{
		return fileItems == null || fileItems.isEmpty() ? null : fileItems.get(0);
	}

	public List<FileItem> getFileItems()
	{
		return fileItems == null ? new ArrayList<>() : fileItems;
	}

	public void addFileItem(FileItem fileItem)
	{
		if (fileItems == null) {
			fileItems = new ArrayList<>();
		}
		fileItems.add(fileItem);
	}

	public String getLanguage()
	{
		return language;
	}

	public void setLanguage(String language)
	{
		this.language = language;
		if (serviceContext != null) {
			serviceContext.setLanguage(language);
		}
	}

	public UUID getOnlineUserId()
	{
		return onlineUserId;
	}

	public void setOnlineUserId(UUID onlineUserId)
	{
		this.onlineUserId = onlineUserId;
	}

	public UUID getTokenId()
	{
		return tokenId;
	}

	public void setTokenId(UUID tokenId)
	{
		this.tokenId = tokenId;
	}

	public Identity getIdentity()
	{
		return identity;
	}

	public void setIdentity(Identity identity)
	{
		this.identity = identity;
		if (identity != null && identity.isUser()) {
			this.setUserId(identity.getEntityId());
		}
	}

	public UUID getUserId()
	{
		return userId;
	}

	public void setUserId(UUID userId)
	{
		this.userId = userId;
	}

	public UUID getDepartmentId()
	{
		return getServiceContext().getDepartmentId();
	}

	public ServiceContext getServiceContext()
	{
		if (identity == null) {
			if (serviceContext == null || !ObjectUtil.equals(serviceContext.getUserId(), userId)) {
				serviceContext = new ServiceContext(userId, language);
				serviceContext.setToken(token);
			}
		}
		else {
			if (serviceContext == null || identity != serviceContext.getIdentity()) {
				serviceContext = ServiceContext.create(identity, language);
			}
		}
		return serviceContext;
	}

	public DaoContext getDaoContext()
	{
		if (daoContext == null) {
			daoContext = getServiceContext().getDaoContext();
		}
		return daoContext;
	}
}
