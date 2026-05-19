# Unit Form, List, And Query Metadata

Use this reference when creating or changing `TsForm`, `TsList`, `TsQuerySchema`, or their helper calls.

## TsForm

`TsForm` defines form layouts for a unit.

`Qs.Form` is registered as a slave unit of `Qs.Unit`: `FIsSlaveUnit=1`, `FMasterUnitId` points to `Qs.Unit`, `FTable='TsForm'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FName'`, and `FMasterField='FUnitId'`.

## TsForm Fields

Identity and ordering:

- `FId`: form ID used by `setFormFields`.
- `FName`: form name.
- `FIndex`: ordering.
- `FUnitId`: owning unit ID.
- `FPageId`: optional page binding.
- `FPlatform`: platform, such as `Computer`.

Behavior:

- `FDefault`: whether this is the default form.
- `FGroupMode`: grouping/layout mode, such as `Double`.
- `FEditableCondition`: condition controlling form editability.

## Qs.Form Field Examples

Use `Qs.Form` examples when selecting form metadata controls:

- Required core fields include `FUnitId`, `FName`, `FPlatform`, and `FGroupMode`.
- `FUnitId` and `FPageId` use `EntityBox`.
- `FPlatform` and `FGroupMode` use `ComboBox-SelectOnly` with dictionaries.
- `FDefault` uses `CheckBox`.
- `FIndex` uses `InputBox-Integer`.
- `FEditableCondition` uses `InputBox-Text`.
- Common defaults include `FPlatform='Computer'`.

Use `setFormFields` to place fields into form groups and sections. Keep field order and grouping aligned with `TsField` definitions.

## TsList

`TsList` defines list layouts for a unit.

`Qs.List` is registered as a slave unit of `Qs.Unit`: `FIsSlaveUnit=1`, `FMasterUnitId` points to `Qs.Unit`, `FTable='TsList'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FName'`, and `FMasterField='FUnitId'`.

## TsList Fields

Identity and ordering:

- `FId`: list ID used by `setListFields`.
- `FUnitId`: owning unit ID.
- `FName`: list name.
- `FPageId`: optional page-specific list binding.
- `FIndex`: ordering.
- `FPlatform`: platform.

Behavior:

- `FDefault`: default list flag.
- `FMultiPage`: whether pagination is enabled.

## Qs.List Field Examples

Use `Qs.List` examples when selecting list metadata controls:

- Required core fields include `FName` and `FPlatform`.
- `FUnitId` and `FPageId` use `EntityBox`.
- `FPlatform` uses `ComboBox-SelectOnly` with a platform dictionary.
- `FDefault` and `FMultiPage` use `CheckBox`.
- `FIndex` uses `InputBox-Integer`.
- Common defaults include `FPlatform='Computer'` and `FMultiPage=1`.

Use `setListFields` to define visible list columns.

For a newly created entity unit, generate three default `TsList` rows when following the standard template: main list, selection list, and homepage list. Call `setListFields` for all three lists in the same field order.

## TsQuerySchema

`TsQuerySchema` defines default query schemes.

`Qs.QuerySchema` is registered as a unit whose business table is `TsQuerySchema`: `FTable='TsQuerySchema'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FName'`, and `FApiEnabled=1`.

Common types in the bundled template:

- `condition`: normal condition schema, such as "all".
- `collection`: favorite/collection schema.

## TsQuerySchema Fields

Identity and ordering:

- `FId`: query schema ID.
- `FUnitId`: owning unit ID.
- `FName`: schema name.
- `FIndex`: ordering.

Type and sharing:

- `FType`: schema type.
- `FPublic`, `FVisible`, `FTemp`, `FGlobalAutoQuery`, `FShare`: behavior flags.
- `FUserId`: user owner.

Condition and SQL:

- `FConditionId`: condition ID.
- `FSqlSource`: SQL source mode.
- `FSql`: SQL text or Java class.
- `FUpdateTime`: update timestamp.
- `FOriginSchemaId`: original schema ID.
- `FParentId`: parent query schema.

## Qs.QuerySchema Field Examples

Use `Qs.QuerySchema` examples when selecting query schema metadata controls:

- Required core fields include `FName` and `FType`.
- `FUnitId`, `FUserId`, and `FParentId` use `EntityBox`.
- `FType` and `FSqlSource` use `ComboBox-SelectOnly` with dictionaries.
- `FPublic`, `FVisible`, `FTemp`, `FGlobalAutoQuery`, and `FShare` use `CheckBox`.
- `FConditionId` and `FOriginSchemaId` use `InputBox-Uuid`.
- `FIndex` uses `InputBox-Integer`.
- `FSql` uses `TextBox` with a large size.
- `FUpdateTime` uses `DateBox-DateTime`.
- Common defaults include `FType='condition'`, `FSqlSource='None'`, `FPublic=0`, and `FVisible=1`.

## Related Helpers

- `setQueryFormFields`: query form field list.
- `setKeywordFields`: keyword search fields.
- `setFormFields`: form field layout.
- `setListFields`: list columns.
- `setImportTemplateFields`: import template fields.

## Rules

- Any field shown in forms or lists must have a matching `TsField` row.
- For modifying or deleting existing `TsForm`, `TsList`, or `TsQuerySchema` rows, generate SQL with `where FId='<id>'`; do not identify the row only by name, unit ID, page ID, or type.
- If a field is searchable, update both `TsField.FQueryable` and the relevant query helper call.
- If a list is bound to a specific page, keep `TsList.FPageId` aligned with that page ID.
- Do not add fields to import templates unless the unit supports importing or a nearby unit does the same.
