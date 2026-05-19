# Unit Init SQL Reference

Use this reference when you need existing QS system metadata from `assets/templates/unit/sql/init.sql`.

`init.sql` is the complete QS product base system data source. It contains table DDL, standard `Qs.*` unit registrations, field definitions, pages, tools, forms, lists, query schemes, menus, dictionaries, privilege types, system privileges, parameters, roles, tenant configuration, and other platform seed data. Application products can define their own units with prefixes such as `Ecp.*` or `Mes.*` based on these QS base units.

Do not load or copy the whole file into context. Search it by marker, table name, ID, or unit code.

## How To Search

Useful search patterns:

- `^--Qs\\.`: list standard unit sections.
- `--Qs.Unit`, `--Qs.Field`, `--Qs.Page`, etc.: jump to a standard unit section.
- `create table Ts<FieldName>`: inspect a table structure.
- `insert into TsUnit set .*FCode='Qs.<Name>'`: inspect a QS base unit registration. For application projects, adapt the pattern to the target prefix, such as `Ecp.<Name>` or `Mes.<Name>`.
- `insert into TsEdit set .*FUnitId='<unit-id>'` plus nearby `setEditFields` and `setEditHiddenPages`: inspect edit/entity types, supported fields, and hidden slave pages. For `Qs.Unit`, see `references/unit-core.md`.
- `insert into TsDictionary set` and `insert into TsDictionaryItem set`: inspect dictionaries used by `FDictionaryId`.
- `TsDictionary.FId='4d2eec6d-5f41-4c38-9ad1-c04ded9e3110'`: standard `QS-欄位-類型` dictionary used by `TsField.FType`; see `references/unit-field.md`.
- `insert into TsPrivilegeType set`: inspect standard privilege type IDs.
- `insert into TsMenu set`: inspect system menu placement and parent IDs.

## Standard Unit Sections

The base file contains many `--Qs.*` sections. These are QS product base-unit examples. Unit-generation work most often needs these:

- Core unit metadata: `--Qs.Unit`, `--Qs.Field`, `--Qs.Relation`.
- Page and toolbar metadata: `--Qs.Page`, `--Qs.PageGroup`, `--Qs.Script`, `--Qs.ToolItem`, `--Qs.ToolSubItem`, `--Qs.SpecialPath`.
- Layout and query metadata: `--Qs.Form`, `--Qs.List`, `--Qs.QuerySchema`.
- Menu metadata: `--Qs.Menu`, `--Qs.MenuNumber`, `--Qs.MobileMenu`, `--Qs.IconMenuCatalog`, `--Qs.IconMenu`.
- Privilege metadata: `--Qs.PrivilegeType`, `--Qs.Privilege`, `--Qs.RolePrivilege`, `--Qs.RelationPrivilege`, `--Qs.SlavePagePrivilege`.
- Dictionary metadata: `--Qs.Dictionary`, `--Qs.DictionaryItem`.
- Module and configuration examples: `--Qs.ParameterGroup`, `--Qs.ParameterDefinition`, `--Qs.Language`.
- Integration/API examples: `--Qs.DirectApiGroup`, `--Qs.DirectApi`, `--Qs.LocalApiGroup`, `--Qs.LocalApi`, `--Qs.RemoteApiGroup`, `--Qs.RemoteApi`, `--Qs.Webhook`, `--Qs.WebServiceProvider`, `--Qs.WebServiceInterface`.

## Reusable IDs And Seed Data

Prefer existing IDs from `init.sql` when a generated unit references platform metadata:

- Standard privilege type IDs are defined by `TsPrivilegeType` and documented in `references/unit-privilege-menu.md`.
- Dictionary IDs appear in `TsField.FDictionaryId`, `TsPage` controls, toolbar controls, form/list/query controls, and system parameter definitions.
- Entity reference IDs appear in `TsField.FEntityUnitId` and commonly point to `Qs.Unit`, `Qs.Page`, `Qs.Dictionary`, `Qs.PrivilegeType`, `Qs.QuerySchema`, or user/role units.
- Standard menu parent IDs appear in `TsMenu`; use nearby menu sections to place new system menus.
- Standard module IDs appear in `TsUnit.FModuleId`, `TsPrivilege.FModuleId`, and `TsMenu.FParentId`.

## Generation Rules

- Use `unit.sql` as the small new-unit template; use `init.sql` as the source of existing platform conventions and IDs.
- Do not duplicate base system rows already provided by `init.sql`.
- When a generated unit needs a dictionary-backed field, search `init.sql` for nearby `FDictionaryId` usage and `TsDictionaryItem` values before choosing or creating a dictionary.
- When creating menu entries, search `init.sql` for the target parent menu and copy its `FIndex`, `FTreeLevel`, `FTreeSerial`, `FType`, `FOpenMode`, `FBuiltin`, and `FIsSystemLevel` conventions.
- When creating privileges, reuse standard `TsPrivilegeType` IDs and match `FEditId`, `FModuleId`, and `FIsSystemLevel` to nearby units.
- When creating pages and toolbars, use existing standard sections to choose `FType`, `FUrl`, event handlers, icons, query box settings, and toolbar button patterns.
