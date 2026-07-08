# Unit Core Metadata

Use this reference when creating or changing the unit's business table or `TsUnit` row.

## Tables

- Business table, such as `TsTestCreateUnit`: stores the unit's actual business data.
- `TsUnit`: defines the unit itself and links metadata to the business table.

## Business Table

The business table must match `TsUnit.FTable`.

Keep these aligned:

- Primary key column and `TsUnit.FKeyField`.
- Primary key type and `TsUnit.FKeyType`.
- Display/name column and `TsUnit.FNameField`.
- Created or modified fields and the related `TsField` rows.

For new relational entity units, default `TsUnit.FKeyField='FId'`, `FKeyType='Uuid'`, and `FNameField='FName'` when the user does not specify alternatives. These defaults imply a minimal business table with `FId uuid primary key` and `FName varchar(50)`, plus matching `TsField` metadata for both fields.

## TsUnit

`TsUnit` controls the unit's identity, table binding, and major feature switches.

`Qs.Unit` itself is a QS product base unit whose business table is `TsUnit`. Its own `TsField` rows are useful examples for field titles, control types, queryability, list widths, default values, and layout spans. Product or project units may use other prefixes such as `Ecp.*` or `Mes.*`; do not force generated unit codes to use `Qs.*`.

## Unit Edit Types

`TsUnit.FEditId` selects the unit's entity/edit type. The base `Qs.Unit` seed data defines these standard types in `TsEdit`:

| `TsEdit.FId` | Name | Default | Meaning |
| --- | --- | --- | --- |
| `541c707d-79dd-4dbb-85fc-1a214fd5fce4` | `實體單元（基於關聯式資料庫）` | Yes | Entity unit whose back-end data is stored in a relational database, using bindings such as `TsUnit.FDataSource`, `FTable`, `FKeyField`, and `FNameField`. |
| `e87b8d5b-f747-4467-9754-e149bc047e1c` | `實體單元（基於 ElasticSearch）` | No | Entity unit whose back-end data is stored in ElasticSearch, using bindings such as `FEsDataSource`, `FEsIndex`, `FEsType`, `FKeyField`, `FNameField`, and `FEsDaoClassName`. |
| `8b7ebd7e-8173-4787-9e34-3d27ad4c9c29` | `非實體單元` | No | Non-entity unit. Use this for units that only need Java class method entry points and do not need ordinary entity metadata such as fields, forms, lists, pages, privileges, workflow, import, and related slave-page configuration. |

The supported editable `TsUnit` fields differ by edit type. When generating or modifying a unit, do not set type-specific fields that are not supported by the chosen `FEditId` unless an existing target project does so deliberately.

Relational and ElasticSearch entity units are both entity units. Their main difference is the back-end storage: relational entity units store data in the database table named by `FTable`, while ES entity units store data in the ElasticSearch index/type named by `FEsIndex` and `FEsType`.

Both entity and non-entity units can configure Java class bindings on `TsUnit`, and front-end AJAX can call methods through those configured classes. The difference is that entity units also carry business-storage and entity UI metadata, while non-entity units keep only the lightweight unit registration and Java method entry points.

`Qs.Condition` in `assets/templates/unit/sql/unit.sql` is the compact reference for non-entity unit generation: it only registers `TsUnit` with the non-entity `FEditId`, blank table/key/name data-binding fields where applicable, and explicit Java class bindings. It does not create a business table, `TsField`, pages, forms, lists, query schemes, unit privileges, import metadata, or menu rows by default.

For non-entity units, use `{Base}=Base` when rendering Java templates and do not render `Model.template`; non-entity units do not have a model class by default.

Relational database entity unit fields:

```text
FName,FCode,FIcon,FModuleId,FOpenMode,FIsSlaveUnit,FMasterUnitId,FIsTreeStructure,FIsTreeCheckPrivilege,FTreeDefaultExpandLevel,FSupportWorkflow,FSupportUser,FSupportDepartment,FSupportEditType,FSupportAttachment,FSupportDataPrivilege,FSupportBusinessLog,FSupportNote,FSupportSort,FRecordCreateInfo,FRecordUpdateInfo,FApiEnabled,FDataSource,FTable,FKeyField,FKeyType,FNameField,FMasterField,FHomeClassName,FDaoClassName,FServiceClassName,FActionClassName,FApiClassName,FUnitFilterSql,FBusinessFilterSql,FDescription,FViewPageConditionForList,FViewPageConditionForLink,FSupportVersion,FWebServiceUniqueField,FSupportAvatar,FSupportAlbum
```

ElasticSearch entity unit fields:

