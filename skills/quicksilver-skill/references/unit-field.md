# Unit Field Metadata

Use this reference when creating or changing `TsField` rows or field-related helper calls.

## Table

`TsField` defines fields for a unit. It controls both data binding and UI behavior.

`Qs.Unit` and `Qs.Field` are useful reference units. `Qs.Unit` shows fields for the `TsUnit` table. `Qs.Field` shows fields for the `TsField` table itself and is the best local reference for field-control metadata.

## TsField Fields

Identity and basic behavior:

- `FId`: field ID.
- `FUnitId`: owning unit ID.
- `FName`: field name, usually matching the business table column.
- `FTitle`: field display title.
- `FType`: field control type, such as `InputBox-Key` or `InputBox-Text`.
- `FSize`: size or max length when applicable.
- `FVisible`: whether the field is visible.
- `FFilterByRole`: whether role filtering applies.
- `FRequired`: whether input is required.
- `FReadOnly`: whether the field is read-only.
- `FQueryable`: whether the field can be used in queries.

Dictionary, entity, relation, and source binding:

- `FDictionaryId`: dictionary ID for dictionary-backed controls, especially `ComboBox-SelectOnly`.
- `FParentField`: parent dictionary field.
- `FEntityUnitId`: related entity unit ID for key/entity fields.
- `FRelationTable`: relation table name.
- `FRelationCapacity`: maximum relation count.
- `FRelationId`: relation metadata ID.
- `FSelectListConstantFilterSql`: fixed filter SQL for selection lists.
- `FSelectListVariableFilterSql`: variable filter SQL for selection lists.
- `FSourceType`: value source, such as `local`.
- `FJoinField`: join field used when sourcing data.
- `FSourceField`: source field.
- `FSource`: SQL or template source text.

Localization and text behavior:

- `FSupportLocalText`: whether local entity text is supported.
- `FSupportI18n`: whether i18n text is supported.
- `FLocalTextField`: field used for local text.
- `FLocalTextFirst`: whether local text is preferred.
- `FLocalTextFirstCondition`: condition for preferring local text.

Form layout and control sizing:

- `FColSpan` and `FRowSpan`: form layout span controls.
- `FIsNewRow`: whether the field starts a new row.
- `FTitleWidth`: title width mode.
- `FControlWidth`: control width mode.
- `FControlWidthValue`: explicit control width in pixels.

List and display formatting:

- `FListWidth` and `FListAlign`: list column display controls.
- `FScale`: decimal scale.
- `FLabelColor`: label color.
- `FMobileListFormat`: mobile list format.
- `FSuffix`: display suffix.

Default values, hints, validation, and client behavior:

- `FDefaultValueType`: default value type, such as server value.
- `FDefaultValue`: default value.
- `FHint`: hint/help text.
- `FAlwaysBringDataToClient`: whether the field is always sent to the client.
- `FValidation`: validation rule, usually a regular expression.
- `FFollowingField`: following field.
- `FCustomData`: custom metadata.

Web service and integration fields:

- `FWebServiceListQueryField`: field used for list query integration.
- `FWebServiceItemQueryField`: field used for item query integration.
- `FWebServiceCreateField`: field used for create/update integration.

Masking and encryption:

- `FMaskEnabled`: whether masking is enabled.
- `FLeftNumberToShow`: visible characters on the left when masking.
- `FRightNumberToShow`: visible characters on the right when masking.
- `FRightLessNumberToShow`: fewer visible right-side characters when masking.
- `FEncrypted`: whether the field is encrypted.

`TsField` has a unique constraint on `(FName, FUnitId)`. Do not create duplicate field names inside the same unit.

## Qs.Field Field Examples

`Qs.Field` is registered as a slave unit of `Qs.Unit`: `FIsSlaveUnit=1`, `FMasterUnitId` points to `Qs.Unit`, `FTable='TsField'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FTitle'`, and `FMasterField='FUnitId'`.

