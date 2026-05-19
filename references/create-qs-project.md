# Create QS Project

## Use When

Use this reference when the user asks to create, scaffold, initialize, inspect, or generate files for a QS project.

## Expected Project Structure

```text
<project-name>/
├── <project-name>-module-<module-name>/
├── <project-name>-lib-<lib-name>/
├── <project-name>-run/
├── <project-name>-build/
├── gradle/
├── build.gradle
├── settings.gradle
├── gradlew
└── gradlew.bat
```

## Directory Roles

- `<project-name>` is provided by the user when creating a QS project, such as `ecp`, `mes`, or another custom project name.
- `<module-name>` is a user-provided or template-defined business module name, such as `crm`, `hr`, `oa`, or another custom module.
- `<lib-name>` is a user-provided or template-defined library module name, such as `net`, `zip`, or another custom library.
- `<project-name>-module-<module-name>/`: business module directories.
- `<project-name>-lib-<lib-name>/`: library module directories.
- `<project-name>-run/`: runtime, startup, configuration, or SQL-related project files.
- `<project-name>-build/`: build support files.
- `gradle/`, `gradlew`, `gradlew.bat`: Gradle wrapper files.
- `build.gradle`, `settings.gradle`: root Gradle project configuration.

For example, if the project name is `ecp` and the requested modules are `crm` and `report`, create directories such as `ecp-module-crm/`, `ecp-module-report/`, and `ecp-run/`. If the requested libraries are `net` and `zip`, create directories such as `ecp-lib-net/` and `ecp-lib-zip/`.

## Default Skeleton

When the user asks to create a QS project and only provides the project name, create this default structure:

```text
<project-name>/
├── <project-name>-build/
├── <project-name>-run/
└── <project-name>-module-main/
```

In the default skeleton, `main` is the default module name used for the module subproject. For example, if the user asks to create an `abc` project, create `abc-build/`, `abc-run/`, and `abc-module-main/`.

When creating the default skeleton, create or update `settings.gradle` so it includes the default subprojects:

```gradle
include '<project-name>-build'
include '<project-name>-run'
include '<project-name>-module-main'
```

For example, when creating an `abc` project, `settings.gradle` should include:

```gradle
include 'abc-build'
include 'abc-run'
include 'abc-module-main'
```

## Target Location

If the user specifies a target location for the QS project, create the project root there.

If the user does not specify a target location, use the current command-line working directory as the parent directory and create `<project-name>/` inside it. For example, if the current working directory is `/workspace` and the user asks to create an `abc` project, create `/workspace/abc/`.

## Template Sources

When creating a parent project or subproject, copy the matching template files and directories from `assets/templates/create-qs-project/`.

Template directories are organized by project type:

- `parent/`: copy into the QS parent project root.
- `build/`: copy into `<project-name>-build/`.
- `run/`: copy into `<project-name>-run/`.
- `lib/`: copy the full template tree into `<project-name>-lib-<subproject-name>/`, including `build.gradle`, `src/main/java/`, and `src/main/resources/`.
- `module/`: copy the full template tree into `<project-name>-module-<subproject-name>/`, including `build.gradle`, `src/main/java/`, and `src/main/resources/META-INF/` when present.

For the default skeleton, use these template sources:

- Parent project root: `assets/templates/create-qs-project/parent/`
- `<project-name>-build/`: `assets/templates/create-qs-project/build/`
- `<project-name>-run/`: `assets/templates/create-qs-project/run/`
- `<project-name>-module-main/`: `assets/templates/create-qs-project/module/`

When creating a `lib` subproject, copy from `assets/templates/create-qs-project/lib/`. When creating a `module` subproject, copy from `assets/templates/create-qs-project/module/`.

Module templates may include web resources such as `src/main/resources/META-INF/web-fragment.xml`. Preserve these files unless the user asks to customize them.

## Template Rendering

Do not copy template files as raw text when they contain placeholders. While copying files from `assets/templates/create-qs-project/`, replace known placeholders with project-specific values.

Current placeholders:

- `<parent-project-name>`: replace with the QS parent project name, such as `abc`, `ecp`, or `mes`.
- `<qs-version>`: replace with the QS version requested by the user.

Known template files that use these placeholders:

