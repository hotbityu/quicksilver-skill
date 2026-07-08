# API Discovery

## Use When

Use this reference when the user asks to discover, analyze, inventory, or document APIs across all QS module projects and record the result in a Markdown file.

The output is an evidence-backed API report. Confirmed facts must cite source files. Inferred facts must be labeled as inferred. Do not add a separate "pending confirmation" / "needs confirmation" section; unresolved details should stay in the relevant API's analysis status or notes.

## Contract Reference

Use the bundled API annotation templates as the primary contract reference when analyzing QS APIs:

- `assets/templates/api-discovery/java/Api.java`
- `assets/templates/api-discovery/java/BaseApiImpl.java`
- `assets/templates/api-discovery/java/EntityApiImpl.java`
- `assets/templates/api-discovery/java/ApiAttribute.java`
- `assets/templates/api-discovery/java/ApiDataType.java`
- `assets/templates/api-discovery/java/ApiRequestFormat.java`
- `assets/templates/api-discovery/java/ApiResult.java`
- `assets/templates/api-discovery/java/JsonResult.java`
- `assets/templates/api-discovery/java/XmlResult.java`
- `assets/templates/api-discovery/java/TextResult.java`
- `assets/templates/api-discovery/java/FileResult.java`
- `assets/templates/api-discovery/sql/`

Treat methods annotated with `com.jeedsoft.quicksilver.integration.annotation.Api` or an equivalent imported `@Api` as confirmed API entry points. The annotation fields are secondary metadata hints and should not override actual handler code behavior:

- `value`: preferred API path or name.
- `path`: legacy API path; use only when `value` is empty.
- `description`: developer-supplied API purpose text. Use it as the first priority for the API purpose.
- `since`: version or release marker indicating when the API became available. Render it as `起始版本` in `基本資訊` only when non-empty.
- `requestFormat`: request format, one of `json`, `xml`, `text`, or `default`.
- `responseFormat`: response format, one of `json`, `xml`, `text`, or `default`.
- `isTokenRequired`: whether token authentication is required. When `isFullPowers=true`, this flag no longer applies because the developer fully owns request parsing and response writing. Handler code is still the stronger source: if the handler calls `getTokenId()` on the method parameter typed as `ApiContext`, such as `public JsonResult discard(ApiContext ac)` with `ac.getTokenId()` or `public JsonResult discard(ApiContext context)` with `context.getTokenId()`, treat the API as token-dependent even when the annotation says `isTokenRequired=false`. Do not treat arbitrary non-`ApiContext` `getTokenId()` calls, static `ApiContext.getTokenId()` calls, or local-variable calls as token requirements.
- `isInherited`: whether inherited behavior is enabled.
- `isFullPowers`: whether the API has full powers.
- `isAlwaysEnabled`: whether the API is always enabled.
- `input`: request attributes, each with `name`, `type`, `dimension`, `elementType`, `required`, `defaultValue`, and `description`.
- `output`: response attributes with the same attribute fields.

The primary Java scan target is `XXXApiImpl` implementation classes under `api.impl` packages. Examples:

- `com.jeedsoft.quicksilver.account.api.impl.AccountApiImpl`
- `com.jeedsoft.quicksilver.user.api.impl.UserApiImpl`

In these classes, every method annotated with `@Api` is the handler for the current API request. Use that method as the canonical Java source for path, request format, response format, token requirement, actual request-field reads, actual response construction, and implementation flow. Use `@Api.input` and `@Api.output` only as fallback support when code evidence is incomplete.

`BaseApiImpl`, `EntityApiImpl`, `BusinessEntityApiImpl`, and `TreeEntityApiImpl` are top-level/base API classes. They define reusable or inherited `@Api` handlers and contracts, but they must not be exported as standalone APIs for themselves. Prefer the target project's actual source when it exists; use the bundled `assets/templates/api-discovery/java/` files only as fallback references. Only concrete API classes that extend these base classes inherit their APIs. Non-entity API classes that inherit `BaseApiImpl` without `EntityApiImpl` in the superclass chain, such as `MiscApiImpl`, do not inherit `item`, `list`, `create`, `update`, `delete`, `submit`, `assign`, `execute`, `finish`, `discard`, or `revise`. For concrete classes that do extend `EntityApiImpl`, you must expand each inherited `@Api` method into concrete routes for each concrete API class and unit; do not leave inherited APIs only as generic suffix templates. Use the concrete API class's derived unit prefix, which should come from `Home.UNIT_ID -> TsUnit.FCode` first and fall back to `CACHE_REGION` only when needed. For example, inherited `@Api(value = "item")` becomes `openapi/qs/user/item` for unit `Qs.User`, `openapi/qs/account/item` for unit `Qs.Account`, and `openapi/qs/diskfile/item` for unit `Qs.DiskFile`. `BusinessEntityApi` workflow-operation methods, including `submit`, `assign`, `execute`, `finish`, `discard`, and `revise`, are available as inherited routes only for units whose effective `TsUnit.FSupportWorkflow=1`; do not export those inherited routes for units that do not support workflow. This workflow-support gate does not suppress concrete `@Api` handlers declared directly in the unit's own `XXXApiImpl` class.

Use the bundled `BaseApiImpl.java` template to resolve non-entity superclass chains when the target project does not include the base source. A chain that stops at `BaseApiImpl` does not get entity-style inherited APIs unless another concrete base class in that chain declares its own `@Api` handlers.

Current `EntityApiImpl` contains the behavior formerly represented by deprecated `BusinessEntityApiImpl` and `TreeEntityApiImpl`. Old projects may still extend those two legacy classes. When their source is missing from the target project, resolve them from the bundled templates and continue walking the chain to `EntityApiImpl`; do not treat an unresolved legacy base class as a reason to drop inherited entity APIs.

When exporting inherited APIs, keep the report path-first and attach inherited-contract information to each concrete API route. Instead:

- Emit each concrete inherited route, such as `openapi/qs/diskfile/item`, as its own path-headed API section.
- Mark it as inherited from `EntityApiImpl` in the API's basic information when useful.
- Write request/response fields in that concrete route section when they are needed for the API reference.
- If inherited behavior is unchanged and repeating the full contract would be noisy, identify the route as an unchanged `EntityApiImpl` inherited handler through `入口類型` and the request/response contract. Do not add source-evidence rows to `基本資訊`.
- Do not create standalone shared inherited-contract, binding catalog, or exported-route catalog sections.

When the target project has an `EntityApiImpl.java`, discover inherited API suffixes from that file. Known inherited entity API suffixes from the bundled fallback `EntityApiImpl.java` include:

- `item`
- `list`
- `create`
- `update`
- `delete`
- `submit`
- `assign`
- `execute`
- `finish`
- `discard`
- `revise`

The inherited suffixes `submit`, `assign`, `execute`, `finish`, `discard`, and `revise` come from `BusinessEntityApi` workflow behavior. Export inherited versions only when the concrete unit metadata has `FSupportWorkflow=1`. If a concrete `XXXApiImpl` declares one of these suffixes with its own `@Api`, keep that concrete handler according to the normal concrete-handler rules.

When a concrete `XXXApiImpl` overrides an inherited API method with its own `@Api`, use the concrete class method as the primary handler and record the base method only as inherited/overridden evidence. When it does not override the inherited method, still emit the concrete route under that concrete API class and unit.

`@Api.value` or `@Api.path` is usually the operation path suffix, not always the full external URL. Derive the callable path from the API class's unit/home context when possible:

- Find the related Home class from the API constructor, superclass arguments, imports, or unit metadata. Example: `UserApiImpl()` calls `super(UserHome.UNIT_ID, UserModel.class)`.
- Derive the unit prefix from `Home.UNIT_ID` and `TsUnit.FCode` first:
  - Read `public static final UUID UNIT_ID` from the resolved Home class.
  - Look up that unit ID in module SQL metadata such as `init.sql` and find the matching `TsUnit.FCode`.
  - Convert `TsUnit.FCode` to lowercase and replace `.` with `_`, for example `Qs.Attachment` -> `qs_attachment`, `Qs.DictionaryItem` -> `qs_dictionaryitem`.
  - Convert that unit token to the OpenAPI unit path by replacing only the first underscore with a slash: `qs_attachment` -> `qs/attachment`, `qs_dictionaryitem` -> `qs/dictionaryitem`.
  - Use that derived prefix as the primary evidence when composing the exported OpenAPI route.
