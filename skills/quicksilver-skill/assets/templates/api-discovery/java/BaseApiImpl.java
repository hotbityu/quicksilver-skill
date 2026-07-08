package com.jeedsoft.quicksilver.base.api.impl;

import com.jeedsoft.quicksilver.base.api.BaseApi;

import java.util.UUID;

public abstract class BaseApiImpl implements BaseApi
{
	private UUID unitId;
	
	@Override
	public UUID getUnitId()
	{
		return unitId;
	}

	public void setUnitId(UUID unitId)
	{
		this.unitId = unitId;
	}
}
