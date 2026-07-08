# Unit Page And Tool Metadata

Use this reference when creating or changing `TsPage`, `TsToolItem`, or `TsToolSubItem` rows.

## TsPage

`TsPage` defines pages for the unit.

Common page types in the bundled template:

- Main list page, such as code suffix `.List`.
- Selection list page, such as code suffix `.SelectList`.
- Form page, such as code suffix `.Form`.

`Qs.Page` is registered as a unit whose business table is `TsPage`. Its `TsField` rows are useful examples for page metadata control types, defaults, required fields, query behavior, and dialog sizing.

## TsPage Fields

Identity and display:

- `FId`: page ID referenced by tools, lists, menus, and forms.
- `FName`: page name.
- `FTitle`: page title.
- `FCode`: unique page code.
- `FEditId`: interface/edit type ID.
- `FPlatform`: platform, such as `Computer`.
- `FType`: page type, such as `EntityList` or `EntityForm`.
- `FIcon`: page icon.
- `FUrl`: JSP/template URL.
- `FDescription`: page description.
- `FGroupId`: page group ID.

Action, load, and relation binding:

- `FActionMethodName`: action method such as `Qs.TestCreateUnit.prepareList`.
- `FLoadHandler`: page load handler.
- `FRelationId`: relation metadata ID.
- `FUnitId`: owning unit ID.
- `FMasterUnitId`: master unit for slave/form pages.
- `FIsSlavePage`: whether the page is a slave page.
- `FIndex`: ordering.

Form and dialog behavior:

- `FFormColumnCount`: form column count.
- `FDialogWidth`: dialog width.
- `FDialogHeight`: dialog height.
- `FDialogMaximized`: whether the dialog opens maximized.

Query and view behavior:

- `FQueryFormAutoQuery`: whether query form auto-runs.
- `FHasViewFrame`: whether the view frame is shown.
- `FQueryOnLoad`: query-on-load mode.
- `FQuerySchemaId`: default query schema ID.
- `FCreateQuerySchemaBox`: whether to create/show the query schema box.
- `FCreateKeywordBox`: whether to create/show the keyword box.
- `FToolItemInitArguments`: toolbar initialization arguments.

Visibility:

- `FVisible`: whether the page is visible.
- `FVisibleCondition`: page visibility condition.

## Icon Paths

Quicksilver projects may use multi-theme or single-theme icon paths. Multi-theme icons include `${theme}` in the path and commonly use SVG, for example `quicksilver/image/unit/${theme}/New.svg`. Single-theme icons omit `${theme}` and may use GIF, for example `quicksilver/image/unit/New.gif`.

Use the target QS version to choose the default icon style when nearby SQL does not make it obvious. For existing or inherited QS projects, prefer reading the version from Gradle's `com.jeedsoft:quicksilver-gradle-plugin:<version>` dependency. If using a custom Gradle task inside the project, `$qsVersion` can also provide the resolved QS version.

- `6.x`: single-theme.
- `7.2.x`: single-theme.
- `7.3.x`: single-theme.
- `7.1.32.05` and lower: single-theme.
- Higher than `7.1.32.05`, such as `7.1.32.14`: multi-theme.

Common multi-theme to single-theme examples:

| Multi-theme | Single-theme |
| --- | --- |
| `quicksilver/image/unit/${theme}/New.svg` | `quicksilver/image/unit/New.gif` |
| `quicksilver/image/unit/${theme}/Form.svg` | `quicksilver/image/unit/Form.png` |
| `quicksilver/image/16/${theme}/Add.svg` | `quicksilver/image/16/Add.png` |

When generating `FIcon` or `FBigIcon`, inspect nearby SQL in the target module and follow the project's existing icon style. Do not convert a single-theme project to `${theme}` SVG paths, and do not remove `${theme}` from a multi-theme project.

## Qs.Page Field Examples

Use `Qs.Page` examples when selecting page metadata controls:

- Required identity fields include `FCode`, `FEditId`, `FName`, `FPlatform`, `FTitle`, `FType`, `FIcon`, and `FUrl`.
- Page type and platform fields such as `FType`, `FPlatform`, `FQueryOnLoad`, `FCreateQuerySchemaBox`, and `FCreateKeywordBox` use `ComboBox-SelectOnly` with dictionaries.
- References such as `FEditId`, `FGroupId`, `FMasterUnitId`, `FQuerySchemaId`, `FRelationId`, and `FUnitId` use `EntityBox`.
- Boolean behavior fields such as `FDialogMaximized`, `FHasViewFrame`, `FIsSlavePage`, `FQueryFormAutoQuery`, and `FVisible` use `CheckBox`.
- Numeric layout fields such as `FDialogWidth`, `FDialogHeight`, `FFormColumnCount`, and `FIndex` use `InputBox-Integer`.
- Long text fields such as `FDescription` and `FToolItemInitArguments` use `TextBox` with larger row spans.
- Common defaults include `FPlatform='Computer'`, `FQueryFormAutoQuery=true`, and `FVisible=true`.

## TsToolItem

`TsToolItem` defines top-level toolbar items for a page.

Common items include `Add`, `Open`, `Delete`, `Refresh`, `Other`, `ConfirmSelection`, and `Save`.

For a newly created entity unit's main list page, generate the `Other` toolbar item as a dropdown/combo button by default, following the bundled `unit.sql` pattern. Its default `TsToolSubItem` children are `Import`, `ExcelExport`, and `BillPrint`.

For a newly created entity unit's selection list page, generate `ConfirmSelection`, `Add`, and `Open` toolbar buttons by default.