- `assets/templates/create-qs-project/parent/build.gradle`
- `assets/templates/create-qs-project/build/build.gradle`

If the user provides the QS version, always use that value as `<qs-version>`. For example, if the user asks to create a QS project named `abc` with QS version `7.1.32.12`, render `<qs-version>` as `7.1.32.12`.

For existing or inherited QS projects, the QS version is usually available from the Gradle plugin dependency. Search Gradle files for `com.jeedsoft:quicksilver-gradle-plugin:<version>` and use that `<version>` as the QS version. This is the preferred source when inspecting an existing project. If writing a custom Gradle task inside the project, `$qsVersion` can also be used to read the resolved QS version.

If the user does not provide the QS version while creating a parent project and a template requires `<qs-version>`, try to resolve the latest QS version from this Maven metadata URL:

```text
http://qbi.qbiai.com:23801/repository/maven-releases/com/jeedsoft/quicksilver-gradle-plugin/maven-metadata.xml
```

When metadata lookup is needed, resolve `<qs-version>` in this order:

1. Use `<latest>` when present and non-empty.
2. Otherwise use `<release>` when present and non-empty.
3. If neither value can be determined, ask the user for the QS version before rendering the template.

The currently verified `<latest>` value is `7.2.2.beta26.08`.

## Creating Subprojects

When the user asks to create a subproject inside an existing QS parent project, combine the parent project name, subproject type, and subproject name:

```text
<project-name>-<subproject-type>-<subproject-name>/
```

Supported subproject types:

- `lib`: create `<project-name>-lib-<subproject-name>/`
- `module`: create `<project-name>-module-<subproject-name>/`

For example, if the parent project is `abc` and the user asks to create a `lib` project named `test`, create `abc-lib-test/` under the `abc/` parent project. If the user asks to create a `module` project named `test`, create `abc-module-test/`.

## Gradle Settings

After creating any subproject, check the parent project's `settings.gradle`.

If the new subproject is not already included, add an `include` entry using the subproject directory name:

```gradle
include '<project-name>-<subproject-type>-<subproject-name>'
```

For example, after creating `abc-lib-zip/`, ensure `settings.gradle` contains:

```gradle
include 'abc-lib-zip'
```

Do not add a duplicate `include` entry if the project is already present.

## Run Project Dependencies

After creating any `module` subproject, including modules created while initializing a parent project, check the run project's `build.gradle`:

```text
<project-name>-run/build.gradle
```

Ensure its `dependencies` block contains an implementation dependency on the module project:

```gradle
implementation project(':<project-name>-module-<subproject-name>')
```

For example, after creating `abc-module-main/`, whether as part of parent project creation or as a later subproject addition, ensure `abc-run/build.gradle` contains this inside `dependencies`:

```gradle
implementation project(':abc-module-main')
```

Do not add a duplicate dependency if the same `implementation project(...)` entry already exists.

## Generation Guidance

1. Ask for the project name if it is not clear.
2. Use the user-specified target location when provided; otherwise create the project under the current command-line working directory.
3. If the user only provides the project name, use the default skeleton without asking for extra modules.
4. When creating the default skeleton, include `<project-name>-build`, `<project-name>-run`, and `<project-name>-module-main` in `settings.gradle`.
5. If the user asks to create a `lib` or `module` subproject and provides its name, create it under the parent project with the standard combined name.
6. Copy the matching template files and directories from `assets/templates/create-qs-project/<project-type>/` into the created project or subproject.
7. Render known template placeholders during copy, including `<parent-project-name>` and `<qs-version>`.
8. If `<qs-version>` is required during parent project creation and the user did not provide it, try the Maven metadata URL first; ask the user only if the latest version cannot be resolved.
9. After creating a subproject, add it to `settings.gradle` if it is not already included.
10. After creating a `module` subproject, including modules created during parent project initialization, add `implementation project(':<project-name>-module-<subproject-name>')` to `<project-name>-run/build.gradle` if it is not already present.
11. Ask which business modules and library modules should be created only when the user requests a non-default module layout.
12. Ask which business module should receive Java files when the target module is ambiguous.
13. Preserve the `<project-name>-module-<module-name>` and `<project-name>-lib-<lib-name>` naming patterns unless the user gives a different module layout.
