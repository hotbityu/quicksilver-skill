package com.jeedsoft.quicksilver.base.api;

import com.jeedsoft.quicksilver.base.model.EntityModel;
import com.jeedsoft.quicksilver.base.type.ApiContext;
import com.jeedsoft.quicksilver.base.type.JsonResult;

public interface BusinessEntityApi<T extends EntityModel> extends EntityApi<T>
{
    JsonResult submit(ApiContext ac);

    JsonResult assign(ApiContext ac);

    JsonResult execute(ApiContext ac);

    JsonResult finish(ApiContext ac);

    JsonResult discard(ApiContext ac);

    JsonResult revise(ApiContext ac);
}