- If `Home.UNIT_ID -> TsUnit.FCode` cannot be resolved, inspect the Home class for `public static final String CACHE_REGION`, such as `UserHome.CACHE_REGION = "qs_user"`.
- Convert the fallback cache region to the openapi unit path by replacing only the first underscore with a slash: `qs_user` -> `qs/user`, `qs_abc_def` -> `qs/abc_def`.
- Append the `@Api.value` or `@Api.path` suffix: `token/apply`.
- The route path becomes `openapi/qs/user/token/apply`.
- Export only the relative OpenAPI route path, such as `openapi/qs/user/token/apply`. Do not include environment-specific base URLs in the Markdown report.
- Explain in the generated report how to compose a full URL from the exported route: full URL = `{serviceBaseUrl}/{api-path}`. The `{serviceBaseUrl}` should include protocol, host, port, and deployment context path when applicable, and `{api-path}` is the path shown after the HTTP method in the API block title, such as `POST openapi/qs/user/token/apply`. Do not write an environment-specific concrete base URL unless the user provides one.
- If neither `Home.UNIT_ID -> TsUnit.FCode` nor `CACHE_REGION` can be found, keep the annotation path as confirmed and mark the route/status as `inferred` or `metadata-only` as evidence supports.

API loading follows the runtime logic:

```java
boolean isUnitApiEnabled = unit.isApiEnabled();
for (ApiInfo info: map.values()) {
    if (isUnitApiEnabled || info.isAlwaysEnabled) {
        info = new ApiInfo(info);
        info.path = info.path.startsWith("/") ? info.path.substring(1) : prefix + info.path;
        info.unitCode = unitCode;
        list.add(info);
    }
}
```

Apply that logic when deciding API availability, not whether to include a discovered API class handler in the report:

- If `TsUnit.FApiEnabled=1`, export all APIs discovered for that unit.
- If `TsUnit.FApiEnabled` is missing or not `1`, a concrete handler with `@Api.isAlwaysEnabled=true` is still available at runtime and should have availability `true`.
- If an API is declared in a concrete API class with `@Api`, still list it even when `TsUnit.FApiEnabled` is missing or not `1`; mark its availability as `false` and status as `unavailable` unless `@Api.isAlwaysEnabled=true`. Do not silently drop concrete API-class handlers solely because the unit API is disabled.
- For disabled units, do not expand default inherited `EntityApiImpl` APIs unless runtime metadata or source evidence proves they are available. Only concrete `@Api` handlers declared in the bound API class should be listed as unavailable.
- If `@Api.value` or `@Api.path` starts with `/`, treat it as an absolute OpenAPI relative path: strip the leading slash, then prefix it with `openapi/`. Do not prepend the unit prefix or unit code. Example: `/user/autologin` -> `openapi/user/autologin`.
- Otherwise prepend the unit prefix derived first from `Home.UNIT_ID -> TsUnit.FCode`, and use `CACHE_REGION` only as fallback. Example: prefix `openapi/qs/user/` plus `token/apply` -> `openapi/qs/user/token/apply`, and `Qs.Attachment` -> `qs_attachment` -> `openapi/qs/attachment/`.
- If the API path contains a wildcard `*`, replace it with a path parameter placeholder in the exported route. Infer the placeholder name from code context, such as the `ApiContext.getPath()` local variable name, substring/replace result variable, service method argument name, or nearby domain naming. Use names like `{code}`, `{id}`, or `{path}` as evidence supports; use `{path}` only when no more specific name can be inferred. Example: `/qs/file/download/*` may export as `openapi/qs/file/download/{path}` when the handler uses `String path = context.getPath()`.
- Record `unitCode` from `TsUnit.FCode` on each exported API when available.

`ApiResult` is the common API response marker. Known result implementations:

- `JsonResult`: treat as a JSON response body. Fields are added with `put(key, value)` or `putAll(...)`.
- `XmlResult`: treat as an XML response body. It is commonly rooted at `xml`, and fields are added with `put(key, value)` or `putAll(...)`.
- `TextResult`: treat as a plain text response body. Content is set with `setText(...)`.
- `FileResult`: treat as a file-download or binary-stream response body. Record file name, content source, `isDownload`, content type, and last-modified clues when visible.

Observed QS handler pattern:

- `@Api` is commonly written as a multi-line annotation block immediately above the handler method.
- Ignore `@Api` blocks that appear inside Java line comments or block comments.
- `@Override` may appear either before or after the `@Api` block; do not require a fixed annotation order.
- Handler methods commonly look like `public JsonResult methodName(ApiContext ac)`, but may return any `ApiResult` implementation such as `FileResult`, `TextResult`, or `XmlResult`.
- `JSONObject args = ac.getRequestJson()` represents the API request body.
- Request body properties are usually read through helpers such as `JsonUtil.getString(args, "field")`, `JsonUtil.getUuid(args, "field", null)`, `JsonUtil.getUuidArray(args, "field", false)`, and `JsonUtil.getInt(args, "field")`.
- Request body properties may also be read through `JSONObject` methods on the request body variable, such as `args.optString("captcha", null)`, `args.optInt("count", 0)`, `args.getString("name")`, or `args.getJSONObject("options")`.
- Any API handler may use `HttpServletRequest request = ac.getRequest()` to read request parameters, headers, cookies, sessions, body readers, or input streams, even when `isFullPowers = false`.
- Full-powers APIs such as `@Api(isFullPowers = true)` may return `void` and directly use `HttpServletRequest request = ac.getRequest()` and `HttpServletResponse response = ac.getResponse()`. In this mode the developer fully owns request parsing and response writing, so `@Api.isTokenRequired` is not applicable.
- Full-powers responses may be written through `response.sendRedirect(...)`, `response.addCookie(...)`, `response.setContentType(...)`, `response.getWriter()`, `response.getOutputStream()`, status setters, or headers instead of returning an `ApiResult`.
- File-upload APIs may read uploaded content from `ac.getFileItem()`.
- JSON and XML response values are usually written through `JsonResult` or `XmlResult` plus `put(...)` or `putAll(...)`.
- Text response values are usually written through `TextResult.setText(...)`.
- File response values usually come from `FileResult` constructors or setters such as `setFileName`, `setContent`, and `setDownload`.
- Record the handler's concrete `ApiResult` return type as the response model when no stronger code evidence is present. Interpret `JsonResult` as JSON, `XmlResult` as XML, `TextResult` as text, and `FileResult` as a file/binary stream.
- `return null` usually means the handler has no response body beyond success/failure status; record the response as empty unless `@Api.output` says otherwise.
- `@Api` may omit `input` or `output` entirely. Missing annotation fields mean "not declared in annotation", not "no request fields" or "no response fields".
- Normally API request parameters are parsed in the API handler and then typed values are passed to service/home/DAO methods. Sometimes the handler passes the raw `JSONObject`, servlet request, map, or another unparsed object directly to service/home/DAO; in that case continue analysis into the callee to find the real field reads.

## Inputs

Resolve these values before writing the report:

- `<project-root>`: QS parent project root. Prefer the current workspace root when it contains `settings.gradle`, root `build.gradle`, or sibling `*-module-*` directories. If the user provides a single `*-module-*` directory, search upward and use its parent when that parent has QS sibling modules or settings. Otherwise search upward first, then one level downward from the current directory.
- `<project-name>`: the logical QS project name. Derive it from discovered child project names first by taking the shared prefix before `-module-`, `-run`, `-build`, or `-lib-`, such as `quicksilver` from `quicksilver-module-main` and `quicksilver-run`. Fall back to the basename of `<project-root>` only when no reliable shared prefix can be derived.
- `<module-list>`: all QS module project directories found under `<project-root>`, such as `ecp-module-main` and `mes-module-order`.
- `<output-md>`: Markdown output path. Default to `<project-root>/docs/<project-name>-api-discovery.md` unless the user specifies another path.
- `<scan-scope>`: default to all discovered modules. Limit to one module or a subset only when the user explicitly requests that scope.
- `<has-entity-api-source>`: whether the current scanned project actually contains `EntityApiImpl.java` source in its reachable module source tree. Use this only as source-evidence context inside concrete route sections; it must not create a standalone shared inherited-contract section.

If no `*-module-*` project can be found, ask the user for the QS project root. If exactly one module is found, still produce the same API calling-reference structure.

