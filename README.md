# Quicksilver Skill

`quicksilver-skill` 是一個面向 Quicksilver/QS 專案開發的 Codex Skill。它把建立 QS 專案、生成單元 SQL/Java、處理單元修改刪除，以及產生文字資源國際化 SQL 的規則整理成可重複使用的工作流程。

## 主要能力

- 建立 QS 父專案、`run` 專案、`build` 專案與預設 `module-main`。
- 在既有 QS 父專案中新增 `lib` 或 `module` 子專案。
- 依照 QS 模組結構生成單元 SQL，並放入正確的 `src/main/resources/QS-MODULE/data/sql/default` 目錄。
- 依既有專案風格生成或調整 Java 層檔案，例如 model、dao、service、action、api、home。
- 依原始 SQL metadata 產生修改或刪除 SQL，優先使用原始資料列的 `FId`。
- 生成 `TsTextResource` 文字資源新增、修改、刪除 SQL，支援 `T.*` 與 `E.*` 國際化資源編碼。

## 專案結構

```text
quicksilver-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── templates/
│       ├── create-qs-project/
│       └── unit/
└── references/
    ├── create-qs-project.md
    ├── unit.md
    ├── unit-core.md
    ├── unit-field.md
    ├── unit-form-list-query.md
    ├── unit-icons.md
    ├── unit-init.md
    ├── unit-page-tool.md
    └── unit-privilege-menu.md
```

## 使用方式

在 Codex 中可以直接提到 `$quicksilver-skill` 或描述 QS 任務，例如：

```text
使用 $quicksilver-skill 建立一個 ecp 專案，QS 版本 7.1.32.12
```

```text
幫我在 mes-module-main 新增一個客戶單元，表名為 TMCustomer
```

```text
新增文字資源 T.Public.Save = 保存
```

```text
刪除文字資源 確定
```

## 建立 QS 專案

當只提供專案名稱時，技能會建立預設骨架：

```text
<project-name>/
├── <project-name>-build/
├── <project-name>-run/
└── <project-name>-module-main/
```

建立子專案時，會遵循 QS 命名規則：

- `lib` 子專案：`<project-name>-lib-<subproject-name>`
- `module` 子專案：`<project-name>-module-<subproject-name>`

新增子專案後，技能會同步更新父專案的 `settings.gradle`。新增 `module` 子專案時，也會確保 `<project-name>-run/build.gradle` 依賴該 module。

## 單元生成

單元生成以 `references/unit.md` 為主要流程說明，並使用 `assets/templates/unit/` 中的 Java 與 SQL 模板。

生成前會先判斷或詢問以下資訊：

- QS 父專案名稱與目標 module。
- 單元編碼，例如 `Qs.Customer`、`Ecp.Customer`、`Mes.WorkOrder`。
- 單元名稱、資料表名稱、主鍵欄位、名稱欄位與欄位定義。
- 是否需要生成 Java 檔案。
- 目標專案既有的 package、base class、SQL 目錄與命名風格。

SQL 檔案會放在目標 module 的：

```text
src/main/resources/QS-MODULE/data/sql/default
```

如果目錄中有版本化 SQL 檔，會依現有命名遞增最後一段數字，例如：

```text
quicksilver-7.1.31.21.sql -> quicksilver-7.1.31.22.sql
```

如果同一 SQL tree 中存在 `init.sql`，新增單元 SQL 也會同步到 `init.sql`。

## 修改與刪除單元

修改或刪除既有單元 metadata 時，技能會先掃描目標 module 的 SQL 目錄，尋找原始 `insert` 語句並取得 `FId`。產生 `update` 或 `delete` SQL 時，會優先使用：

```sql
where FId='<id>'
```

並在語句前加入來自原始 `FName` 或 `FTitle` 的註解，例如：

```sql
--客戶名稱
update TsField set FTitle='客戶' where FId='<field-id>';
```

## 文字資源

`TsTextResource` 是 QS 的基礎國際化文字資源表。前端或後端引用穩定的 `FCode`，系統會依目前語言解析 `FValue`。

常見編碼規則：

- `T.*`：一般文字、UI 文案、提示文字。
- `E.*`：錯誤、例外、校驗訊息。

新增文字資源時，提供 `FCode` 與 `FValue`，技能會產生新的 UUID：

```sql
insert into TsTextResource set FId='<uuid>', FCode='T.Public.OK', FValue='確定';
```

修改文字資源時，使用 `FCode` 定位：

```sql
update TsTextResource set FValue='確認' where FCode='T.Public.OK';
```

刪除文字資源時，如果使用者提供 `T.*` 或 `E.*`，會直接按 `FCode` 刪除：

```sql
delete from TsTextResource where FCode='T.Public.OK';
```

如果使用者提供普通文字，例如「確定」，技能會先在現有 SQL 中查找匹配的 `FValue`，找到唯一對應資源時再按 `FCode` 刪除。找不到或找到多筆時，會回報結果並要求確認。

## 參考文件

- `references/create-qs-project.md`：QS 專案建立流程、目錄規則、模板渲染與 Gradle 設定。
- `references/unit.md`：單元新增、修改、刪除、SQL 位置、文字資源 SQL。
- `references/unit-core.md`：業務表與 `TsUnit` metadata。
- `references/unit-field.md`：`TsField` 與欄位控制規則。
- `references/unit-page-tool.md`：`TsPage`、`TsToolItem`、`TsToolSubItem`。
- `references/unit-form-list-query.md`：`TsForm`、`TsList`、`TsQuerySchema`。
- `references/unit-privilege-menu.md`：`TsPrivilege` 與 `TsMenu`。
- `references/unit-init.md`：QS 基礎系統資料 `init.sql` 的搜尋索引。
- `references/unit-icons.md`：QS 圖示路徑與版本差異。

## 模板資源

- `assets/templates/create-qs-project/parent/`：父專案根目錄模板。
- `assets/templates/create-qs-project/build/`：`<project-name>-build` 模板。
- `assets/templates/create-qs-project/run/`：`<project-name>-run` 模板。
- `assets/templates/create-qs-project/lib/`：`lib` 子專案模板。
- `assets/templates/create-qs-project/module/`：`module` 子專案模板。
- `assets/templates/unit/java/`：單元 Java 層模板。
- `assets/templates/unit/sql/`：單元 SQL metadata 模板與 QS 基礎 `init.sql`。

## 維護注意事項

- `SKILL.md` 只保留觸發後最常用的高階流程，詳細規則放在 `references/`。
- 更新單元生成邏輯時，優先同步 `references/unit.md` 與相關 focused reference。
- 更新模板時，確認 placeholder 能完整渲染，不要留下 `<placeholder>` 或 `{Placeholder}`。
- 修改 `TsTextResource` 規則時，保持新增、修改、刪除三種 SQL 行為一致。
