# Unit

## Use When

Use this reference when the user asks to add, modify, delete, or generate a unit in a QS project.

A QS unit usually includes metadata SQL plus Java files for the target business module. Because QS projects may use different local conventions, inspect the target module before rendering templates.

## Required Inputs

Resolve these values before creating or changing files:

- `<project-name>`: QS parent project name, such as `ecp` or `mes`.
- `<module-name>`: target module name from `<project-name>-module-<module-name>`. When a project has multiple module projects, determine the exact target module project before generating SQL or Java files.
- `{Package}`: Java package for the target module.
- `{UnitCode}`: PascalCase unit code used in Java class names, such as `TestCreateUnit`.
- `{Base}`: base class prefix used by the target QS project, such as `Entity`.
- `<generate-java>`: whether to generate Java files. For entity units, ask before creating Java files when the user does not specify. For non-entity units, generate Java by default unless the user explicitly says not to, because non-entity units are Java method entry points.
- `<unit-code>`: unit code used in SQL metadata, such as `Qs.TestCreateUnit`, `Ecp.Customer`, or `Mes.WorkOrder`. Derive the prefix from the target project name first when it is not provided: `quicksilver-module-main` uses `Qs.*`, `ecp-module-main` uses `Ecp.*`, and `mes-module-xxx` uses `Mes.*`. Then check existing SQL under the target module project's `src/main/resources/QS-MODULE/data/sql/default` directory when present, including `.sql` files directly under `default` and `.sql` files in nested subdirectories, usually no more than three levels deep. Adjust to match the project's established unit-code prefix style. `Qs.*` codes are QS product base units and examples, not the only valid unit-code prefix.
- `<unit-name>`: display name for the unit.
- `<table-name>`: database table name, such as `customer_order`.
- `<field-definitions>`: unit fields with Java types, SQL column names, nullability, defaults, and comments.
- `<primary-key-field>`: primary key Java field name.
- `<primary-key-field-type>`: primary key Java type, such as `Long`, `String`, or `Integer`.
- `<primary-key-column>`: primary key database column name.
- `<delete-mode>`: `hard` for physical delete, `soft` for logical delete.

If a value can be inferred from existing files in the target module, use the inferred value. Ask the user only when inference is unsafe. For multi-module projects, do not create unit SQL until the target module project is known.

## Target Locations

Prefer the target project's existing layout. If no unit pattern exists, use this default:

```text
<project-name>/
├── <project-name>-module-<module-name>/
│   └── src/main/java/<package-path>/
│       ├── action/{UnitCode}Action.java
│       ├── action/impl/{UnitCode}ActionImpl.java
│       ├── api/{UnitCode}Api.java
│       ├── api/impl/{UnitCode}ApiImpl.java
│       ├── dao/{UnitCode}Dao.java
│       ├── dao/impl/{UnitCode}DaoImpl.java
│       ├── home/{UnitCode}Home.java
│       ├── model/{UnitCode}Model.java
│       ├── service/{UnitCode}Service.java
│       └── service/impl/{UnitCode}ServiceImpl.java
└── <project-name>-module-<module-name>/
    └── src/main/resources/QS-MODULE/data/sql/default[/<latest-dir>/]<next-sql-file>.sql
```

When the target project already uses different packages, base classes, or generated-file names, follow the existing names.

Generated Java files must be written under the selected target module project's `src/main/java` tree. Convert `{Package}` to `<package-path>` by replacing `.` with `/`; for example `{Package}=com.jeedsoft.quicksilver.account` maps to `src/main/java/com/jeedsoft/quicksilver/account`.

## Template Sources

Use these bundled templates as starting points:

- `assets/templates/unit/java/Model.template`
- `assets/templates/unit/java/Dao.template`
- `assets/templates/unit/java/DaoImpl.template`
- `assets/templates/unit/java/Service.template`
- `assets/templates/unit/java/ServiceImpl.template`
- `assets/templates/unit/java/Action.template`
- `assets/templates/unit/java/ActionImpl.template`
- `assets/templates/unit/java/Api.template`
- `assets/templates/unit/java/ApiImpl.template`
- `assets/templates/unit/java/Home.template`
- `assets/templates/unit/sql/unit.sql`

Before writing final files, adapt imports, base classes, transaction handling, result wrappers, and route conventions to match the target QS module.

## Unit SQL Metadata

`assets/templates/unit/sql/unit.sql` is not just a business-table template. Treat it as the canonical unit metadata template and keep the related `TsXXX` records consistent.

Load these focused references as needed:

- `references/unit-init.md`: index for the complete base system data in `assets/templates/unit/sql/init.sql`.
- `references/unit-core.md`: business table and `TsUnit`.
- `references/unit-field.md`: `TsField`, field control properties, and field-related helper calls.
- `references/unit-page-tool.md`: `TsPage`, `TsToolItem`, and `TsToolSubItem`.
- `references/unit-form-list-query.md`: `TsForm`, `TsList`, `TsQuerySchema`, and form/list/query helper calls.
- `references/unit-privilege-menu.md`: `TsPrivilege` and `TsMenu`.

Also preserve related helper statements in the SQL template, such as `setQueryFormFields`, `setKeywordFields`, `setFormFields`, `setListFields`, and `setImportTemplateFields`.

When generating a new unit, generate fresh IDs for every metadata row unless the user provides explicit IDs. Keep all foreign-key-style references aligned, especially `FUnitId`, `FPageId`, `FToolItemId`, `FMasterUnitId`, `FModuleId`, and menu `FPageId`.

When generating update or delete SQL for existing unit metadata rows such as units, fields, pages, buttons/tool items, forms, lists, query schemes, privileges, or menus, use the row's `FId` in the `where` condition whenever the table has `FId`. Do not rely on names, codes, titles, or display text as the primary update/delete locator. For modify or delete requests, first scan the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree for the original `insert` statement, usually within three nested directory levels, and extract the row's `FId` from that source statement before generating `update` or `delete` SQL. Add a comment line immediately above each generated `update` or `delete`, using the original row's `FName` or `FTitle`, for example `--客戶名稱`.

## Unit SQL File Placement

When adding a unit, create a new SQL file under the target module project's `src/main/resources/QS-MODULE/data/sql/default` tree. Only module projects such as `<project-name>-module-main` or `<project-name>-module-xxx` have this QS-MODULE SQL directory.

Choose the target directory this way:

- If `default` has no subdirectories, create the file directly under `default`.
- If `default` has subdirectories, sort directory names lexicographically and enter the latest directory.
- Repeat the same lexicographic directory choice for nested subdirectories, usually no more than three levels deep.
- Create the new SQL file in the latest final directory.

Choose the new filename from the latest existing `.sql` filename in that target directory. If the latest file is `quicksilver-7.1.31.21.sql`, create `quicksilver-7.1.31.22.sql`: preserve the prefix and all earlier version segments, and increment only the final numeric segment before `.sql`.

If the target directory has no existing `.sql` files, infer the filename prefix from the project/module and nearby SQL conventions before choosing a starting version.

If `init.sql` exists anywhere under the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree, also add the newly generated unit SQL to that `init.sql` so the module's initial database seed stays in sync with the incremental SQL file. Preserve existing `init.sql` content and append or merge the new unit section following nearby unit-section formatting.

## Text Resource SQL

`TsTextResource` is the QS base i18n resource table. It stores text that frontend code, backend exceptions, unit metadata, and base data can reference by stable `FCode`. At runtime QS resolves `FValue` to the current language through the system i18n mechanism. The `Qs.TextResource` unit uses `FUseSystemI18nTable=1`, and `TsTextResource.FValue` is an i18n-enabled field.

Use this focused workflow when the user asks to add, modify, or delete text resources rather than a whole unit.

Inputs:

- `FCode`: required. Codes normally start with `T.` for text/UI resources or `E.` for error/exception messages, for example `T.Public.OK` or `E.Basic.File.NotFound`.
- `FValue`: required for add and modify. This is the default text, often traditional Chinese in QS base data.

Generation rules:

- For add, generate a fresh UUID for `FId`.
- For add, use `insert into TsTextResource set FId='<uuid>', FCode='<code>', FValue='<value>';`.
- For modify, prefer `where FCode='<code>'` because `FCode` is the stable external reference and has a unique constraint.
- For delete, the user may identify the target by `FCode` or by displayed/default text `FValue`. Treat a target matching the usual `T.*` or `E.*` resource-code pattern as `FCode`.
- For an ordinary-text delete target, first search existing SQL under the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree, and the QS base `init.sql` when relevant, for `insert into TsTextResource` statements with matching `FValue`.
- If exactly one matching `FValue` resource is found, generate delete SQL using that row's `FCode`, not `FValue`.
- If no matching resource is found, say that the text resource code could not be resolved. Only generate `delete from TsTextResource where FValue='<value>';` if the user explicitly wants value-based deletion or asks for a fallback SQL.
- If multiple matching resources are found, list the matching `FCode` values and ask the user which one should be deleted.
- For delete by code, generate `delete from TsTextResource where FCode='<code>';`.
- For fallback delete by value, generate `delete from TsTextResource where FValue='<value>';`.
- If both `FCode` and `FValue` are supplied, delete by `FCode` and include `FValue` only as a comment if useful.
- Escape single quotes in `FCode` and `FValue` by doubling them.
- Preserve placeholders such as `${0}` in `FValue`.
- If the user provides multiple `FCode = FValue` pairs, generate one statement per pair in the same order.