```text
FName,FCode,FIcon,FModuleId,FOpenMode,FIsSlaveUnit,FMasterUnitId,FSupportWorkflow,FSupportUser,FSupportDepartment,FSupportEditType,FSupportAttachment,FSupportDataPrivilege,FSupportBusinessLog,FSupportNote,FRecordCreateInfo,FRecordUpdateInfo,FApiEnabled,FEsDataSource,FEsIndex,FEsType,FKeyField,FNameField,FMasterField,FHomeClassName,FEsDaoClassName,FServiceClassName,FActionClassName,FApiClassName,FDescription,FSupportVersion,FSupportAvatar,FSupportAlbum
```

Non-entity unit fields:

```text
FName,FCode,FModuleId,FIcon,FApiEnabled,FHomeClassName,FDaoClassName,FServiceClassName,FActionClassName,FApiClassName,FDescription
```

For non-entity units, the base metadata hides these `Qs.Unit` slave pages:

```text
Qs.Unit.FieldList,Qs.Unit.RelationList,Qs.Unit.EditList,Qs.Unit.FormList,Qs.Unit.ListList,Qs.Unit.ViewItemList,Qs.Unit.OperationList,Qs.Unit.EntityEventList,Qs.Unit.PageList,Qs.Unit.PrivilegeList,Qs.Unit.SlavePagePrivilege,Qs.Unit.SerialNumberList,Qs.Unit.ImportConfig,Qs.Unit.WorkflowList,Qs.Unit.DuplicationList,Qs.Unit.ListFilterList,Qs.Unit.ListColorList,Qs.Unit.SlaveUnitPrivilege
```

## TsUnit Fields

Identity and display:

- `FId`: unit ID referenced by almost every related metadata row.
- `FCode`: unique unit code, such as `Qs.Unit`, `Ecp.Customer`, or `Mes.WorkOrder`. Use the target product/project prefix; `Qs.*` is the QS base-product prefix. When the prefix is not given, infer it from the project name first, then check existing `.sql` files under the target module project's `src/main/resources/QS-MODULE/data/sql/default` directory, including nested subdirectories usually up to three levels deep, to match the user's established prefix and casing style.
- `FName`: unit display name.
- `FIcon` and `FBigIcon`: 16x16 and 64x64 icon paths.
- `FEditId`: interface/edit type ID.
- `FModuleId`: owning module ID.
- `FOpenMode`: opening behavior, such as `System`.
- `FDescription`: description text.

Tree and master-detail behavior:

- `FIsTreeStructure`: whether the unit is tree-structured.
- `FIsTreeCheckPrivilege`: whether tree display checks privilege.
- `FMaxTreeLevel`: maximum tree level.
- `FTreeDefaultExpandLevel`: default tree expand level, commonly `2`.
- `FIsSlaveUnit`: whether this is a slave unit.
- `FMasterUnitId`: master unit ID.
- `FMasterField`: field linking to the master unit.

Feature switches:

- `FSupportWorkflow`: workflow support.
- `FSupportUser`: user support.
- `FSupportDepartment`: department support.
- `FSupportEditType`: edit/entity type support.
- `FSupportAttachment`: attachment support.
- `FSupportDataPrivilege`: data privilege support.
- `FSupportVersion`: history/version support.
- `FSupportBusinessLog`: business log support.
- `FSupportNote`: note support.
- `FSupportSort`: sorting support.
- `FSupportAvatar`: avatar support.
- `FSupportAlbum`: album support.
- `FSupportPrivilegeField`: custom privilege-field support.
- `FIsFullTextSearch`: full-text search support.
- `FSearchAttachment`: whether attachments are included in search.
- `FSupportEqualQuery`: exact query support.
- `FUseSystemI18nTable`: whether system i18n tables are used.
- `FExtraQueryResultLimit`: extra query result limit.
- `FRecordCreateInfo`, `FRecordUpdateInfo`, `FRecordDeleteInfo`: create/update/delete audit information flags.
- `FApiEnabled`: whether API access is enabled.

Data binding:

- `FDataSource`: data source name, usually `default`.
- `FTable`: business table.
- `FKeyField`: primary key field.
- `FKeyType`: key type, such as `Uuid`.
- `FNameField`: default display/name field.
- `FWebServiceUniqueField`: unique field for web service integration.

Java class binding:

- `FHomeClassName`: home class name.
- `FDaoClassName`: DAO implementation class name.
- `FServiceClassName`: service implementation class name.
- `FActionClassName`: action implementation class name.
- `FApiClassName`: API implementation class name.

When `{Package}` and `{UnitCode}` are known, infer the standard class bindings this way unless nearby units use a different convention:

