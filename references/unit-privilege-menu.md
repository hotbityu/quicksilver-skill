# Unit Privilege And Menu Metadata

Use this reference when creating or changing `TsPrivilege`, `TsPrivilegeType`, or `TsMenu` rows.

## TsPrivilege

`TsPrivilege` defines privileges for the unit.

Common privilege rows in the bundled template:

- Add
- View
- Modify
- Delete

`Qs.Privilege` is registered as a unit whose business table is `TsPrivilege`: `FTable='TsPrivilege'`, `FKeyField='FId'`, `FKeyType='Uuid'`, and `FNameField='FName'`.

## TsPrivilege Fields

Identity and ordering:

- `FId`: privilege ID.
- `FName`: privilege display name.
- `FIndex`: ordering.

Scope and type:

- `FUnitId`: owning unit ID.
- `FModuleId`: owning module ID.
- `FPrivilegeTypeId`: privilege type, such as add/view/modify/delete.

Reuse and source behavior:

- `FUseExisting`: whether an existing privilege is reused.
- `FSourcePrivilegeId`: source privilege when reusing or deriving permissions.
- `FEditId`: edit/configuration ID.
- `FIsSystemLevel`: system-level flag.

## Qs.Privilege Field Examples

Use `Qs.Privilege` examples when selecting privilege metadata controls:

- Required core fields include `FName`, `FUnitId`, and `FModuleId`.
- References such as `FUnitId`, `FModuleId`, `FPrivilegeTypeId`, `FSourcePrivilegeId`, and `FEditId` use `EntityBox`.
- `FUseExisting` and `FIsSystemLevel` use `CheckBox` with default `0`.
- `FIndex` uses `InputBox-Integer`.
- `FName` uses `InputBox-Text` and may support i18n.
- Match nearby units to choose the correct `FPrivilegeTypeId` values for add, view, modify, delete, and any custom privilege types.

## TsPrivilegeType

`TsPrivilegeType` defines reusable privilege types referenced by `TsPrivilege.FPrivilegeTypeId`.

`Qs.PrivilegeType` is registered as a unit whose business table is `TsPrivilegeType`: `FTable='TsPrivilegeType'`, `FKeyField='FId'`, `FKeyType='Uuid'`, and `FNameField='FName'`.

## TsPrivilegeType Fields

Identity and ordering:

- `FId`: privilege type ID referenced by `TsPrivilege.FPrivilegeTypeId`.
- `FName`: privilege type display name.
- `FIndex`: ordering.

Privilege semantics:

- `FIsDataPrivilege`: whether this privilege type supports data privileges.
- `FAccessBit`: access bit for the privilege.
- `FRequiredBits`: prerequisite data privilege bits.
- `FDescription`: description.

## Qs.PrivilegeType Field Examples

Use `Qs.PrivilegeType` examples when selecting privilege-type metadata controls:

- Required core field is `FName`.
- `FIsDataPrivilege` uses `CheckBox`.
- `FAccessBit` and `FIndex` use `InputBox-Integer`.
- `FRequiredBits` and `FName` use `InputBox-Text`.
- `FDescription` uses `TextBox` with a larger row span.
- Do not invent new privilege types when standard add/view/modify/delete types already exist; reuse existing `TsPrivilegeType` IDs from the target project.

## Standard Privilege Types

Use these standard `TsPrivilegeType` IDs when creating common unit privileges:

- Add: `00000000-0000-0000-1005-000000000001`, name `新增`, `FIsDataPrivilege=0`, `FAccessBit=0`, index `1`.
- View: `00000000-0000-0000-1005-000000000002`, name `查看`, `FIsDataPrivilege=1`, `FAccessBit=1`, index `2`.
- Modify: `00000000-0000-0000-1005-000000000003`, name `修改`, `FIsDataPrivilege=1`, `FAccessBit=2`, `FRequiredBits='1'`, index `3`.
- Delete: `00000000-0000-0000-1005-000000000004`, name `刪除`, `FIsDataPrivilege=1`, `FAccessBit=3`, `FRequiredBits='1,2'`, index `4`.
- Assign: `00000000-0000-0000-1005-000000000005`, name `分配`, `FIsDataPrivilege=1`, `FAccessBit=4`, `FRequiredBits='1'`, index `5`.
- Manage: `00000000-0000-0000-1005-000000000006`, name `管理`, `FIsDataPrivilege=0`, `FAccessBit=0`, index `6`.
- Close: `00000000-0000-0000-1005-000000000007`, name `關閉`, `FIsDataPrivilege=1`, `FAccessBit=5`, `FRequiredBits='1'`, index `7`.
- Revise: `00000000-0000-0000-1005-000000000008`, name `重新修訂`, `FIsDataPrivilege=0`, `FAccessBit=0`, index `8`.

For the default unit CRUD privileges, use Add, View, Modify, and Delete unless the user or nearby unit requires more.

## TsMenu

`TsMenu` registers the unit page in the menu tree.

Important fields include:

- `FId`: menu ID.
- `FParentId`: parent menu ID.
- `FIndex`: sibling order.
- `FTreeLevel` and `FTreeSerial`: tree placement.
- `FName`: menu display name.
- `FIcon`: menu icon.
- `FType`: menu type, such as `InternalPage`.
- `FPageId`: page opened by the menu, usually the main list page.
- `FOpenMode`: open mode.
- `FLicensed`, `FEnabled`, `FReplaceByChildren`, `FSubMenuSource`, and `FBuiltin`: behavior flags.

## Rules

- Privilege rows must point to the correct `TsUnit.FId` and module ID.
- For modifying or deleting existing `TsPrivilege`, `TsPrivilegeType`, or `TsMenu` rows, generate SQL with `where FId='<id>'`; do not identify the row only by name, unit ID, parent menu ID, or page ID.
- Use nearby units to determine exact `FPrivilegeTypeId` values.
- Add `TsPrivilegeType` rows only when the project truly needs a new privilege type; otherwise reference existing types.
- Menu rows must point to the correct main page ID.
- Keep `FTreeSerial`, `FTreeLevel`, and `FIndex` consistent with the target menu parent.
- When deleting or disabling a unit, handle menu and privilege cleanup together with the unit metadata.