Use `Qs.Field` examples when selecting control types:

- Boolean flags such as `FVisible`, `FRequired`, `FReadOnly`, `FQueryable`, `FIsNewRow`, `FSupportI18n`, `FMaskEnabled`, and `FEncrypted` use `CheckBox`.
- Numeric fields such as `FSize`, `FColSpan`, `FRowSpan`, `FListWidth`, `FScale`, `FControlWidthValue`, and mask character counts use `InputBox-Integer`.
- Dictionary-backed choice fields such as `FType`, `FSourceType`, `FListAlign`, `FTitleWidth`, `FControlWidth`, and `FDefaultValueType` use `ComboBox-SelectOnly` with `FDictionaryId`.
- Entity references such as `FUnitId`, `FDictionaryId`, `FEntityUnitId`, and `FRelationId` use `EntityBox` and set `FEntityUnitId`.
- Large text fields such as `FSource`, `FCustomData`, `FHint`, `FSelectListConstantFilterSql`, and `FSelectListVariableFilterSql` use `TextBox` with larger `FRowSpan`.
- Required core fields include `FUnitId`, `FName`, `FTitle`, `FType`, `FSourceType`, `FColSpan`, `FRowSpan`, and `FListWidth` in the `Qs.Field` metadata.

## Field Type Mapping

`TsField.FType` values must come from the `QS-欄位-類型` dictionary in base metadata:

```text
TsDictionary.FId='4d2eec6d-5f41-4c38-9ad1-c04ded9e3110'
TsDictionary.FName='QS-欄位-類型'
```

Allowed standard values include:

```text
InputBox-Text
TextBox
InputBox-Integer
InputBox-BigInt
InputBox-Double
InputBox-Decimal
InputBox-Percent
InputBox-Email
InputBox-Phone
InputBox-Address
InputBox-Url
InputBox-Password
CheckBox
MultiCheckBox
RadioBox
ComboBox-Inputable
ComboBox-SelectOnly
DateBox-Date
DateBox-DateTime
DateBox-MonthDay
EntityBox
MultiEntityBox
PictureBox
HtmlBox
Grid
List
InputBox-Key
InputBox-Uuid
Label
Button
```

When choosing a field type, prefer these dictionary values and verify against the target project's `init.sql` or existing dictionary rows if the project customizes field types.

The Quicksilver runtime maps `TsField.FType` to SQL types, ES field types, Cast types, and generated SQL type names. Use this mapping when generating business tables and field metadata.

The source of truth is `com.jeedsoft.quicksilver.unit.misc.FieldType`. It also declares `List`, `Button`, and `Label`, but those constants are not registered in the SQL, ES, Cast, or SQL type-name maps in the base runtime, so do not use them as ordinary business table column types unless the target project adds custom handling.

Common SQL type mappings:

- Text-like controls: `InputBox-Text`, `InputBox-Password`, `InputBox-Email`, `InputBox-Phone`, `InputBox-Address`, `InputBox-Url`, `TextBox`, `HtmlBox`, `RadioBox`, `MultiCheckBox`, `MultiCheckComboBox`, `ComboBox-Inputable`, `ComboBox-SelectOnly`, `DateBox-MonthDay`, and `Grid` map to `varchar`.
- Integer controls: `InputBox-Integer` maps to `int`.
- Big integer controls: `InputBox-BigInt` maps to `bigint`.
- Decimal/number controls: `InputBox-Double` and `InputBox-Percent` map to `double`; `InputBox-Decimal` maps to `decimal`.
- Boolean controls: `CheckBox` maps to `bit`.
- Date controls: `DateBox-Date` maps to `date`; `DateBox-DateTime` maps to `timestamp`.
- ID/entity controls: `InputBox-Key`, `InputBox-Uuid`, `EntityBox`, and `PictureBox` map to `uuid`.
- Multi-entity controls: `MultiEntityBox` maps to `varchar` sized by relation capacity.

