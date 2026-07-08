# Unit Base Metadata Reference

Use this reference when you need QS product base metadata while generating or analyzing units.

The skill does not ship a full QS initialization SQL file. It keeps only focused, non-project-specific references:

- `assets/templates/api-discovery/sql/quicksilver-init.sql`: compact QS product `TsUnit` metadata used by API discovery.
- `assets/templates/unit/sql/unit.sql`: sample new-unit SQL with table, `TsUnit`, `TsField`, page, form/list/query, privilege, and menu rows.
- `references/unit-system-tables.md`: field guide for common QS system metadata tables such as dictionaries, menus, privileges, and roles.

Application products can define their own units with prefixes such as `Ecp.*` or `Mes.*`. Always inspect the target project's own SQL tree first when choosing exact IDs, parent menu placement, dictionary rows, or project-specific metadata conventions.

## What To Search

Useful local search patterns:

- `insert into TsUnit set .*FCode='Qs.<Name>'` in `assets/templates/api-discovery/sql/quicksilver-init.sql`: inspect a compact QS base unit registration.
- `insert into TsUnit set` in `assets/templates/unit/sql/unit.sql`: inspect the sample generated unit metadata.
- `insert into TsField set` in `assets/templates/unit/sql/unit.sql`: inspect common field-control metadata.
- `insert into TsPrivilege set` in `assets/templates/unit/sql/unit.sql`: inspect default add/view/modify/delete privilege rows.
- `insert into TsMenu set` in `assets/templates/unit/sql/unit.sql`: inspect a generated menu row pattern.
- `references/unit-system-tables.md`: inspect field names and required fields for dictionaries, menus, privileges, roles, and text resources.

## Focused References

- Core unit metadata: `references/unit-core.md`.
- Field metadata and field-type values: `references/unit-field.md`.
- Page and toolbar metadata: `references/unit-page-tool.md`.
- Form/list/query metadata: `references/unit-form-list-query.md`.
- Privilege and menu metadata: `references/unit-privilege-menu.md`.
- Common system table fields: `references/unit-system-tables.md`.

## Reusable IDs And Seed Data

Prefer IDs from the target project when a generated unit references platform metadata:

- Standard privilege type IDs are documented in `references/unit-privilege-menu.md`.
- Standard field control values are documented in `references/unit-field.md`.
- Dictionary IDs, menu parent IDs, module IDs, and role IDs should be read from the target module SQL when project-specific placement matters.
- If target SQL does not define a needed base ID, use the stable IDs documented in focused references only when they are explicitly listed there.

## Generation Rules

- Use `assets/templates/unit/sql/unit.sql` as the small new-unit template.
- Use focused references for table fields and stable constants instead of copying broad base data.
- Do not duplicate base system rows that already exist in the target project.
- When a generated unit needs a dictionary-backed field, use `references/unit-field.md` for standard field types and inspect the target project's dictionary rows for custom dictionaries.
- When creating menu entries, inspect the target project's `TsMenu` rows for the target parent menu and copy its `FIndex`, `FTreeLevel`, `FTreeSerial`, `FType`, `FOpenMode`, `FBuiltin`, and `FIsSystemLevel` conventions.
- When creating privileges, reuse standard `TsPrivilegeType` IDs from `references/unit-privilege-menu.md` unless the target project uses custom privilege types.