```text
FHomeClassName    = {Package}.{UnitCode}Home
FDaoClassName     = {Package}.dao.impl.{UnitCode}DaoImpl
FServiceClassName = {Package}.service.impl.{UnitCode}ServiceImpl
FActionClassName  = {Package}.action.impl.{UnitCode}ActionImpl
FApiClassName     = {Package}.api.impl.{UnitCode}ApiImpl
```

Only populate these `TsUnit` class binding fields automatically when Java generation is requested or the user explicitly provides class names. If the user chooses SQL-only unit creation, leave class binding fields unset.

For Java template rendering, derive `{CacheRegion}` from `TsUnit.FCode`: lowercase the unit code and replace `.` and other non-alphanumeric characters with `_`. For example, `Qs.Account` becomes `qs_account`.

Derive `{UnitCode}` from the last segment of `TsUnit.FCode` in PascalCase when it is not given explicitly. For example, with `{Package}=com.jeedsoft.quicksilver.account` and `FCode='Qs.Account'`, use `Account` and generate:

```text
FHomeClassName='com.jeedsoft.quicksilver.account.AccountHome'
FDaoClassName='com.jeedsoft.quicksilver.account.dao.impl.AccountDaoImpl'
FServiceClassName='com.jeedsoft.quicksilver.account.service.impl.AccountServiceImpl'
FActionClassName='com.jeedsoft.quicksilver.account.action.impl.AccountActionImpl'
FApiClassName='com.jeedsoft.quicksilver.account.api.impl.AccountApiImpl'
```

Filtering, view conditions, ES, and tenant behavior:

- `FViewPageConditionForList`: condition used when opening through a list.
- `FViewPageConditionForLink`: condition used when opening through a link.
- `FUnitFilterSql`: unit-level filter SQL.
- `FBusinessFilterSql`: business-level filter SQL.
- `FEsDataSource`: ES data source.
- `FEsIndex`: ES index.
- `FEsType`: ES type, commonly `data`.
- `FEsDaoClassName`: ES DAO class name.
- `FTenantMode`: tenant mode.

## Qs.Unit Field Examples

The `Qs.Unit` metadata defines `TsField` rows for many `TsUnit` columns. Use those rows as examples when deciding field controls:

- Java class fields such as `FHomeClassName`, `FDaoClassName`, `FServiceClassName`, `FActionClassName`, `FApiClassName`, and `FEsDaoClassName` use `InputBox-Text` with size around `100`.
- Boolean feature switches such as `FApiEnabled`, `FIsTreeStructure`, `FSupportAttachment`, and `FRecordCreateInfo` use `CheckBox`.
- Long SQL/text fields such as `FBusinessFilterSql`, `FUnitFilterSql`, and `FDescription` use `TextBox` and larger row spans.
- Entity references such as `FEditId`, `FMasterUnitId`, and `FModuleId` use `EntityBox` and set `FEntityUnitId`.
- Dictionary-backed choices such as `FDataSource`, `FEsDataSource`, `FKeyType`, and `FOpenMode` use `ComboBox-SelectOnly` and set `FDictionaryId`.
- Required identity/binding fields include examples such as `FCode`, `FName`, `FDataSource`, `FEditId`, `FModuleId`, `FTable`, `FKeyField`, `FKeyType`, and `FNameField`.

## Rules

- Generate a fresh `TsUnit.FId` for each new unit unless an explicit ID is provided.
- Every related row that has `FUnitId`, `FEntityUnitId`, or `FMasterUnitId` must point to the correct unit ID.
- For modifying or deleting an existing `TsUnit` row, generate SQL with `where FId='<unit-id>'`; do not identify the row only by `FCode` or `FName`.
- When deleting an entire entity unit, related metadata rows that have `FUnitId` can be deleted with `where FUnitId='<unit-id>'`; delete dependent child rows such as `TsToolSubItem` and `TsToolItem` before deleting `TsPage`. For non-entity units, delete only the `TsUnit` row by default.
- Do not enable feature switches casually. Match a nearby unit or user requirements.
- If `FKeyField`, `FKeyType`, and `FNameField` are not specified for a new relational entity unit, use `FId`, `Uuid`, and `FName`; generate both the business table columns and matching `TsField` rows.
- For a new non-entity unit, generate only `TsUnit` by default; keep business table and field metadata empty/absent unless there is an explicit requirement.
- For non-entity Java generation, use base classes such as `BaseHome`/`BaseDao` patterns from the templates via `{Base}=Base`, and skip the model class unless the target project has a custom non-entity model convention.
- If class-name fields are blank, the runtime may use defaults; if the target project sets them explicitly, render the full implementation class names.
- If `FTable`, `FKeyField`, `FKeyType`, or `FNameField` changes, update related Java model/DAO behavior and field metadata.
