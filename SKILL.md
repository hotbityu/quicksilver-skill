---
name: quicksilver-skill
aliases:
  - qs-skill
description: Use this skill for Quicksilver tasks, especially creating QS projects and generating project SQL or Java files from the bundled templates.
---

# Quicksilver Skill

## Overview

Use this skill when the user asks for Quicksilver or QS project work. The skill is organized by sub-skill, with detailed workflow references and templates stored separately.

## Sub-Skills

### Create QS Project

Use this sub-skill when the user asks to create, scaffold, initialize, or describe a QS project.

- Read `references/create-qs-project.md` for the expected QS project structure and workflow.
- Copy template files and directories from `assets/templates/create-qs-project/<project-type>/` when creating parent projects or subprojects.
- Render template placeholders while copying files, including `<parent-project-name>` and `<qs-version>` in `build.gradle` templates.
- If `<qs-version>` is required, use the user-provided QS version first; only try the configured Maven metadata URL when the user did not provide a version.
- Treat the project name as a user-provided prefix, such as `ecp` or `mes`.
- If the user specifies where to create the QS project, create it at that location; otherwise create `<project-name>/` under the current command-line working directory.
- When the user only provides a project name, create the default skeleton: `<project-name>-build/`, `<project-name>-run/`, and `<project-name>-module-main/`.
- When creating the default parent project skeleton, include `<project-name>-build`, `<project-name>-run`, and `<project-name>-module-main` in `settings.gradle`.
- When the user asks to create a `lib` or `module` subproject under an existing QS parent project, name it `<project-name>-lib-<subproject-name>` or `<project-name>-module-<subproject-name>`.
- After creating any subproject, ensure the parent project's `settings.gradle` includes it, for example `include 'abc-lib-zip'`.
- After creating any `module` subproject, including modules created during parent project initialization, ensure `<project-name>-run/build.gradle` depends on it, for example `implementation project(':abc-module-main')`.
- When adding a unit to a project with multiple module projects, determine the exact target module project before generating SQL or Java files. If it cannot be inferred, ask which module should receive the unit.
- For unit SQL, use the target module project's `src/main/resources/QS-MODULE/data/sql/default` tree. Only module projects such as `<project-name>-module-main` or `<project-name>-module-xxx` have this QS-MODULE SQL directory. If that tree has nested directories, sort directory names lexicographically at each level and create the new SQL in the latest final directory; otherwise create it directly under `default`. Name the file by incrementing the latest SQL filename's final numeric segment, for example `quicksilver-7.1.31.21.sql` -> `quicksilver-7.1.31.22.sql`.
- When adding a unit, if `init.sql` exists under the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree, also sync the generated unit SQL into that `init.sql`.
- For unit modify/delete SQL, scan the selected module project's `src/main/resources/QS-MODULE/data/sql/default` tree for the original `insert` statement, extract the row's `FId`, and generate `update` or `delete` using `where FId='<id>'`. Add a `--<name-or-title>` comment immediately above each generated `update` or `delete`, taking the label from the original insert's `FName` or `FTitle`.
- If the user asks to add an entity unit but does not say whether Java files should be generated, ask before creating Java files. Non-entity units are Java method entry points, so generate Java by default unless the user explicitly says not to. When Java generation is requested, keep generated Java files under the selected target module project's `src/main/java`, in the directory matching the requested Java package. When Java generation is not requested, do not auto-populate `TsUnit` Java class binding fields unless the user provides class names.

### Unit

Use this sub-skill when the user asks to add, modify, delete, or generate a QS unit, including unit SQL or Java files.

- Read `references/unit.md` before generating or changing unit files.
- Inspect the target QS module first and match its existing package names, DAO/service/action/home patterns, SQL location, naming style, and delete conventions.
- Copy or adapt template files from `assets/templates/unit/` only after resolving placeholders from the target project and user-provided unit details.
- Treat add, modify, and delete as separate operations: add creates the unit files, modify updates the existing unit files in place, and delete removes or disables the unit according to the target project's established convention.
- Ask for missing unit code, unit name, table name, fields, module name, base class, or delete semantics only when they cannot be inferred from the target project.

## Template Layout

- `assets/templates/create-qs-project/parent/`: templates for the QS parent project root.
- `assets/templates/create-qs-project/build/`: templates for `<project-name>-build/`.
- `assets/templates/create-qs-project/run/`: templates for `<project-name>-run/`.
- `assets/templates/create-qs-project/lib/`: full template tree for `<project-name>-lib-<subproject-name>/`.
- `assets/templates/create-qs-project/module/`: full template tree for `<project-name>-module-<subproject-name>/`, including web resources when present.
- `assets/templates/unit/java/`: Java templates for unit model, DAO, service, action, API, and home layers.
- `assets/templates/unit/sql/`: SQL templates for unit metadata and table creation.