Examples:

```sql
insert into TsTextResource set FId='<uuid>', FCode='T.Public.OK', FValue='確定';

update TsTextResource set FValue='確認' where FCode='T.Public.OK';

delete from TsTextResource where FCode='T.Public.OK';

-- fallback only when FCode cannot be resolved or the user explicitly requests value-based deletion
delete from TsTextResource where FValue='確定';
```

## Template Rendering

Replace all placeholders before writing generated files:

```text
{Package}
{UnitCode}
{Base}
{CacheRegion}
<unit-code>
<unit-name>
<package-path>
<table-name>
<field-definitions>
<java-fields>
<sql-columns>
<sql-values>
<sql-update-assignments>
<primary-key-field>
<primary-key-field-type>
<primary-key-column>
<delete-mode>
<soft-delete-column>
```

Do not leave unresolved placeholders in output files.

For Java templates, render `{CacheRegion}` from `<unit-code>` by lowercasing it and replacing `.` and other non-alphanumeric characters with `_`, for example `Qs.Account` -> `qs_account`.

## Add Unit

1. Locate the QS parent project and exact target module project, such as `<project-name>-module-main` or `<project-name>-module-xxx`. If multiple module projects exist and the target cannot be inferred from the user's request or nearby context, ask which module should receive the new unit.
2. Inspect nearby model, DAO, service, action, API, home, and SQL files.
3. Resolve naming, package, unit-code prefix, and target directories from existing project structure. Infer the prefix from the project name first, such as `quicksilver` -> `Qs`, `ecp` -> `Ecp`, and `mes` -> `Mes`. If the target module project has existing SQL under `src/main/resources/QS-MODULE/data/sql/default`, inspect `.sql` files directly in that directory and in nested SQL subdirectories, usually up to three levels deep, and use the prefix/casing style that matches the user's project conventions.
4. Choose the unit edit type. For ordinary relational entity units, use `TsUnit.FEditId='541c707d-79dd-4dbb-85fc-1a214fd5fce4'`; for non-entity units, use `TsUnit.FEditId='8b7ebd7e-8173-4787-9e34-3d27ad4c9c29'`.
5. Determine whether Java files should be generated. For entity units, if the user did not explicitly request or reject Java generation, ask before creating Java files. For non-entity units, generate Java by default unless the user explicitly says not to.
6. Inspect nearby SQL icon paths and follow the target project's icon style. Multi-theme projects use paths like `quicksilver/image/unit/${theme}/New.svg`; single-theme projects use paths like `quicksilver/image/unit/New.gif`. If nearby SQL is inconclusive, determine the QS version from `com.jeedsoft:quicksilver-gradle-plugin:<version>` in Gradle files, then use the target QS version rule in `references/unit-page-tool.md`.
7. If Java generation is requested, resolve `{Package}` and `{UnitCode}`. When both are known, infer `TsUnit` Java class binding fields using `references/unit-core.md`. If Java generation is not requested, leave `TsUnit` class binding fields unset unless the user explicitly provides them.
8. For relational entity units, resolve `TsUnit.FKeyField`, `FKeyType`, and `FNameField` before rendering fields. If the user does not specify them, default to `FKeyField='FId'`, `FKeyType='Uuid'`, and `FNameField='FName'`.
9. For relational entity units, generate the default business columns implied by those values. With the default key/name settings, create `FId uuid primary key` and `FName varchar(50)`.
10. For relational entity units, generate matching `TsField` rows for the key and name fields. With the default settings, create hidden `FId` metadata using `InputBox-Key` and visible required `FName` metadata using `InputBox-Text`.
11. For non-entity units, generate only the `TsUnit` row by default. Configure the needed Java class bindings just as entity units can, but do not create a business table, `TsField` rows, form/list/query metadata, pages, toolbars, unit privileges, import configuration, or menu entries unless the user or existing project pattern explicitly requires them. For Java templates, use `{Base}=Base` and do not render `Model.template` unless a custom target-project convention requires a model.
12. For entity units, generate the default list metadata: main list, selection list, and homepage list. Add `setListFields` for all three lists using the same field order.
13. For entity units, generate the standard main-list toolbar, including the `Other` dropdown/combo button by default. Add default `Other` subitems `Import`, `ExcelExport`, and `BillPrint`. For the selection list page, generate `ConfirmSelection`, `Add`, and `Open` toolbar buttons by default. For the form page, generate `Save` and `Other`; the form `Other` dropdown has `BillPrint` by default.
14. Render `assets/templates/unit/sql/unit.sql`, including the business table and all related `TsXXX` metadata records that apply to the chosen unit edit type. Do not populate `FHomeClassName`, `FDaoClassName`, `FServiceClassName`, `FActionClassName`, `FApiClassName`, or `FEsDaoClassName` when Java generation is not requested, unless the user explicitly provides class names.
15. Create the SQL file under the selected target module project using the Unit SQL File Placement rules. If `init.sql` exists under the same module's `src/main/resources/QS-MODULE/data/sql/default` tree, also sync the new unit SQL into `init.sql`.
16. Read `references/unit-init.md` when existing system IDs, dictionaries, menus, privilege types, or standard QS product base-unit examples such as `Qs.*` are needed. For project units, keep the target product prefix, such as `Ecp.*` or `Mes.*`.
17. Read the focused metadata references for every `TsXXX` group touched by the unit.
18. If Java generation is requested, render Java templates only for layers used by the target module. Write them under the selected module project's `src/main/java/<package-path>` tree. For non-entity units, skip `Model.template` by default.
19. Add registration, routing, mapper XML, dependency, menu, privilege, or configuration entries only when the existing project requires them and they are not already covered by `unit.sql`.
20. Run the smallest relevant compile or test command available in the target project.

