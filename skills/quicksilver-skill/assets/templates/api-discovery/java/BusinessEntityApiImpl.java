package com.jeedsoft.quicksilver.base.api.impl;

import com.jeedsoft.quicksilver.base.model.EntityModel;

import java.util.UUID;

/**
 * @deprecated use EntityApiImpl
 */
@Deprecated
public abstract class BusinessEntityApiImpl<T extends EntityModel> extends EntityApiImpl<T>
{
	public BusinessEntityApiImpl()
	{
	}

	public BusinessEntityApiImpl(UUID unitId, Class<T> modelClass)
	{
		super(unitId, modelClass);
	}
}