Example: when `<project-root>` is `quicksilver-7.1-task1` and child projects include `quicksilver-module-base`, `quicksilver-module-main`, and `quicksilver-run`, derive `<project-name>` as `quicksilver`, scan both modules, and write the report to `quicksilver-7.1-task1/docs/quicksilver-api-discovery.md`.

## Fast Export Tool

The skill includes `scripts/export_qs_api.py` for fast first-pass API exports.

Use it when the user asks to export QS APIs and a complete Markdown reference is needed quickly:

```sh
python3 scripts/export_qs_api.py <project-root>
python3 scripts/export_qs_api.py <project-root> <output-md>
```

The script:

- Discovers QS module projects from `settings.gradle` and immediate `*-module-*` child directories.
- Accepts either the QS parent project root or a single `*-module-*` directory; module-directory inputs are normalized to the parent QS project when possible.
- Parses Java `@Api` handlers under `api.impl` by scanning only `*ApiImpl.java` files on the primary pass. It must not build a full-project `*.java` index before API classes are known.
- Uses annotation-first extraction for very large `ApiImpl` files, classes with many `@Api` handlers, or handlers with very large method bodies: keep route, token, request/response format, and `@Api.input` / `@Api.output`, but skip deep method-body field scanning so one complex handler cannot dominate export time.
- Keeps memory bounded by compacting records before rendering, clearing runtime caches after discovery, avoiding cache keys that retain full source or method-body strings, and streaming the Markdown report to disk instead of building one giant output string.
- Parses `TsUnit` insert/update SQL metadata under `src/main/resources/QS-MODULE/data/sql/default`, including `init.sql` when present.
- Parses `TsField` insert SQL metadata before Java field-shape inference and builds a `FUnitId -> fields` index. When a request object is read with `JsonUtil.getObject(...)` or `JsonUtil.getObjectArray(...)` and its class can be matched to the current or another known `TsUnit`, expand the object fields from `TsField` metadata first. When any API handler belongs to a concrete unit and calls `JsonUtil.getObject(...)` or `JsonUtil.getObjectArray(...)` with `getModelClass()`, use the concrete unit being exported and expand from that unit's `TsField` rows regardless of the request field name. When a response field is produced by `FormHome.getService().getDataJson(...)`, treat it as the current unit's model data and expand the response object from the concrete unit's `TsField` rows. When a response field is produced by `ListHome.getService().getDataJson(...)`, treat it as an array of the current unit's model data and expand the array element fields from the concrete unit's `TsField` rows. Use `FName`, `FTitle`, `FType`, `FRequired`, and `FSize` to render the nested contract, and mark the field source as `TsField metadata`. If the class cannot be matched to a unit, keep the existing Java-class shape inference or leave the object dynamic instead of guessing.
- Merges `@Api.input` and `@Api.output` with code-derived fields conservatively: when handler code has already produced request or response fields, annotation metadata may supplement only same-name fields and must not add different field names. When no code-derived fields are available, annotation fields may be used as fallback.
- Renders request/response object detail tables at the end of the current API block after both `請求內容` and `回應內容`, and emits each object type title only once per API even when multiple fields reference the same type.
- When a response list field such as `items` is expanded from current-unit metadata, renders the parent type as `ConcreteModel[]` and uses the concrete model name, such as `AccountIdentityModel`, as the object detail table title instead of generic labels such as `Items[]`.
- Render array types in table cells with square-bracket notation, for example `ConcreteModel[]`, `uuid[]`, or `file[]`, so Markdown previews and raw text show the same type.
- Parses all `.sql` files under bundled QS base directory `assets/templates/api-discovery/sql/` before module SQL. These template SQL files provide compact QS product metadata, primarily `TsUnit` rows and any focused `TsField` rows needed for API discovery, so product units such as `Qs.User` and `Qs.Department` can be resolved even when an application module such as ECP does not redefine them. Module SQL metadata is merged afterward and may add or override application-specific units.
- Parses each module project's own `src/main/resources/QS-MODULE/data/sql/default/init.xml` when present and uses its `<version>` as that module's SQL initialization baseline. Baselines are per module and must not affect other module projects.
- When `init.sql` exists without `init.xml`, scan only `init.sql` because it is treated as the complete SQL snapshot.
- When an `init.xml` baseline exists, scan `init.sql` plus only versioned `.sql` files whose filename version is greater than the baseline; skip versioned `.sql` files at or below the baseline because their contents are already represented by `init.sql`.
- Expands inherited `EntityApiImpl` handlers into concrete API routes when the bound unit has `FApiEnabled=1`.
- Skips inherited `BusinessEntityApi` workflow routes (`submit`, `assign`, `execute`, `finish`, `discard`, and `revise`) unless the concrete unit has `FSupportWorkflow=1`; concrete `@Api` handlers declared directly on the unit's own API class are still exported through the normal concrete-handler path.
- Continues analysis for confirmed `object` and `object[]` fields when the handler exposes concrete evidence, including local/inline `JSONObject` construction, `JsonUtil.toJsonObject(...)`, `JsonUtil.getObject(...)`, `JsonUtil.getObjectArray(...)`, and local DTO/model variables whose Java class can be resolved. When the shape is runtime-metadata-driven, keep the dynamic object row and write a clear semantic description instead of guessing fields.
- Writes the default report to `<project-root>/docs/<project-name>-api-discovery.md` when no output path is supplied.

Treat the generated Markdown as an accelerated baseline, not as the final word for every complex contract. After running the script, manually inspect APIs that rely on downstream service parsing, dynamic form/list metadata, nested object construction, full-powers servlet responses, wildcard path names that need a better parameter name than `{path}`, or any field marked as inferred/unknown.

## Discovery Workflow

1. Locate the QS parent project root.
   - If `scripts/export_qs_api.py` is available and the user wants an export rather than a deep audit, run it after resolving `<project-root>` and `<output-md>`, then review the generated report for obvious gaps.
2. Discover all module projects:
   - Prefer module names included in `settings.gradle`.
   - Also scan immediate child directories matching `*-module-*`.
   - Include a candidate only when it has `build.gradle`, `src/main/java`, or `src/main/resources/QS-MODULE`.
   - Sort module names lexicographically for stable output.
3. Derive the logical QS project name:
   - Collect discovered child project names that match `*-module-*`, `*-run`, `*-build`, or `*-lib-*`.
   - Strip the known suffix from each candidate name and compare the remaining prefixes.
   - Use the shared prefix when it is consistent across the discovered child projects.
   - If no reliable shared prefix can be derived, fall back to the basename of `<project-root>`.
4. Inspect project-level identity and dependencies:
   - `settings.gradle`
   - root `build.gradle`
   - shared Gradle convention files.
5. For each module in `<module-list>`, inspect module identity and dependencies:
   - `<module>/build.gradle`
   - `<module>/src/main/resources/META-INF/web-fragment.xml`
   - other obvious Spring, servlet, or QS config files under `src/main/resources`.
