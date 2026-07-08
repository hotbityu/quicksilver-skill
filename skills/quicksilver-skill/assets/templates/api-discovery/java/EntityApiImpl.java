package com.jeedsoft.quicksilver.base.api.impl;

import com.jeedsoft.common.advanced.data.criteria.Criteria;
import com.jeedsoft.common.advanced.data.criteria.Criterias;
import com.jeedsoft.common.advanced.data.filter.Filter;
import com.jeedsoft.common.advanced.data.filter.Filters;
import com.jeedsoft.common.advanced.data.order.Order;
import com.jeedsoft.common.advanced.db.dataset.DataSet;
import com.jeedsoft.common.advanced.db.dataset.PageDataSet;
import com.jeedsoft.common.advanced.transaction.annotation.Transaction;
import com.jeedsoft.common.basic.type.ParamSql;
import com.jeedsoft.common.basic.util.ArrayUtil;
import com.jeedsoft.common.basic.util.JsonUtil;
import com.jeedsoft.quicksilver.base.api.BusinessEntityApi;
import com.jeedsoft.quicksilver.base.api.EntityApi;
import com.jeedsoft.quicksilver.base.api.TreeEntityApi;
import com.jeedsoft.quicksilver.base.dao.EntityDao;
import com.jeedsoft.quicksilver.base.model.BusinessEntityModel;
import com.jeedsoft.quicksilver.base.model.EntityModel;
import com.jeedsoft.quicksilver.base.model.TreeEntityModel;
import com.jeedsoft.quicksilver.base.service.impl.EntityServiceImpl;
import com.jeedsoft.quicksilver.base.storage.sql.SqlCriteriaAnalyzer;
import com.jeedsoft.quicksilver.base.type.*;
import com.jeedsoft.quicksilver.base.util.LayerUtil;
import com.jeedsoft.quicksilver.base.util.ListQueryUtil;
import com.jeedsoft.quicksilver.base.util.MethodSignature;
import com.jeedsoft.quicksilver.constant.QsPlatform;
import com.jeedsoft.quicksilver.constant.QsServiceContextAttributeKey;
import com.jeedsoft.quicksilver.integration.annotation.Api;
import com.jeedsoft.quicksilver.integration.annotation.ApiAttribute;
import com.jeedsoft.quicksilver.integration.annotation.ApiDataType;
import com.jeedsoft.quicksilver.layout.EditHome;
import com.jeedsoft.quicksilver.layout.FormHome;
import com.jeedsoft.quicksilver.layout.ListHome;
import com.jeedsoft.quicksilver.query.QuerySchemaHome;
import com.jeedsoft.quicksilver.registry.Registry;
import com.jeedsoft.quicksilver.unit.model.FieldModel;
import com.jeedsoft.quicksilver.wfinstance.WfActivityHome;
import com.jeedsoft.quicksilver.wfinstance.model.WfActivityModel;
import org.json.JSONObject;

import java.util.List;
import java.util.UUID;