Avoid overwriting existing files unless the user explicitly wants replacement. If a target file already exists, switch to the modify workflow.

## Modify Unit

1. Find all files belonging to the unit, including SQL metadata, business table SQL, model, DAO, service, action, API, home, tests, and configuration.
2. Determine whether the change is a field change, behavior change, validation change, route/API change, or persistence change.
3. Scan the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree for the original metadata `insert` statements that created the affected rows. Prefer extracting `FId` from those statements over guessing from names or codes.
4. Read the focused metadata references for the changed `TsXXX` groups.
5. Update all affected Java layers and related `TsXXX` metadata rows consistently. For metadata SQL updates, locate existing rows by `FId` in the `where` condition whenever possible, and add `--<name-or-title>` above each `update` statement using `FName` or `FTitle` from the original `insert`.
6. Preserve hand-written logic and local formatting.
7. Update migration SQL instead of rewriting historical SQL when the target project uses migrations.
8. Run relevant compile or tests.

For field additions, update the business table columns, `TsField` rows, form/list/query helper calls, Java fields, query projections, validation, and DTO mappings as applicable.

For metadata field modifications or removals, generate `update` or `delete` statements with `where FId='<field-id>'` for `TsField` rows and with the corresponding row `FId` for related page, tool, form, list, query, privilege, or menu rows. Put `--<FTitle-or-FName>` immediately above each generated statement.

## Delete Unit

Determine delete semantics before editing:

- Use soft delete when the target project has fields such as `deleted`, `is_deleted`, `delete_flag`, `dr`, or `status`.
- Use hard delete only when existing units physically delete records or when the user explicitly requests it.

For soft delete:

1. Add or use the existing soft-delete column.
2. Update delete operations to mark rows as deleted.
3. Update list/detail queries to exclude deleted rows.
4. Keep Java types and APIs intact unless the user wants the whole unit removed.

For hard delete:

1. Remove or disable routes and service methods if the user wants the feature removed.
2. Remove DAO or mapper operations only when no callers remain.
3. Add cleanup SQL for related `TsXXX` metadata rows only when the target project uses such scripts.
4. Scan the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree for original metadata `insert` statements and extract `FId` values for every row being deleted.
5. For non-entity units, delete only the `TsUnit` row by default:

```sql
--<unit-name>
delete from TsUnit where FId='<unit-id>';
```

6. For entity units, prefer `where FUnitId='<unit-id>'` for metadata tables that directly contain `FUnitId`, such as `TsField`, `TsPage`, `TsForm`, `TsList`, `TsQuerySchema`, and `TsPrivilege`.
7. Delete child toolbar metadata before parent page metadata. Use `TsPage.FUnitId` to reach toolbar rows:

```sql
--工具欄子項
delete from TsToolSubItem
where FToolItemId in (
    select FId
    from TsToolItem
    where FPageId in (
        select FId
        from TsPage
        where FUnitId='<unit-id>'
    )
);

--工具欄按鈕
delete from TsToolItem
where FPageId in (
    select FId
    from TsPage
    where FUnitId='<unit-id>'
);
```

8. For metadata tables that do not have `FUnitId`, use the appropriate parent reference or `where FId='<id>'`, with `--<FName-or-FTitle>` immediately above each delete statement when deleting specific rows.
9. Delete the `TsUnit` row itself last with `where FId='<unit-id>'`.
10. Search for references and update callers.

## Validation Checklist

- Generated files match the target module's package and directory layout.
- Business table, `TsUnit`, `TsField`, pages, toolbars, forms, lists, privileges, query schemes, and menu records match the unit definition.
- Java class names, variables, and imports compile with the target project style.
- Existing files are modified in place without losing hand-written code.
- No unresolved `<placeholder>` text remains.
- Relevant compile or tests have been run, or the reason they could not run is reported.