6. For each module, scan Java API entry points under `<module>/src/main/java`:
   - First scan `api/impl/*ApiImpl.java` classes and package names ending in `.api.impl`.
   - Keep the primary pass narrow: do not parse or index every `*.java` file under `src/main/java` before finding confirmed API handlers. Large modules may vendor third-party source trees, and those must not affect API discovery time.
   - In `XXXApiImpl` classes, treat every method annotated with `@Api` as a confirmed request handler.
   - Use `assets/templates/api-discovery/java/Api.java` as the contract for each `@Api` handler.
   - Skip `BaseApiImpl`, `EntityApiImpl`, `BusinessEntityApiImpl`, and `TreeEntityApiImpl` as standalone API providers in the primary export. Keep them in the Java/source index so concrete subclasses can inherit and expand their `@Api` methods.
   - If the API class extends `BaseApiImpl` directly or through another non-entity base class, resolve the chain with bundled templates when needed, but do not add entity-style inherited APIs unless the chain reaches `EntityApiImpl`.
   - If the API class extends `EntityApiImpl` directly or through another base class, add inherited `@Api` handlers from the target project's actual `EntityApiImpl.java` when available. If the chain contains deprecated `BusinessEntityApiImpl` or `TreeEntityApiImpl` and the target project does not include those source files, resolve them from bundled templates and continue to `EntityApiImpl`. If the target project does not contain `EntityApiImpl.java`, use the bundled `assets/templates/api-discovery/java/EntityApiImpl.java` template content to discover inherited methods and contracts, then expand their routes with the concrete unit prefix derived from `Home.UNIT_ID -> TsUnit.FCode`, falling back to `CACHE_REGION` only when needed.
   - Treat inherited `BusinessEntityApi` workflow suffixes (`submit`, `assign`, `execute`, `finish`, `discard`, and `revise`) as conditional APIs. Expand inherited versions only for concrete units whose effective `TsUnit.FSupportWorkflow=1`; skip inherited versions for units with `FSupportWorkflow=0`, `null`, empty, or missing. If the concrete API class itself declares one of these suffixes with `@Api`, keep that concrete handler and do not apply the workflow-support gate to it.
   - Emit those inherited handlers as concrete APIs for each matching unit and concrete API class. Do not leave them only in a shared `EntityApiImpl` template section.
   - Put inherited request/response details or concise inherited-handler notes inside each concrete route's path-headed section.
   - Do not include a standalone shared `EntityApiImpl` inherited-contract section, even when the current scanned project contains `EntityApiImpl.java` source.
   - If the current scanned project does not contain `EntityApiImpl.java` source, still keep only the concrete inherited routes and use the fallback or external inherited source evidence for validation. Do not render that evidence as a `基本資訊` row.
   - If the API class does not extend `EntityApiImpl` and instead stays on `BaseApiImpl` or another non-entity base class, do not add inherited entity APIs.
   - If the concrete class overrides an inherited API suffix, use the concrete method and mark the inherited method as overridden.
   - If SQL metadata, bundled template SQL, and resolvable superclass source cannot identify a unit, infer the unit from the unresolved `extends` superclass FQCN before falling back to the current subclass path. `com.jeedsoft.quicksilver...` implies product prefix `Qs`; otherwise skip common domain/organization prefixes such as `com.xxx`, `org.xxx`, `net.xxx`, or `cn.xxx`, and use the segment after the second dot as the product prefix with initial uppercase. For example, `com.jeedsoft.quicksilver.user.api.impl.UserApiImpl` implies `Qs.User` and route prefix `qs/user`, `com.chainsea.abc.order.OrderApiImpl` implies `Abc.Order` and route prefix `abc/order`, and `org.foo.mes.order.OrderApiImpl` implies `Mes.Order` and route prefix `mes/order`.
   - Resolve additional Java source lazily only when a confirmed API handler needs superclass, model/DTO, Home, or nested field-shape evidence.
   - Then scan fallback packages or directories named `api`, `action`, `controller`, `rest`, `web`, `endpoint`, or similar only when the `XXXApiImpl @Api` pass does not cover the requested API surface or the user asks for a broader audit.
   - Treat classes ending in `Api`, `ApiImpl`, `Action`, `ActionImpl`, `Controller`, `Resource`, or `Endpoint` as fallback candidates only when no `XXXApiImpl @Api` handler covers the API.
   - Methods with mapping or exposure annotations such as `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`, `@Path`, `@WebServlet`, `@QsApi`, or project-specific equivalents.
   - Public methods in API/action classes even when no route annotation is present are candidates, not confirmed handlers, unless correlated with `@Api` or strong metadata evidence.
7. For each module, scan QS unit metadata SQL under `<module>/src/main/resources/QS-MODULE/data/sql/default` when present:
   - If `init.xml` exists next to `init.sql`, parse its `<version>` and record it as that specific module project's SQL initialization baseline in the report summary. Do not reuse one module's baseline for another module.
   - If `init.sql` exists but `init.xml` does not, treat `init.sql` as the complete SQL snapshot and do not scan additional `.sql` files in that SQL tree.
   - With an `init.xml` baseline, scan that module's `init.sql` and only that module's higher-version incremental SQL files. Always use the actual parsed `<version>` from the same module's `init.xml` as the threshold: files at or below that version are covered by that module's `init.sql` and should be skipped; files above that version should still be scanned.
   - `insert into TsUnit` and `update TsUnit` statements for `FId`, `FCode`, `FName`, `FApiEnabled`, `FApiClassName`, Java class binding fields, edit type, key field, name field, and module relation.
   - Apply later `update TsUnit` statements to earlier unit metadata when they target the same row by `FId`, `FCode`, or another clear unit locator. Use the final effective values when deciding API exposure.
   - `insert into TsField` statements for each unit's entity fields. Build a per-unit field index from `FUnitId` and use it to describe `JsonUtil.getObject(...)` / `JsonUtil.getObjectArray(...)` request bodies when the object class maps to a known unit. For any API bound to a concrete unit, resolve `getModelClass()` object reads against the concrete unit currently being exported, regardless of whether the handler comes from `EntityApiImpl` or another API class and regardless of the request field name. Prefer `TsField` over plain Java class fields because it reflects the QS entity fields that callers can normally submit.
   - Treat `TsUnit.FApiEnabled=1` as evidence that the unit's API is enabled. If `FApiEnabled` is missing or not `1`, still list concrete `@Api` handlers declared in the bound API class, but mark availability as `false` unless `@Api.isAlwaysEnabled=true`.
   - When `FApiEnabled=1` and `FApiClassName` is empty or unset, treat an entity-style unit as using inherited/default `EntityApiImpl` APIs by default. Expand inherited APIs into concrete routes using the unit's derived unit prefix from `Home.UNIT_ID -> TsUnit.FCode`, falling back to `CACHE_REGION` only when needed.
   - When `FApiClassName` is set, locate that API class and analyze its concrete `@Api` handlers. If `FApiEnabled=1`, also analyze inherited APIs from its superclass chain and emit both kinds only when that superclass chain actually includes `EntityApiImpl`; otherwise emit only the concrete handlers declared on the non-entity API class unless a project-specific base class defines additional APIs. If `FApiEnabled` is missing or not `1`, list concrete handlers from that API class as unavailable and do not expand default inherited APIs unless evidence proves runtime availability.
   - For inherited routes whose behavior is unchanged from `EntityApiImpl`, record that fact in the concrete route's `基本資訊`; do not point to a separate shared inherited-contract section.
   - Related `TsPrivilege`, `TsMenu`, `TsPage`, `TsToolItem`, and `TsToolSubItem` rows when they clarify API visibility, page actions, or permissions.
   - Helper calls such as `setFormFields`, `setListFields`, and `setQueryFormFields` only when useful for request/response or UI-operation context.
8. Correlate Java and SQL within each module first:
   - Match `TsUnit.FApiClassName`, `FActionClassName`, `FServiceClassName`, `FHomeClassName`, and class names in Java.
   - Use `TsUnit.FApiEnabled` to decide whether a unit's API exposure is enabled.
   - If `TsUnit.FApiClassName` is empty for an API-enabled entity-style unit, resolve the unit prefix from `FHomeClassName`, `Home.UNIT_ID -> TsUnit.FCode`, fallback `CACHE_REGION`, Java conventions, or unit metadata and expand default inherited `EntityApiImpl` APIs into concrete routes for that unit.
   - If `TsUnit.FApiClassName` is empty for a non-entity unit, do not assume `EntityApiImpl`; export only APIs confirmed from the unit's actual base class and concrete handlers.
   - If `TsUnit.FApiClassName` is set, locate and analyze that class as the unit's concrete API class, then expand inherited `EntityApiImpl` APIs into concrete routes for that same class and unit unless a concrete override replaces them.
   - When an application API class extends a QS product API class, such as `com.chainsea.ecp.user.api.impl.UserApiImpl extends com.jeedsoft.quicksilver.user.api.impl.UserApiImpl`, bind the application subclass to the QS base unit whose `FApiClassName` matches the superclass. Do not expect the application module SQL to contain `Qs.User` or `Qs.Department`; those come from the bundled/base QS metadata.
   - Match API implementation constructors and superclass arguments to Home classes, such as `super(UserHome.UNIT_ID, UserModel.class)`.
   - Inspect matched Home classes for `CACHE_REGION` to derive the openapi unit path.
   - Match unit code prefixes such as `Qs.*`, `Ecp.*`, or `Mes.*` to nearby package and class naming.
   - Match action/API method names to toolbar buttons, privileges, or page operations when naming is strong enough.
9. Correlate across modules only when evidence points outside the current module:
   - Java imports reference another module package.
   - Gradle dependencies indicate an API class lives in another sibling module.
   - SQL class binding points to a package not present in the current module.