For a newly created entity unit's form page, generate `Save` and an `Other` dropdown/combo button by default. The form page `Other` button's default child is `BillPrint`.

`Qs.ToolItem` is registered as a slave unit of `Qs.Page`: `FIsSlaveUnit=1`, `FMasterUnitId` points to `Qs.Page`, `FTable='TsToolItem'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FCode'`, and `FMasterField='FPageId'`.

## TsToolItem Fields

Identity and display:

- `FPageId`: page that owns the toolbar item.
- `FCode`: command code.
- `FName` and `FHint`: display text.
- `FLabel`: label text.
- `FType`: button type, such as `Button` or `ComboButton`.
- `FAlign`, `FIndex`, `FWidth`, and `FIcon`: placement and appearance.
- `FScale`: decimal scale for value-oriented controls.
- `FSuffix`: display suffix.

Value, entity, dictionary, and submenu behavior:

- `FEntityUnitId`: related entity unit.
- `FDefaultValue`: default value.
- `FSubItemSource`: submenu content source.
- `FDictionaryId`: dictionary ID for dictionary-backed controls.
- `FSubItemRoutine`: Java class or SQL/routine used for submenu content.

Visibility, enablement, and handling:

- `FVisibleCondition`: condition controlling visibility.
- `FEnableCondition`: condition controlling enablement.
- `FHandleType`: handling mode, such as JavaScript, page, chart, or none depending on dictionaries.
- `FHandlePageId`: page used by page-handling modes.
- `FChartId`: chart used by chart-handling modes.
- `FConfirmMessage`: confirmation message shown before execution.
- `FDefaultEventHandler`: default JavaScript function or statement.

`TsToolItem` has a unique constraint on `(FCode, FPageId)`. Do not create duplicate tool item codes on the same page.

## Qs.ToolItem Field Examples

Use `Qs.ToolItem` examples when selecting toolbar metadata controls:

- Required core fields include `FAlign`, `FCode`, `FHandleType`, and `FType`.
- `FType`, `FAlign`, `FHandleType`, and `FSubItemSource` use `ComboBox-SelectOnly` with dictionaries.
- References such as `FPageId`, `FEntityUnitId`, `FDictionaryId`, `FHandlePageId`, and `FChartId` use `EntityBox`.
- Numeric fields such as `FIndex`, `FWidth`, and `FScale` use `InputBox-Integer`.
- Large handler/routine fields such as `FDefaultEventHandler` and `FSubItemRoutine` use `TextBox` with larger row spans.
- User-facing text such as `FName`, `FHint`, `FLabel`, and `FConfirmMessage` may support i18n in nearby metadata.
- Common defaults include `FType='Button'`, `FHandleType='None'`, and `FAlign` from the toolbar alignment dictionary.

## TsToolSubItem

`TsToolSubItem` defines submenu entries under combo toolbar items.

Common items include `Import`, `ExcelExport`, and `BillPrint`.

Use `TsToolSubItem` when a top-level `TsToolItem` has dropdown or combo-button children. Keep the parent `TsToolItem.FSubItemSource` compatible with table-backed subitems.

`Qs.ToolSubItem` is registered as a slave unit of `Qs.ToolItem`: `FIsSlaveUnit=1`, `FMasterUnitId` points to `Qs.ToolItem`, `FTable='TsToolSubItem'`, `FKeyField='FId'`, `FKeyType='Uuid'`, `FNameField='FName'`, and `FMasterField='FToolItemId'`.

## TsToolSubItem Fields

Identity and display:

- `FId`: subitem ID.
- `FToolItemId`: parent toolbar item ID.
- `FCode`: subitem command code.
- `FName`: display name.
- `FExpandMode`: expand mode, such as `None`.
- `FIndex`: ordering under the parent item.
- `FIcon`: icon path.

Visibility, enablement, and handling:

- `FVisibleCondition`: condition controlling visibility.
- `FEnableCondition`: condition controlling enablement.
- `FHandleType`: handling mode, such as JavaScript, page, chart, or none depending on dictionaries.
- `FHandlePageId`: page used by page-handling modes.
- `FChartId`: chart used by chart-handling modes.
- `FConfirmMessage`: confirmation message shown before execution.
- `FEventHandler`: JavaScript function or statement executed by the subitem.

`TsToolSubItem` has a unique constraint on `(FCode, FToolItemId)`. Do not create duplicate subitem codes under the same toolbar item.

## Qs.ToolSubItem Field Examples

Use `Qs.ToolSubItem` examples when selecting submenu metadata controls:

- Required core fields include `FToolItemId`, `FCode`, `FName`, `FExpandMode`, and `FHandleType`.
- `FExpandMode` and `FHandleType` use `ComboBox-SelectOnly` with dictionaries.
- References such as `FToolItemId`, `FHandlePageId`, and `FChartId` use `EntityBox`.
- Numeric ordering uses `FIndex` with `InputBox-Integer`.
- Handler text uses `FEventHandler` with `TextBox` and a large row span.
- User-facing text such as `FName` and `FConfirmMessage` may support i18n in nearby metadata.
- Common defaults include `FExpandMode='None'` and `FHandleType='JavaScript'`.

## Rules

- When creating a page, generate fresh page IDs and update every dependent row.
- For modifying or deleting existing `TsPage`, `TsToolItem`, or `TsToolSubItem` rows, generate SQL with `where FId='<id>'`; do not identify the row only by code, name, title, page ID, or parent tool item ID.
- Toolbar entries must point to the correct page or parent tool item.
- Match event handlers to page type. List tools usually use `EntityList.*`; form tools usually use `EntityForm.*`.
- Preserve menu and list references when page IDs change.