Common ES mappings:

- Text-search fields such as `InputBox-Text`, `InputBox-Address`, `InputBox-Url`, `TextBox`, `HtmlBox`, and `Grid` map to ES `text`.
- Exact-match fields such as password, UUID/key, email, phone, radio, checkbox-multi, combo, entity, multi-entity, picture, and month-day controls map to ES `keyword`.
- Number fields map to ES integer, long, or double according to the field type.
- `CheckBox` maps to ES boolean.
- `DateBox-Date` and `DateBox-DateTime` map to ES date.

Common Cast mappings:

- Text-like, radio, multi-check, combo, month-day, multi-entity, and grid controls map to `Cast.STRING`.
- `InputBox-Integer` maps to `Cast.INTEGER`; `InputBox-BigInt` maps to `Cast.LONG`.
- `InputBox-Double` and `InputBox-Percent` map to `Cast.DOUBLE`; `InputBox-Decimal` maps to `Cast.DECIMAL`.
- `CheckBox` maps to `Cast.BOOLEAN`.
- `DateBox-Date` and `DateBox-DateTime` map to `Cast.DATE`.
- `InputBox-Key`, `InputBox-Uuid`, `EntityBox`, and `PictureBox` map to `Cast.UUID`.

Generated SQL type-name rules:

- `varchar` types must include the field's actual size.
- `double` fields for `InputBox-Double` and `InputBox-Percent` use SQL column type `double`; set `TsField.FScale` when the UI should display or edit a fixed number of decimal places, commonly `FScale=2`.
- `decimal` fields for `InputBox-Decimal` use SQL column type `decimal(FSize, FScale)`; set `TsField.FSize` to the total precision and `TsField.FScale` to the decimal places, for example `FSize=25`, `FScale=2` maps to `decimal(25, 2)`.
- `MultiEntityBox` uses `varchar(FRelationCapacity * 37 - 1)`.

Floating/decimal examples from `assets/templates/unit/sql/unit.sql`:

```sql
FDouble double,
FDecimal decimal(25, 2),
FPercent double
```

```sql
insert into TsField set FName='FDouble',  FType='InputBox-Double',  FScale=2, ...;
insert into TsField set FName='FDecimal', FType='InputBox-Decimal', FSize=25, FScale=2, ...;
insert into TsField set FName='FPercent', FType='InputBox-Percent', FScale=2, ...;
```

Runtime grouping:

- Char-like fields include text, password, email, phone, address, URL, text box, HTML box, radio, multi-check, combo, and grid controls.
- Number fields include integer, bigint, double, percent, and decimal controls.
- Quoted SQL literal fields include text-like controls plus key/UUID/date/entity/picture/grid controls.

## Related Helpers

Field metadata must stay consistent with helper calls:

- `setQueryFormFields(<unit-id>, ...)`: fields shown in the query form.
- `setKeywordFields(<unit-id>, ...)`: fields used for keyword search.
- `setFormFields(<form-id>, ...)`: fields placed on a form.
- `setListFields(<list-id>, ...)`: fields placed in a list.
- `setImportTemplateFields(<unit-id>, ...)`: fields used in import templates.

## Rules

- Adding a business column usually requires a `TsField` row plus updates to form/list/query/import helper calls when the field should appear there.
- For modifying or deleting an existing `TsField` row, generate SQL with `where FId='<field-id>'`; do not identify the row only by `FName`, `FTitle`, or `FUnitId`.
- Required fields should have both `FRequired=1` and compatible Java/server validation when the target project has validation conventions.
- Hidden key fields typically use `FVisible=0` and a key-style control type.
- Layout fields such as `FColSpan` and `FRowSpan` affect only placement; do not use them to model business logic.
- Queryable fields need `FQueryable=1` and may also need `setQueryFormFields` or `setKeywordFields`.
- Match nearby units for control types before inventing new `FType` values.