10. Inspect request and response shapes:
   - Prefer actual handler code behavior over `@Api.input` and `@Api.output`. Treat annotation attributes as secondary evidence only.
   - When `@Api.isFullPowers = true`, allow `void` return type and analyze servlet request/response usage as the handler contract. Treat token requirement as not applicable, regardless of `@Api.isTokenRequired`.
   - If handler code calls `getTokenId()` on the method parameter typed as `ApiContext`, such as `ac.getTokenId()` or `context.getTokenId()`, report `Token required=true` and add the automatic `Authorization` header even when `@Api.isTokenRequired=false`, because the handler uses the caller token for business behavior. Do not count arbitrary non-`ApiContext` `getTokenId()` calls, static `ApiContext.getTokenId()` calls, or local-variable calls. In `基本資訊`, write a concise explanation such as `true（處理器程式碼呼叫 ApiContext 參數的 getTokenId()；覆蓋 @Api.isTokenRequired=false）`.
   - Infer request body fields from `JsonUtil.get*`, `JsonUtil.opt*`, `JSONObject.get*`, and `JSONObject.opt*` calls on the `JSONObject` returned by `ac.getRequestJson()`, whether or not `@Api.input` is present.
   - For inherited `EntityApiImpl` list APIs, follow the fixed list-query call chain from `list/getList` to `getListDataSet`, `getListSelect`, `getListFilter`, and `getListOrder`, then into `ListQueryUtil.getSelect`, `ListQueryUtil.getFilter`, and `ListQueryUtil.getOrder`. Include request fields read there, such as `fieldNames`, `listId`, `schemaId`, `keyword`, `masterEntityId`, `relationId`, `entityBoxFieldId`, `listFilterCode`, `filtered`, `conditions`, `includeSelf`, `includeIndirectSub`, `forms`, `listFilterArgs`, and `order`, in addition to paging fields read directly by `EntityApiImpl`. Treat the `forms` field read by `ListQueryUtil.getFilter` as the current concrete unit model, render its type as the current `XxxModel`, and expand its fields from the current unit's `TsField` metadata when available.
   - When handler code confirms one or more request or response fields, use `@Api.input` / `@Api.output` only to supplement same-name fields; do not add annotation-only fields with different names. If handler code confirms no fields for that side, annotation fields may be used as fallback.
   - Treat the string key argument in `JsonUtil.get*(args, "<field>", ...)`, `JsonUtil.opt*(args, "<field>", ...)`, `args.get*("<field>")`, and `args.opt*("<field>", ...)` as the request body property name.
   - Use the helper method name to infer the body property type, for example `getUuid` -> `uuid`, `getUuidArray` -> `array` with `uuid` element type, `getString` or `optString` -> `string`, `getInt` or `optInt` -> `int`, and `getJSONObject` or `optJSONObject` -> `object`.
   - When a Request Body or Response Body field is `object` or `object[]`, continue analysis into the object's construction or consumption when evidence is available. If the object shape can be named, use a meaningful object type such as `User` or `WfVersionModel` in the parent field row, then collect a separate object-field table for rendering at the end of the current API block. This rule applies equally to request fields and response fields. Use dotted paths such as `data.name` or array-element paths such as `items[].id` only when a separate object table would be less clear.
   - For response objects built from a local `JSONObject`, follow chained or sequential `put(...)` / `JsonUtil.put(...)` calls on that object before it is inserted into the result. Example: if `JSONObject userJson = new JSONObject().put("id", user.getId()).put("name", user.getName())` is later returned as `result.put("user", userJson)`, list parent field `user` as type `User`, then add a `User` object table containing `id` and `name`.
   - For inline response object construction, expand the object the same way. Example: `result.put("user", JsonUtil.toJsonObject("id", user.getId(), "name", user.getName()))` must not remain as a generic `object`; list parent field `user` as type `User`, then add a `User` object table with `id` and `name`.
   - For object fields parsed into a model or DTO, such as `JsonUtil.getObject(args, "data", getModelClass())`, inspect the resolved model class and metadata-backed field configuration when available. Use the model/DTO name as the object type when the shape is concrete; if concrete fields are metadata-driven or cannot be resolved, keep the object row and describe that its properties come from the unit model, form/list fields, or runtime metadata.
   - For response object fields built with `FormHome.getService().getDataJson(...)`, such as `result.put("data", FormHome.getService().getDataJson(...))`, treat the field as current-unit model data and expand it from the concrete unit's `TsField` rows.
   - For response array fields built with `ListHome.getService().getDataJson(...)`, such as `result.put("items", ListHome.getService().getDataJson(...))`, treat the field as an array of current-unit model data and expand the element fields from the concrete unit's `TsField` rows.
   - When such a response array can be tied to a concrete model, render the parent field type as `ConcreteModel[]` and use `ConcreteModel` as the object-field table title. Avoid generic table titles such as `Items[]` when the concrete item model is known.
   - For dynamic layout responses such as `FormHome.getService().getDataJson(...)` or `ListHome.getService().getDataJson(...)`, expand fields only when the selected form/list fields are resolved from SQL or source constants. Otherwise keep the object/array row and state that the object's properties are dynamic and determined by `fieldNames`, form/list configuration, or unit metadata.
   - Treat `opt*` calls as optional by default: `required=false`, even when no explicit default is supplied. Use the explicit default argument when present.
   - Use explicit default arguments such as `null`, `false`, `0`, `""`, or a constant value as default-value clues. When a default value is a constant such as `LanguageHome.EN_US` or `LoginOptions.FROM_APP`, resolve the constant declaration and write the concrete value such as `en-us` or `app` in the report. Keep the constant name only when the concrete value cannot be resolved from source. When the field is enum-like or backed by a group of constants, add only the concrete possible values to the field description when they can be found from source, such as `可能值：en-us, zh-cn, zh-tw`, `可能值：web, app`, or `JSON("json")` rendered as `可能值：json`; do not render `EN_US=en-us` or `JSON=json` mappings, and do not include QS metadata constants such as `CACHE_REGION`, `UNIT_ID`, `VERSION`, or `SERIAL_VERSION_UID` as possible values. When a helper call has no default argument, uses a required-style getter such as `JsonUtil.getUuid(args, "entityId")` or `args.getString("name")`, or an `@ApiAttribute.required = true`, mark the field as required. Optional-style calls with defaults, such as `JsonUtil.getUuid(args, "entityId", null)` or `args.optString("captcha", null)`, mean the field is optional with that default.
   - For `JsonUtil.getObject(args, "data", getModelClass())` and similar object helper calls where the third argument is the target model class rather than a default value, mark the field as required. For `JsonUtil.getObject(args, "data", null, getModelClass())`, mark it optional with default `null`.
   - When handler code confirms a field and `@Api.input.required=true` also declares it required, the annotation may supplement the code-derived field by setting `Required=true`; do not use `@Api.input.required=false` to weaken a field that code proves required.
   - For `JsonUtil.getXXXArray(args, "field")`, including helpers such as `JsonUtil.getUuidArray(args, "userIds")`, the field is required: record `Required=true` with an empty default value.
   - For `JsonUtil.getXXXArray(args, "field", boolean)`, including helpers such as `JsonUtil.getStringArray(args, "fieldNames", false)` and `JsonUtil.getUuidArray(args, "ids", true)`, the third boolean argument represents the field's `required` flag, not a default value. Therefore `false` means `Required=false` with an empty default value, and `true` means `Required=true` with an empty default value.
   - If an `opt*` field is later checked by explicit validation that rejects null, blank, or missing values, record `required=true` and cite the validation code as evidence.
   - Infer response fields from `JsonResult.put(...)`, `XmlResult.put(...)`, chained `new JsonResult().put(...)`, `putAll(...)`, `TextResult.setText(...)`, `FileResult` constructors/setters, or the handler return type, whether or not `@Api.output` is present.
   - When a response field comes from a local variable or expression with an obvious Java type, use that actual type as the primary response type evidence. Examples: `UUID attachmentId` -> `uuid`, `JSONObject userJson` -> `object`, `JSONArray items` -> `array`, `String name` -> `string`, `int count` -> `int`, `boolean success` -> `boolean`.
   - Treat obvious count/size/total fields and methods as `int`, including camelCase names such as `recordCount`, `totalCount`, and expressions such as `pds.totalSize()` or `pds.getPageCount()`.
   - Do not use `unknown` lightly. Before marking a field as `unknown`, trace local variable declarations, method return types, `@ApiAttribute` metadata, helper method names, constants, and obvious field names such as `id`, `*Id`, `count`, `pageCount`, `recordCount`, `items`, and `buttons`. Use the concrete type when evidence supports it; use `unknown` only when these sources still do not provide enough evidence.
   - For all APIs, infer request parameters from `request.getParameter(...)`, `getParameterValues(...)`, `getHeader(...)`, `getCookies()`, `getSession(...)`, `getReader()`, and `getInputStream()` usage when the handler uses `ac.getRequest()`. Treat `request.getParameter("field")` as a request parameter named `field`; mark it required only when validation rejects missing or blank values.
   - When handler code calls `ApiContext.getFileItem()` or `ApiContext.getFileItems()`, record the request body as uploaded file content even if no `@Api.input` declares it. Use `file` for `getFileItem()` and `files` with type `file[]` for `getFileItems()`, and mark the request format as `multipart/form-data` unless an explicit non-default `@Api.requestFormat` is present. In generated notes, explain that frontend callers use `FormData`: ordinary parameters are commonly grouped into an `args` JSON string, such as `formData.append("args", JSON.stringify({life: "temp"}))`, and may also be appended directly; file field names such as `file1` and `file2` follow QS upload parsing conventions. For `getFileItem()`, callers may still append multiple files, but the handler reads the first uploaded file.
   - Infer path parameters from wildcard API paths and `ApiContext.getPath()` usage. Derive the parameter name from the local variable or downstream usage when possible. For example, `String code = context.getPath()` may export `{code}`, while `String path = context.getPath()` may export `{path}`. Record wildcard path parameters as required.
   - For full-powers APIs, infer response behavior from `response.sendRedirect(...)`, `addCookie(...)`, `setHeader(...)`, `setStatus(...)`, `sendError(...)`, `setContentType(...)`, `getWriter()`, and `getOutputStream()`. Record response type as redirect, cookie/header mutation, status/error, text/body stream, or mixed servlet response.
   - Use `@Api.input` only to supplement missing field names, types, or descriptions when handler code does not provide enough evidence.
   - Use `@Api.output` only to supplement missing response metadata when handler code does not provide enough evidence.
   - Cross-check `@Api.input` names against `JsonUtil.get*`, `JsonUtil.opt*`, `JSONObject.get*`, and `JSONObject.opt*` calls on `ac.getRequestJson()` and treat handler code as the source of truth when they differ.
   - Cross-check `@Api.output` names against `JsonResult.put(...)`, `XmlResult.put(...)`, `putAll(...)`, text, or file response construction and treat handler code as the source of truth when they differ.
   - Recognize `JsonUtil.getUuidArray`, `getStringArray`, and similar array helpers as array request fields; record the element type when it can be inferred from the helper name.
   - Method parameters and return types.
   - Model, DTO, VO, Query, Request, Response, and Result classes used by the entry point.
   - Validation annotations and exception/error resource references where visible.