public abstract class EntityApiImpl<T extends EntityModel> extends BaseApiImpl
	implements EntityApi<T>, TreeEntityApi<T>, BusinessEntityApi<T>
{
	//private static final Logger logger = LoggerFactory.getLogger(EntityApiImpl.class);

	@SuppressWarnings("unchecked")
	private Class<T> modelClass;
	
	public EntityApiImpl()
	{
	}

	public EntityApiImpl(UUID unitId, Class<T> modelClass)
	{
		setUnitId(unitId);
		setModelClass(modelClass);
	}

	@Override
	@SuppressWarnings("unchecked")
	public Class<T> getModelClass()
	{
		// XXX make model class configurable
		if (modelClass == null) {
			UUID unitId = getUnitId();
			Class<?>[] classes = {
				LayerUtil.getGenericsParameterClass(getClass()),
				Registry.getEntityService(unitId).getModelClass(),
				Registry.getEntityDao(unitId).getModelClass(),
				Registry.getEntityAction(unitId).getModelClass(),
			};
			modelClass = (Class<T>)classes[0];
			for (Class<?> cls: classes) {
				if (cls != EntityModel.class && cls != BusinessEntityModel.class && cls != TreeEntityModel.class) {
					modelClass = (Class<T>)cls;
					break;
				}
			}
		}
		return modelClass;
	}
	
	private void setModelClass(Class<T> modelClass)
	{
		this.modelClass = modelClass;
	}
	
	protected EntityServiceImpl<T> getService()
	{
		return Registry.getService(getUnitId());
	}
	
	protected EntityDao<T> getDao()
	{
		return Registry.getDao(getUnitId());
	}

	@Api
	(
		value = "item",
		input = {
			@ApiAttribute(name = "id", type = ApiDataType.UUID, required = true),
			@ApiAttribute(name = "fieldNames", type = ApiDataType.ARRAY, elementType = ApiDataType.STRING),
		},
		output = {
			@ApiAttribute(name = "data", type = ApiDataType.OBJECT, required = true),
		}
	)
	@Override
	public JsonResult getItem(ApiContext ac)
	{
		ServiceContext sc	= ac.getServiceContext();
		DaoContext dc		= ac.getDaoContext();
		JSONObject args		= ac.getRequestJson();
		UUID unitId			= getUnitId();
		UUID entityId		= JsonUtil.getUuid(args, "id");
		String[] fieldNames	= JsonUtil.getStringArray(args, "fieldNames", false);
		JsonResult result	= new JsonResult();
		if (fieldNames != null) {
			result.put("data", FormHome.getService().getDataJson(sc, unitId, fieldNames, entityId));
		}
		else {
			UUID editId = EditHome.getDao().getEditId(dc, unitId, entityId);
			UUID formId = FormHome.getDao().getDefaultFormId(dc, unitId);
			result.put("data", FormHome.getService().getDataJson(sc, formId, editId, entityId));
		}
		return result;
	}

	@Api
	(
		value = "list",
		input = {
			@ApiAttribute(name = "keyword", type = ApiDataType.STRING),
			@ApiAttribute(name = "schemaId", type = ApiDataType.UUID),
			@ApiAttribute(name = "listId", type = ApiDataType.UUID),
			@ApiAttribute(name = "masterEntityId", type = ApiDataType.UUID),
			@ApiAttribute(name = "relationId", type = ApiDataType.UUID),
			@ApiAttribute(name = "conditions", type = ApiDataType.ARRAY, elementType = ApiDataType.OBJECT),
			@ApiAttribute(name = "fieldNames", type = ApiDataType.ARRAY, elementType = ApiDataType.STRING),
			@ApiAttribute(name = "pageSize", type = ApiDataType.INT),
			@ApiAttribute(name = "pageIndex", type = ApiDataType.INT),
			@ApiAttribute(name = "count", type = ApiDataType.BOOLEAN),
		},
		output = {
			@ApiAttribute(name = "items", type = ApiDataType.ARRAY, elementType=ApiDataType.OBJECT),
			@ApiAttribute(name = "hasNextPage", type = ApiDataType.BOOLEAN),
		}
	)
	@Override
	public JsonResult getList(ApiContext ac)
	{
		ServiceContext sc	= ac.getServiceContext();
		DaoContext dc		= ac.getDaoContext();
		JSONObject args		= ac.getRequestJson();
		UUID unitId			= getUnitId();
		String[] fieldNames	= JsonUtil.getStringArray(args, "fieldNames", false);
		int pageSize		= JsonUtil.getInt(args, "pageSize", 0);
		int pageIndex		= JsonUtil.getInt(args, "pageIndex", 0);
		boolean count		= JsonUtil.getBoolean(args, "count", false);
		DataSet<T> ds		= getListDataSet(ac);
		Iterable<FieldModel> fields;
		if (fieldNames != null) {
			fields = ListHome.getDao().getDataFields(dc, unitId, fieldNames, sc.getUserId());
		}
		else {
			UUID listId = ListHome.getDao().getDefaultListId(dc, unitId);
			fields = ListHome.getDao().getDataFields(dc, listId, sc.getUserId());
		}
		PageDataSet<?> pds = new PageDataSet<>(ds, pageSize).pageJump(pageIndex);
		JsonResult result = new JsonResult();
		result.put("items", ListHome.getService().getDataJson(sc, fields, pds));
		result.put("hasNextPage", pds.hasNextPage());
		if (count) {
			result.put("pageCount", pds.getPageCount());
			result.put("recordCount", pds.totalSize());
		}
		return result;
	}

	@Api
	(
		value = "create",
		input = {
			@ApiAttribute(name = "data", type = ApiDataType.OBJECT, required = true),
		},
		output = {
			@ApiAttribute(name = "id", type = ApiDataType.UUID, required = true),
		}
	)
	@Override
	public JsonResult create(ApiContext ac)
	{
		ServiceContext sc	= ac.getServiceContext();
		JSONObject args		= ac.getRequestJson();
		T entity			= JsonUtil.getObject(args, "data", getModelClass());
		UUID entityId		= getService().create(sc, entity);
		return new JsonResult().put("id", entityId);
	}

	@Api
	(
		value = "update",
		input = {
			@ApiAttribute(name = "id", type = ApiDataType.UUID, required = true),
			@ApiAttribute(name = "data", type = ApiDataType.OBJECT, required = true),
		}
	)
	@Override
	public JsonResult update(ApiContext ac)
	{
		ServiceContext sc	= ac.getServiceContext();
		JSONObject args		= ac.getRequestJson();
		UUID entityId		= JsonUtil.getUuid(args, "id");
		T entity			= JsonUtil.getObject(args, "data", getModelClass());
		getService().update(sc, entityId, entity);
		return null;
	}

	@Api
	(
		value = "delete",
		input = {
			@ApiAttribute(name = "id", type = ApiDataType.UUID, required = true),
		}
	)
	@Override
	public JsonResult delete(ApiContext ac)
	{
		ServiceContext sc	= ac.getServiceContext();
		JSONObject args		= ac.getRequestJson();
		UUID entityId		= JsonUtil.getUuid(args, "id");
		getService().delete(sc, entityId);
		return null;
	}
	
	protected DataSet<T> getListDataSet(ApiContext ac)
	{
		ServiceContext sc = ac.getServiceContext();
		Criteria criteria = Criterias.create()
				.setSelect(getListSelect(ac))
				.setFilter(getListFilter(ac))
				.setOrder(getListOrder(ac));
        if (sc.hasAttribute(QsServiceContextAttributeKey.LIST_QUERY_NOT_CHECK_ACCESS)) {
            sc = sc.notCheckAccess();
        }
		return getService().getItems(sc, criteria);
	}
	
	protected String[] getListSelect(ApiContext ac)
	{
		ServiceContext sc = ac.getServiceContext();
		JSONObject args = ac.getRequestJson();
		UUID unitId = getUnitId();
		return ListQueryUtil.getSelect(sc, args, unitId, QsPlatform.COMPUTER); // XXX platform
	}
	
	protected Filter getListFilter(ApiContext ac)
	{
        // 向后兼容 begin
        MethodSignature sign1 = new MethodSignature("getListWhere", ActionContext.class);
        MethodSignature sign2 = new MethodSignature("getListFilter", ActionContext.class);
        if (LayerUtil.isNearer(this.getClass(), sign1, sign2)) {
            return Filters.sql(getListWhere(ac));
        }
        // 向后兼容 end
		ServiceContext sc = ac.getServiceContext();
		JSONObject args = ac.getRequestJson();
		UUID unitId = getUnitId();
		return ListQueryUtil.getFilter(sc, args, unitId);
	}

    /**
     * @deprecated since 7.0, use {@link #getListFilter(ApiContext)}
     */
    @Deprecated
    protected ParamSql getListWhere(ApiContext ac)
    {
        ServiceContext sc = ac.getServiceContext();
        JSONObject args = ac.getRequestJson();
        UUID unitId = getUnitId();
        Filter filter = ListQueryUtil.getFilter(sc, args, unitId);
        return SqlCriteriaAnalyzer.analyse(filter);
    }
    
    /**
     * @deprecated since 7.0, use {@link #getListOrder(ApiContext)}
     */
    @Deprecated
    protected String[] getListSqlOrder(ApiContext ac)
    {
        DaoContext dc = ac.getDaoContext();
        JSONObject args = ac.getRequestJson();
        String[] order = JsonUtil.getStringArray(args, "order", false);
        UUID listId = JsonUtil.getUuid(args, "listId", null);
        UUID schemaId = JsonUtil.getUuid(args, "schemaId", null);
        if (ArrayUtil.isEmpty(order) && schemaId != null) {
            order = QuerySchemaHome.getDao().getSqlOrder(dc, schemaId);
        }
        if (ArrayUtil.isEmpty(order) && listId != null) {
            order = ListHome.getDao().getSqlOrder(dc, listId);
        }
        return order;
    }

	protected List<Order> getListOrder(ApiContext ac)
	{
		ServiceContext sc = ac.getServiceContext();
		JSONObject args = ac.getRequestJson();
		return ListQueryUtil.getOrder(sc, args);
	}
	
	//--------------------------------------------------------------------------
	// for BusinessEntityApi
	//--------------------------------------------------------------------------

    @Api
    (
        value = "submit",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "workflowCode", type = ApiDataType.STRING),
            @ApiAttribute(name = "form", type = ApiDataType.OBJECT),
            @ApiAttribute(name = "data", type = ApiDataType.OBJECT),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "processId", type = ApiDataType.UUID),
            @ApiAttribute(name = "instantActivity", type = ApiDataType.OBJECT),
        }
    )
    @Override
    @Transaction
    public JsonResult submit(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        DaoContext dc       = ac.getDaoContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId", null);
        String workflowCode = JsonUtil.getString(args, "workflowCode", null);
        T form              = JsonUtil.getObject(args, "form", null, getModelClass());
        T data              = JsonUtil.getObject(args, "data", null, getModelClass());
        if (form != null) {
            entityId = save(sc, entityId, form);
        }
        UUID processId = getService().submit(sc, entityId, data, workflowCode);
        WfActivityModel activity = WfActivityHome.getDao().getNewInstantActivity(dc, processId, null);
        JsonResult result = new JsonResult();
        result.put("entityId", entityId);
        result.put("processId", processId);
        result.put("instantActivity", WfActivityHome.getService().getInstantActivityJson(sc, activity));
        return result;
    }

    @Api
    (
        value = "assign",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "form", type = ApiDataType.OBJECT),
            @ApiAttribute(name = "data", type = ApiDataType.OBJECT),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
        }
    )
    @Override
    @Transaction
    public JsonResult assign(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId");
        T form              = JsonUtil.getObject(args, "forms", null, getModelClass());
        T data              = JsonUtil.getObject(args, "data", getModelClass());
        if (form != null) {
            entityId = save(sc, entityId, form);
        }
        getService().assign(sc, entityId, data);
        return new JsonResult().put("entityId", entityId);
    }
    
    @Api
    (
        value = "execute",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "form", type = ApiDataType.OBJECT),
            @ApiAttribute(name = "data", type = ApiDataType.OBJECT),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
        }
    )
    @Override
    @Transaction
    public JsonResult execute(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId");
        T form              = JsonUtil.getObject(args, "form", null, getModelClass());
        T data              = JsonUtil.getObject(args, "data", null, getModelClass());
        if (form != null) {
            entityId = save(sc, entityId, form);
        }
        getService().execute(sc, entityId, data);
        return new JsonResult().put("entityId", entityId);
    }

    @Api
    (
        value = "finish",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "form", type = ApiDataType.OBJECT),
            @ApiAttribute(name = "data", type = ApiDataType.OBJECT),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
        }
    )
    @Override
    @Transaction
    public JsonResult finish(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId");
        T form              = JsonUtil.getObject(args, "form", null, getModelClass());
        T data              = JsonUtil.getObject(args, "data", null, getModelClass());
        if (form != null) {
            entityId = save(sc, entityId, form);
        }
        getService().finish(sc, entityId, data);
        return new JsonResult().put("entityId", entityId);
    }

    @Api
    (
        value = "discard",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
            @ApiAttribute(name = "form", type = ApiDataType.OBJECT),
            @ApiAttribute(name = "data", type = ApiDataType.OBJECT),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
        }
    )
    @Override
    @Transaction
    public JsonResult discard(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId");
        T form              = JsonUtil.getObject(args, "form", null, getModelClass());
        T data              = JsonUtil.getObject(args, "data", null, getModelClass());
        if (form != null) {
            entityId = save(sc, entityId, form);
        }
        getService().discard(sc, entityId, data);
        return new JsonResult().put("entityId", entityId);
    }

    @Api
    (
        value = "revise",
        input = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID, required = true),
        },
        output = {
            @ApiAttribute(name = "entityId", type = ApiDataType.UUID),
        }
    )
    @Override
    @Transaction
    public JsonResult revise(ApiContext ac)
    {
        ServiceContext sc   = ac.getServiceContext();
        JSONObject args     = ac.getRequestJson();
        UUID entityId       = JsonUtil.getUuid(args, "entityId");
        getService().revise(sc, entityId);
        return new JsonResult().put("entityId", entityId);
    }

    protected UUID save(ServiceContext sc, UUID entityId, T entity)
    {
        if (entityId == null) {
            return getService().create(sc, entity);
        }
        else {
            getService().update(sc, entityId, entity);
            return entityId;
        }
    }
}
