package com.jeedsoft.quicksilver.base.type;

import com.jeedsoft.common.basic.util.ResponseUtil;
import com.jeedsoft.quicksilver.misc.model.MemoryFileModel;

import java.io.File;
import java.nio.file.Files;

public class FileResult implements ApiResult
{
	public static final String CONTENT_TYPE_TEXT 		= "text/plain; charset=UTF-8";
	public static final String CONTENT_TYPE_DOWNLOAD	= "application/x-download";

	private String fileName = null;
	
	private Object content;

	private boolean deleteAfterFinish = false;
	
	private boolean isDownload = true;

	private long lastModifiedMillis = -1;

	public FileResult(File file)
	{
		this.content = file;
		this.lastModifiedMillis = file.lastModified();
	}

	public FileResult(MemoryFileModel memoryFile)
	{
		this.fileName = memoryFile.getName();
		this.content = memoryFile.getBytes();
		this.lastModifiedMillis = memoryFile.getLastModified();
	}

	public FileResult(String fileName, Object content)
	{
		this.fileName = fileName;
		this.content = content;
	}
	
	public void setFileName(String fileName)
	{
		this.fileName = fileName;
	}

	public String getFileName()
	{
		return fileName;
	}

	public void setContent(Object content)
	{
		this.content = content;
	}

	public Object getContent()
	{
		return content;
	}

	public boolean isDeleteAfterFinish()
	{
		return deleteAfterFinish;
	}

	public void setDeleteAfterFinish(boolean deleteAfterFinish)
	{
		this.deleteAfterFinish = deleteAfterFinish;
	}

	public boolean isDownload()
	{
		return isDownload;
	}

	public void setDownload(boolean isDownload)
	{
		this.isDownload = isDownload;
	}

	public String getContentType()
	{
		if (isDownload) {
			return content instanceof String ? CONTENT_TYPE_TEXT : CONTENT_TYPE_DOWNLOAD;
		}
		else if (fileName != null) {
			return ResponseUtil.getContentType(fileName);
		}
		else if (content instanceof File) {
			try {
				File file = (File)content;
				String content = ResponseUtil.getContentType(file.getName());
				if (content != null) {
					return content;
				}
				return ResponseUtil.getContentType(Files.probeContentType(file.toPath()));
			}
			catch (Exception e) {
				return null;
			}
		}
		else {
			return null;
		}
	}

	public long getLastModifiedMillis()
	{
		return (this.lastModifiedMillis / 1000) * 1000;
	}
}
