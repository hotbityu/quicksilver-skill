# QS System Table Field Reference

Use this reference when generating or modifying common QS system metadata rows without relying on a full initialization SQL file. Prefer exact IDs and ordering from the target project's own SQL when available.

## Dictionaries

### TsDictionary

`TsDictionary` defines a dictionary catalog used by fields and controls.

Common fields:

- `FId`: dictionary ID.
- `FName`: display name.
- `FCode`: stable code when the project uses code-based lookup.
- `FDescription`: description.
- `FIsSystemLevel`: system-level flag.
- `FEnabled`: enabled flag.
- `FIndex`: ordering.

Required fields are usually `FId` and `FName`; include `FCode`, `FEnabled`, `FIndex`, and `FIsSystemLevel` when nearby project rows use them.

### TsDictionaryItem

`TsDictionaryItem` defines one value under a dictionary.

Common fields:

- `FId`: item ID.
- `FDictionaryId`: owning dictionary ID.
- `FName`: display name.
- `FValue`: submitted or stored value.
- `FCode`: stable code when the project uses code-based lookup.
- `FParentId`: parent item ID for hierarchical dictionaries.
- `FIndex`: ordering.
- `FEnabled`: enabled flag.
- `FDescription`: description.
- `FIsSystemLevel`: system-level flag.

Required fields are usually `FId`, `FDictionaryId`, `FName`, and `FValue`. Keep `FIndex` unique within the same dictionary when the target project orders dictionary values explicitly.

## Menus

### TsMenu

`TsMenu` registers a page or catalog in a menu tree.

Common fields:

- `FId`: menu ID.
- `FParentId`: parent menu ID.
- `FIndex`: sibling order.
- `FTreeLevel`: tree depth.
- `FTreeSerial`: dotted tree serial such as `001.002.016`.
- `FName`: display name.
- `FIcon`: icon path.
- `FType`: menu type, commonly `InternalPage` for unit pages.
- `FPageId`: page opened by this menu.
- `FOpenMode`: open mode, commonly `Tab`.
- `FTabTitleSource`: tab title source, commonly `MenuName`.
- `FLicensed`: license flag.
- `FEnabled`: enabled flag.
- `FReplaceByChildren`: whether children replace the parent menu.
- `FSubMenuSource`: child source, commonly `MenuTable`.
- `FBuiltin`: built-in flag.
- `FIsSystemLevel`: system-level flag.

When adding a menu row, copy the parent branch's `FTreeLevel`, `FTreeSerial`, `FType`, `FOpenMode`, `FTabTitleSource`, `FSubMenuSource`, `FBuiltin`, and system-level conventions from the target project.

## Privileges

### TsPrivilegeType

`TsPrivilegeType` defines reusable privilege semantics.

Common fields:

- `FId`: privilege type ID.
- `FName`: display name.
- `FIndex`: ordering.
- `FIsDataPrivilege`: whether row-level data privilege rules apply.
- `FAccessBit`: access bit used by data privilege logic.
- `FRequiredBits`: prerequisite access bits.
- `FDescription`: description.

Standard common privilege type IDs are documented in `references/unit-privilege-menu.md`.

### TsPrivilege

`TsPrivilege` grants a unit-level permission.

Common fields:

- `FId`: privilege ID.
- `FName`: display name.
- `FIndex`: ordering.
- `FUnitId`: owning unit ID.
- `FModuleId`: owning module ID.
- `FPrivilegeTypeId`: privilege type ID.
- `FUseExisting`: whether to reuse an existing privilege.
- `FSourcePrivilegeId`: source privilege ID when reusing or deriving.
- `FEditId`: edit/configuration ID.
- `FIsSystemLevel`: system-level flag.

For ordinary CRUD unit privileges, create add/view/modify/delete rows unless the target project uses a different pattern.

## Roles

### TsRole

`TsRole` defines a user role or permission group.

Common fields:

- `FId`: role ID.
- `FName`: display name.
- `FCode`: stable code when the project uses code-based lookup.
- `FIndex`: ordering.
- `FEnabled`: enabled flag.
- `FBuiltin`: built-in flag.
- `FIsSystemLevel`: system-level flag.
- `FDescription`: description.

Do not create roles during ordinary unit generation unless the user explicitly requests role setup or the target project has a clear module-specific role pattern.

### TsRolePrivilege

`TsRolePrivilege` links roles to privileges.

Common fields:

- `FId`: row ID.
- `FRoleId`: role ID.
- `FPrivilegeId`: privilege ID.
- `FUnitId`: owning unit ID when the project records it.
- `FModuleId`: module ID when the project records it.
- `FDataPrivilege`: data privilege value when used by the target project.
- `FDataPrivilegeSql`: SQL filter for data privilege when used.
- `FEnabled`: enabled flag.
- `FIsSystemLevel`: system-level flag.

Add role-privilege rows only when the user asks to bind a role or when nearby module SQL clearly grants default unit privileges to a known role.

## Text Resources

### TsTextResource

`TsTextResource` stores i18n text resources.

Common fields:

- `FId`: resource ID.
- `FCode`: stable resource code, commonly starting with `T.` or `E.`.
- `FValue`: default text value.
- `FDescription`: description.

Escape single quotes in SQL string values by doubling them.

## Rules

- For modifications and removals, identify rows by `FId` whenever the table has `FId`.
- When `FId` is unknown, search the target project SQL by stable code first, then by name only if the table has no better identifier.
- Keep foreign-key-style fields aligned: dictionary item `FDictionaryId`, menu `FPageId`, privilege `FUnitId`/`FModuleId`, and role privilege `FRoleId`/`FPrivilegeId`.
- Avoid broad seed data in generated SQL. Generate only the rows needed for the requested unit or metadata change.
