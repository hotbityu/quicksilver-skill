package com.jeedsoft.quicksilver.base.api.impl;

import com.jeedsoft.quicksilver.base.model.EntityModel;

import java.util.UUID;

/**
 * @deprecated use EntityApiImpl
 */
@Deprecated
public abstract class TreeEntityApiImpl<T extends EntityModel> extends EntityApiImpl<T>
{
	public TreeEntityApiImpl()
	{
	}

	public TreeEntityApiImpl(UUID unitId, Class<T> modelClass)
	{
		super(unitId, modelClass);
	}
}