11. Trace service/home/DAO calls when needed:
   - If the handler parses fields locally and passes typed values, record those fields and summarize downstream calls without deep parameter tracing.
   - If the handler passes raw `JSONObject`, `ApiContext`, `HttpServletRequest`, `Map`, `Filter`, or another unparsed request carrier to service/home/DAO, inspect the callee method.
   - In callee methods, apply the same request-field extraction rules for `JsonUtil.get*`, `JsonUtil.opt*`, `JSONObject.get*`, `JSONObject.opt*`, servlet request access, map lookups, and validation checks.
   - Follow the call chain only until request fields and required/default semantics are clear. Avoid broad service/DAO exploration unrelated to API request or response shape.
   - Cite both the handler call site and the callee field-read lines as evidence.
12. Write or update the Markdown report.

Prefer `rg` for scanning. Useful starting searches:

```sh
rg --files <project-root> | rg '/[^/]+-module-[^/]+/(build.gradle|src/main/java|src/main/resources/QS-MODULE)'
rg --files <module>/src/main/java | rg '/api/impl/[^/]+ApiImpl\\.java$'
rg -n "@Api\\b|import .*\\.Api;|class .*ApiImpl\\b|public .*\\(" <module>/src/main/java --glob '*ApiImpl.java'
rg -n "class .*?(Api|ApiImpl|Action|ActionImpl|Controller|Resource|Endpoint)\b|@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|Path|WebServlet|QsApi)\b|public .*\\(" <module>/src/main/java
rg -n "(insert|update)\\s+.*TsUnit|FApiEnabled|FApiClassName|FActionClassName|FServiceClassName|FHomeClassName|insert\\s+into\\s+TsPrivilege|insert\\s+into\\s+TsMenu|insert\\s+into\\s+TsTool(Item|SubItem)" <module>/src/main/resources/QS-MODULE/data/sql/default
```

Adjust patterns to the target project's conventions after inspecting the first matches.

## API Record Fields

For each discovered API, capture as many of these fields as evidence supports:

- API name: human-readable operation or class/method name.
- Module: module project name.
- Unit ID: `TsUnit.FId`, Java `UNIT_ID`, or correlated unit metadata.
- Unit code: `TsUnit.FCode` when correlated.
- Unit name: `TsUnit.FName` when correlated.
- API enabled: `TsUnit.FApiEnabled`, when available.
- API class: `TsUnit.FApiClassName`, default/inherited when empty and API is enabled.
- Provider API class: the Java class that provides the handler, such as `UserApiImpl`; for inherited handlers, record both the concrete unit API class and inherited source class such as `EntityApiImpl`.
- Always enabled: `@Api.isAlwaysEnabled`, defaulting to `false` when omitted.
- Availability: `true` when `TsUnit.FApiEnabled=1` or when the concrete handler has `@Api.isAlwaysEnabled=true`; `false` when the handler is declared in the API class but the unit API is disabled and the handler is not always-enabled.
- Module project name: the discovered QS module project that provides the API class, such as `ecp-module-main`; include it in generated `基本資訊` as `項目名稱` so parent projects with multiple module projects can distinguish API ownership.
- Entry type: `XXXApiImpl @Api handler`, REST controller, QS action, servlet, public Java API candidate, metadata-only unit, or inferred.
- Inheritance: direct handler, inherited from `EntityApiImpl`, or concrete override of inherited API.
- Route or invocation path: confirmed annotation route or inferred QS invocation path.
- OpenAPI route: derived full route path such as `openapi/qs/user/token/apply`, with evidence from `@Api.value` and Home `CACHE_REGION`.
- Request format: `@Api.requestFormat`, defaulting to `default` when omitted.
- Response format: `@Api.responseFormat`, defaulting to `default` when omitted.
- Token required: use handler code first, then `@Api.isTokenRequired` defaulting to `true` when omitted. If handler code calls `getTokenId()` on the method parameter typed as `ApiContext`, mark token required as `true` even when `@Api.isTokenRequired=false`. Do not count arbitrary non-`ApiContext` `getTokenId()` calls, static `ApiContext.getTokenId()` calls, or local-variable calls. For `@Api.isFullPowers=true`, mark token not applicable because the developer handles request/response directly.
- API flags: `isInherited`, `isFullPowers`, and `isAlwaysEnabled`.
- Java source: handler class and method with file path only, preferring `XXXApiImpl` methods annotated with `@Api`. In generated `基本資訊`, put the fully qualified class name in `API 提供類`, such as `com.jeedsoft.quicksilver.account.api.impl.AccountApiImpl`, and put only the Java method name in `處理器`, such as `modifyPassword` or `getList`. Do not render `處理器` as `ClassName#methodName`, and do not include separate `源碼`, `源碼依據`, or source-evidence rows in generated `基本資訊`.
- Request model: actual request body fields, servlet request parameters/headers/cookies/session fields, DTOs, model classes, query objects, or raw request types first; use `@Api.input` only as secondary support.
- Response model: actual response construction, concrete `ApiResult` type, servlet response behavior, return type, wrapper type, DTO/model classes, or void first; use `@Api.output` only as secondary support.
- Service/home/DAO flow: downstream class or method calls visible from the entry point, including callee field-read evidence when raw request carriers are passed through.
- Cross-module references: sibling module dependencies or external class bindings when relevant.
- Permission/menu/page clues: related `TsPrivilege`, `TsMenu`, `TsPage`, `TsToolItem`, or `TsToolSubItem` rows.
- Status: confirmed, unavailable, inferred, or metadata-only.
- Notes: assumptions, missing links, unusual behavior, or risks.

For shared inherited `EntityApiImpl` contracts:

- Do not create a standalone top-level `Shared EntityApiImpl Contract` section in the generated Markdown report.
- Still record every concrete inherited route in every applicable report, with its module, unit, concrete provider API class, inherited handler class, and reference target in that route's `基本資訊` table.
- For unchanged inherited behavior, either write the inherited request/response fields directly in the concrete route section or add a concise note in that route's `基本資訊`; do not move the route details into a separate shared-contract catalog.

Do not invent routes, request fields, or response fields. If only Java method names are available, record the method as a callable API candidate and mark the route/status as `inferred` or `metadata-only` as evidence supports. For inherited `EntityApiImpl` methods, if the concrete API class, enabled unit, and unit prefix can all be resolved, you must export the concrete inherited routes instead of leaving them as generic placeholders.

## Markdown Output Format

Use this structure unless the user requests another format:

Write only explanatory prose in the generated Markdown report in Traditional Chinese. Keep code identifiers, class names, method names, package names, field names, SQL column names, API paths, data types, enum/status values, boolean values, and table cell values from source evidence unchanged.
In generated tables, localize generic source labels to Traditional Chinese. For example, use `處理器程式碼` instead of `handler code`; keep concrete source identifiers such as `@Api`, class names, method names, and file paths unchanged.

The generated file is an API calling reference for frontend development with AI assistance, not a catalog-style inventory report. Its purpose is to let a human or AI quickly identify every API and know how to compose the URL, pass path/query parameters, pass headers, send the request body, and consume the response body.

Optimize the output for stable AI parsing:

- Every exported API must appear exactly once as its own route-led block.
- Each API block must begin with the HTTP method and API path shown in backticks, for example ``## `POST openapi/qs/user/token/apply` ``.
- Put `---` between adjacent API blocks so a reader or AI can reliably split the document into APIs.
- Keep the call-detail block labels stable and in this order when present: `基本資訊`, `路徑參數`, `請求參數`, `請求標頭`, `請求內容`, `回應內容`.
- Keep table column names stable across APIs. Field tables should use `欄位`, `類型`, `是否必填`, `預設值`, `來源`, and `說明`; response body tables should use `欄位`, `類型`, `是否必填`, `來源`, and `說明`.
- Render array type cells with square-bracket notation such as `uuid[]` or `AccountIdentityModel[]`; avoid raw generic notation such as `array<uuid>` because many Markdown previewers treat `<...>` as HTML.
- Keep all call information for an API inside that API block. Do not place request/response contracts in separate shared sections or catalogs that require cross-referencing.
- Omit empty call-detail blocks instead of writing placeholder rows such as `無`.

Use this concise structure exactly:

- Start with the prominent Markdown heading `# 報告摘要`:
  - 專案根目錄: show the logical project name only, not a local absolute filesystem path.
  - 掃描模組
  - API 總數
  - 格式: `路徑優先精簡 API 參考`
- Then add the prominent Markdown heading `# 完整 URL 拼接` before API sections:
  - 完整 URL = `{服務根位址}/{API 路徑}`
  - `{服務根位址}` 需包含協定、網域或 IP、連接埠，以及部署 Context Path（如有），例如 `http://localhost:6080/quicksilver`
  - `{API 路徑}` 即下方各 API 區塊標題中 HTTP 方法後面的路徑，例如 `POST openapi/qs/user/token/apply` 中的 `openapi/qs/user/token/apply`
  - 以上述範例拼接，完整 URL 為 `http://localhost:6080/quicksilver/openapi/qs/user/token/apply`
- After the URL section, write `# Token API` first for token-operation routes, then `# 一般 API` for all remaining routes. Do not output an API catalog, do not group APIs by class, and do not duplicate the same API in a separate details section.
- Make the HTTP method plus OpenAPI route or absolute API path the most visible label for each API block. Prefer a natural heading such as ``## `POST openapi/qs/user/token/apply` `` or ``## `GET openapi/qs/file/download/{path}` `` and separate long API blocks with `---` when it improves scanning. Do not hard-code one required heading level; choose a clear hierarchy that keeps the URL, request fields, and response fields close together.
- Do not create top-level sections named `Quicksilver API Discovery`, `Scope`, `Summary`, `Shared EntityApiImpl Contract`, `Unit API Bindings`, `Unresolved Bindings`, or `Exported Routes` unless the user explicitly asks for that alternate format. The allowed prominent API grouping headings are `# Token API` and `# 一般 API`.

Under each API path, include only non-empty call-detail blocks in this order. Use Traditional Chinese display labels for these blocks: `基本資訊`, `路徑參數`, `請求參數`, `請求標頭`, `請求內容`, and `回應內容`. Use natural labels such as bold text (`**基本資訊**`) or headings, whichever keeps the surrounding context easiest to read; do not force these labels to be first-level or second-level headings. Keep English terms such as `Request Body`, `Response Body`, `Header`, or `Parameter` only when quoting source code, annotations, or framework concepts; do not use them as output section labels.

Infer a short API purpose using explicit developer text first. Use `@Api.description` as the first priority. If it is empty and the method has a JavaDoc, block comment, or consecutive line comments directly attached to its annotation/signature, use the first non-empty comment line as the second priority. A method comment may appear immediately before `@Api` or between `@Api` and the method signature. Ignore decorative separator comments and paired separator group blocks, such as `// ----------` / `// for BusinessEntityApi` / `// ----------`; the middle line is a group label, not an API purpose. Ignore comment lines that start with `@`, such as `@deprecated use EntityApiImpl`, and continue looking for a non-`@` line. If neither exists, infer the purpose as a best-effort description from the final API path. Identify action words such as token/upload/download/transfer/status/login/logout/password/import/export, translate only the needed business object words with a small domain glossary, and render them through natural Traditional Chinese action templates. When working interactively and an unknown business word cannot be translated from code, metadata, or the local glossary, it is acceptable to search the web for the term's public technical/business meaning, then use the confirmed meaning conservatively and prefer adding durable translations back into the glossary or script rules. Then use explicit handler behavior, `@Api.value` / `@Api.path`, unit name, return type, and request/response construction as supporting evidence. If a precise business purpose cannot be inferred from route or metadata, fall back to translating the current `@Api` handler method name into Traditional Chinese. Support both verb-first method names, such as `updateMessage` -> `更新消息。`, and object-plus-verb names, such as `agentIsWorkTime` -> `判斷客服是否工作時間。`. Do not output untranslated or camelCase fallback phrases such as `處理downloadfax`; keep the purpose conservative or omit it when no natural translation is possible. For non-entity API classes or units, do not use the unit name as the business target in purpose text. Write the purpose as a short unlabeled paragraph immediately below the API heading and before `基本資訊`; every line of this paragraph must be indented by two full-width spaces, for example `　　新增商務訂單。`.

**基本資訊**

List compact metadata as a two-column table. Include fields such as:

- 是否可用: `true` or `false`
- 分析狀態: use one compact value with a short explanation in parentheses, such as `confirmed（已確認）`, `inferred（根據繼承、設定或命名規則推斷）`, `metadata-only（僅發現元資料，未確認具體處理邏輯）`, or `unavailable（API 已發現，但目前設定下不可用）`.
- 項目名稱: the QS module project name that provides the API class, such as `ecp-module-main`; use `未確認` only when no concrete module project can be resolved.
- 單元 ID, 單元編碼, 單元名稱 when available
- API 提供類: fully qualified class name, such as `com.jeedsoft.quicksilver.account.api.impl.AccountApiImpl`.
- HTTP 方法: `GET` or `POST`, matching the method shown before the path in the API block title.
- 處理器: method name only, such as `modifyPassword`; keep the provider class in `API 提供類` and do not repeat it as `ClassName#methodName`.
- 入口類型: identify how the route is provided. Use `具體 @Api handler` for methods declared directly on the concrete API class, `繼承 EntityApiImpl` for inherited entity APIs expanded onto a concrete unit/API class, `推斷入口` when the callable entry is inferred from metadata or naming, and `metadata-only` when only metadata exists and no concrete handler is confirmed. In generated Markdown cells, code identifiers such as `@Api` and `EntityApiImpl` may be wrapped in backticks.
- 是否需要 Token. Prefer handler code over annotation metadata. If the handler calls `getTokenId()` on the method parameter typed as `ApiContext` but `@Api.isTokenRequired=false`, write `true（處理器程式碼呼叫 ApiContext 參數的 getTokenId()；覆蓋 @Api.isTokenRequired=false）`. Do not count arbitrary non-`ApiContext` `getTokenId()` calls, static `ApiContext.getTokenId()` calls, or local-variable calls. For full-powers APIs, write `不適用（@Api.isFullPowers=true，開發者自行解析 request 並使用 response 回應）` instead of `true` or `false`.
- 起始版本 when `@Api.since` is non-empty.
- Request/Response format only when the value is neither `default` nor `json`
- `@Api.isAlwaysEnabled`, `@Api.isFullPowers`
- 返回值類型
- 響應類型, such as `json`, `file/binary`, `text`, `redirect`, `servlet`, or `empty body / framework status only`

Keep this section useful for calling and verification. Do not turn it into a catalog: avoid unit catalog rows, API class catalog rows, standalone unresolved binding rows, source-file inventory rows, dependency inventories, or module summaries inside individual API sections.
Do not invent unsupported specific business targets. Annotation paths, final API paths, unit metadata, return types, current handler method names, and simple implementation signals are usable evidence; when the exact business target is unclear, prefer route-level action/object wording and use the current handler method name translation only as the final fallback.
Do not include `源碼`, `源碼依據`, source-evidence, or `單元 Metadata` rows in generated `基本資訊`; Java source and SQL metadata should be used as evidence for status, provider class, unit code, unit name, and availability, not displayed as raw source inventory rows.

If a field category below has no confirmed fields, omit that entire section instead of writing an empty table or a `無` row.

**路徑參數**

Use a table with columns `欄位`, `類型`, `是否必填`, `預設值`, `來源`, and `說明` only when path parameters are confirmed.

**請求參數**

Use the same field table for URL query/form parameters and servlet/request parameters such as `request.getParameter(...)`.

**請求標頭**

Use the same field table for request headers such as `request.getHeader(...)`.
For APIs whose token requirement is `true`, always include a request header field `Authorization` with type `string`, required `true`, default value `Bearer {tokenId}`, source `Token 需求`, and description `Bearer Token 驗證標頭；也可用請求參數 tokenId={tokenId} 傳入`, even if the handler code does not directly call `request.getHeader(...)`. A handler call to `getTokenId()` on the method parameter typed as `ApiContext`, such as `ac.getTokenId()` or `context.getTokenId()`, is enough to make this header required unless `@Api.isFullPowers=true`. Do not add this automatic `Authorization` header for full-powers APIs, because `@Api.isTokenRequired` is not applicable when `@Api.isFullPowers=true`.

**請求內容**

List all confirmed body fields from handler code first and `@Api.input` as fallback support. Include field name, type, required flag, default value, source, and description. If handler code has already confirmed one or more request fields, use `@Api.input` only to supplement same-name fields with missing type, required, or description metadata; do not add annotation-only fields with different names because API annotations are often stale. If handler code cannot confirm any request body fields, `@Api.input` may provide fallback fields. For confirmed named object properties, set the parent field type to the object name and collect object-field tables for rendering at the end of the current API block. For unresolved dynamic objects, keep the parent object row and explain the source of its dynamic properties.
Use stable `來源` values: `處理器程式碼` for fields read or inferred from Java handler code, `API 註解` for fields taken only from annotation fallback, and `處理器程式碼 / API 註解` when annotation metadata supplements a code-confirmed field. Keep `說明` concise, for example `從 request JSON 讀取。` or `由 API 註解宣告。`.
When a request field default value references a Java constant or enum value, such as `LanguageHome.EN_US`, write the resolved concrete value in the default column when available. Resolve sibling constants or enum members from the same source class when available and append only their concrete values to `說明` as possible values, without `CONSTANT=value` mappings. Exclude QS metadata constants such as `CACHE_REGION`, `UNIT_ID`, `VERSION`, and `SERIAL_VERSION_UID`; for example `LanguageHome.CACHE_REGION = "qs_language"` must not appear in language possible values.
For unresolved QS dynamic request objects, prefer semantic descriptions over generic JSON-read descriptions. For example, `data` should use `表單資料物件；屬性依單元模型、表單欄位或執行時元資料而定。`; `form` should use `表單設定物件；屬性依表單欄位設定或執行時元資料而定。`; `forms` should use `多表單資料物件；屬性依單元模型、表單欄位或執行時元資料而定。`.

**回應內容**

List confirmed response body fields from handler code first and `@Api.output` as fallback support. Include field name, type, required flag, source, and description. If handler code has already confirmed one or more response fields, use `@Api.output` only to supplement same-name fields with missing metadata; do not add annotation-only fields with different names because API annotations are often stale. If handler code cannot confirm any response body fields, `@Api.output` may provide fallback fields. For confirmed named object properties, set the parent field type to the object name and collect object-field tables for rendering at the end of the current API block. For unresolved dynamic objects, keep the parent object/array row and explain the source of its dynamic properties. For file, text, redirect, empty-body, or servlet-managed responses with no body fields, omit this section and keep the response behavior/type in `基本資訊`.
Use stable `來源` values: `處理器程式碼` for response fields built or inferred from Java handler code, `API 註解` for fields taken only from annotation fallback, and `處理器程式碼 / API 註解` when annotation metadata supplements a code-confirmed field. Keep `說明` concise, for example `由 ApiResult.put/JSON 組裝推斷。` or `由 API 註解宣告。`.
Treat exception-object text getters such as `e.getMessage()` and `e.getStackTrace()` as `string` for API report purposes only when the receiver variable can be identified as an exception/throwable type, even when the exact Java return type is more specific.
Keep cross-file type inference lightweight and source-bounded. For `ApiResult.put(...)` values such as `SomeErrorCode.SYSTEM_ERROR`, resolve direct `public static final String/Integer/Long/Boolean/...` constants only when the defining Java source file is under one of the currently scanned module `src/main/java` trees and can be found through the current class's import or package context. Do not resolve constants from dependency jars or build a full classpath/type index for field inference; leave unavailable constants as `unknown`.
When a response field value references a Java constant or enum value, append sibling constants or enum members from that source class to `說明` as concrete possible values when they can be resolved without dependency-jar scanning, without `CONSTANT=value` mappings.
For unresolved QS dynamic response objects or lists, prefer semantic descriptions over generic JSON-build descriptions. For example, `data` should use `回應資料物件；屬性依單元模型、欄位設定或執行時元資料而定。`, and `items` should use `資料列表；項目屬性依單元模型、列表欄位或執行時元資料而定。`.

Render all collected request/response object-field tables after `請求內容` and `回應內容` inside the same API block. If multiple request or response fields reference the same object type, such as two fields both using `WfProcessModel`, emit that object type table only once in that API block. For any field whose type references one of these object tables, including array forms such as `UserModel[]`, append a concise note in `說明`, for example `請參考下文的 UserModel 欄位表。`.

Keep table cells concise. Do not output API Catalog, API Details, class-grouped sections, metadata-only unit sections, source-file inventory sections, or pending-confirmation sections unless the user explicitly asks for them.

## Update Rules

- If `<output-md>` does not exist, create it.
- If it exists and the user did not specify overwrite behavior, update the report in place while preserving any clearly user-authored notes outside the generated sections.
- When refreshing APIs for a single class, update the matching path-headed API sections in place when possible.
- If preserving manual notes is ambiguous, write a new timestamped file under the same `docs/` directory, such as `docs/api-discovery-YYYYMMDD-HHMM.md`, and tell the user why.
- Do not modify Java, SQL, Gradle, or resource files while doing API discovery unless the user explicitly asks for fixes.

## Quality Checks

Before finishing:

- Re-run the key source searches or equivalent checks after writing the report.
- Verify every confirmed API section was derived from source evidence during generation.
- Verify the file starts with `# 報告摘要`, then `# 完整 URL 拼接`, then `# Token API` if token-operation routes exist, then `# 一般 API` if general routes exist, without catalog-style sections.
- Verify inferred rows are labeled `inferred` or `metadata-only` as evidence supports.
- Verify the Markdown file exists at the requested output path.
- Report the output path and any important limitations to the user.
