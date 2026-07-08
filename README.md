# Quicksilver Skill

`quicksilver-skill` 是一個面向 Quicksilver/QS 專案開發的 Codex Skill。它把建立 QS 專案、生成單元 SQL/Java、處理單元修改刪除、產生文字資源國際化 SQL，以及盤點匯出 module API 的規則整理成可重複使用的工作流程。

## 安裝

```bash
npx skills add https://github.com/hotbityu/quicksilver-skill/tree/main/skills/quicksilver-skill
```

也可以从仓库安装指定 skill：

```bash
npx skills add hotbityu/quicksilver-skill --skill quicksilver-skill
```

## 移除

```bash
npx skills remove quicksilver-skill
```

## 主要能力

- 建立 QS 父專案、`run` 專案、`build` 專案與預設 `module-main`。
- 在既有 QS 父專案中新增 `lib` 或 `module` 子專案。
- 依照 QS 模組結構生成單元 SQL，並放入正確的 `src/main/resources/QS-MODULE/data/sql/default` 目錄。
- 依既有專案風格生成或調整 Java 層檔案，例如 model、dao、service、action、api、home。
- 依原始 SQL metadata 產生修改或刪除 SQL，優先使用原始資料列的 `FId`。
- 生成 `TsTextResource` 文字資源新增、修改、刪除 SQL，支援 `T.*` 與 `E.*` 國際化資源編碼。
- 掃描 QS module 專案中的 API 實作、`@Api` 標註、單元 metadata 與繼承 API，輸出有來源依據的 API Markdown 報告。
- 使用 `skills/quicksilver-skill/scripts/export_qs_api.py` 快速完成 API 第一輪匯出，再視需要補充複雜 handler 的深層分析。
- 分析 API 路徑、請求欄位、回應欄位、可用性與來源檔案，並將推斷或待確認內容明確標示在報告中。

## 專案結構

```text
quicksilver-skill/
├── README.md
└── skills/
    └── quicksilver-skill/
        ├── SKILL.md
        ├── assets/
        │   └── templates/
        │       ├── api-discovery/
        │       ├── create-qs-project/
        │       └── unit/
        ├── scripts/
        │   └── export_qs_api.py
        └── references/
            ├── api-discovery.md
            ├── create-qs-project.md
            ├── unit.md
            ├── unit-core.md
            ├── unit-field.md
            ├── unit-form-list-query.md
            ├── unit-icons.md
            ├── unit-init.md
            ├── unit-page-tool.md
            ├── unit-privilege-menu.md
            └── unit-system-tables.md
```

根目錄刻意不放 `SKILL.md`，避免 `npx skills add` 將 repository root 當成單檔 skill，只安裝 `SKILL.md` 而漏掉 `references/`、`scripts/` 和 `assets/`。

## 使用方式

在 Codex 中可以直接提到 `$quicksilver-skill`、`$qs-skill`，或直接描述 QS 任務。技能會依任務自動選擇下列子 skill。

## 子 Skill 一覽

| 子 Skill | 適用任務 | 主要輸出 |
| --- | --- | --- |
| Create QS Project | 建立 QS 父專案、預設骨架，或新增 `lib` / `module` 子專案。 | 專案目錄、Gradle 設定與基礎 module 結構。 |
| Unit | 新增、修改、刪除 QS 單元，包含 SQL metadata 與 Java 層檔案。 | 單元 SQL、model、dao、service、action、api、home 等檔案。 |
| Text Resource | 新增、修改、刪除 `TsTextResource` 國際化文字資源。 | `insert`、`update` 或 `delete` SQL。 |
| API Discovery | 盤點、分析、匯出 QS module 專案中的 API。 | `docs/<project-name>-api-discovery.md` API Markdown 報告。 |

### Create QS Project

用於建立 QS 父專案、預設骨架，或在既有 QS 父專案中新增 `lib` / `module` 子專案。

範例：

```text
使用 $quicksilver-skill 建立一個 ecp 專案，QS 版本 7.1.32.12
```

```text
使用 $qs-skill 在現有 abc 專案下新增 module 子專案 report
```

### Unit

用於新增、修改、刪除 QS 單元，包含單元 SQL metadata，以及依專案風格生成 model、dao、service、action、api、home 等 Java 檔案。

範例：

```text
使用 $quicksilver-skill 幫我在 mes-module-main 新增一個客戶單元，單元編碼 Mes.Customer，表名 TMCustomer，需要生成 Java 檔案
```

```text
使用 $qs-skill 修改 Ecp.Customer 單元，把客戶名稱欄位標題改成「客戶」
```

### Text Resource

用於新增、修改、刪除 `TsTextResource` 文字資源 SQL。`T.*` 通常是 UI / 一般文字，`E.*` 通常是錯誤或校驗訊息。

範例：

```text
使用 $quicksilver-skill 新增文字資源 T.Public.Save = 保存
```

```text
使用 $qs-skill 刪除文字資源 確定
```

### API Discovery

用於盤點 QS module 專案中的 API，掃描 `XXXApiImpl`、`@Api` 標註、繼承自 `EntityApiImpl` 的 API、單元 SQL metadata 與相關 Java 呼叫，並在 QS 父專案的 `docs/` 目錄輸出 Markdown 報告。

範例：

```text
使用 $quicksilver-skill 掃描這個 QS 專案所有 module 的 API，輸出 ecp-api-discovery.md
```

```text
使用 $qs-skill 只分析 ecp-module-main 的 API，整理每個 API 的路徑、請求欄位、回應欄位與來源檔案
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

## API Discovery

API Discovery 以 `references/api-discovery.md` 為主要流程說明，並使用 `assets/templates/api-discovery/java/` 中的 API annotation 與 result contract 作為掃描參考。

在此 repository 中快速匯出可直接使用：

```bash
python3 skills/quicksilver-skill/scripts/export_qs_api.py /path/to/qs-project
python3 skills/quicksilver-skill/scripts/export_qs_api.py /path/to/qs-project /path/to/output.md
```

`export_qs_api.py` 會掃描 module、`@Api` handler、`TsUnit` SQL metadata 與 `EntityApiImpl` 繼承 API，快速產生第一版 Markdown。對於下游 service 才解析欄位、動態表單/列表 metadata、巢狀物件或 full-powers servlet response，仍應依 `references/api-discovery.md` 再補充人工分析。

技能會先定位 QS 父專案與所有 module 專案，例如：

```text
<project-name>-module-main
<project-name>-module-base
<project-name>-module-xxx
```

技能會先從 `*-module-*`、`*-run`、`*-build`、`*-lib-*` 等子專案名稱反推出真正的 QS 專案名。例如父目錄是 `quicksilver-7.1-task1/`，但子專案有 `quicksilver-module-main` 與 `quicksilver-run`，則會推得專案名為 `quicksilver`。

預設會掃描所有 module，除非使用者明確要求只掃描某一個 module。輸出檔預設位於 QS 父專案的 `docs/` 目錄：

```text
docs/<project-name>-api-discovery.md
```

掃描時會優先分析：

- `api.impl` package 下的 `XXXApiImpl` 類別。
- 方法上的 `@Api` 標註，以及實際的請求欄位讀取與回應組裝程式碼；`input` / `output` 屬性只作為輔助參考。
- 掃描會忽略 Java 註釋中的 `@Api`；對超大 `ApiImpl`、`@Api` 很多的類、或超長 handler 方法體，採用 annotation-first 模式，只保留 `@Api.input` / `@Api.output`、路徑、token 與回應 metadata，跳過方法體深度欄位掃描，避免單一複雜類拖慢整體匯出。欄位分析以處理器程式碼優先，`@Api.input` / `@Api.output` 只作為 fallback 或補充 metadata。
- 只有沿 superclass chain 實際解析到繼承 `@Api` 的 API class，才補繼承 API，並且要按每個具體 unit 與 concrete API class 展開成實際路由；`BaseApiImpl`、`EntityApiImpl`、`BusinessEntityApiImpl`、`TreeEntityApiImpl` 是頂級/base API class，只作為契約來源，本身不輸出獨立 API；掃描時會用內建 `BaseApiImpl.java` 模板補齊缺失的非實體 base class，但像 `MiscApiImpl` 這類只繼承到 `BaseApiImpl` 的非實體單元，不應補出 entity-style inherited APIs；目前 `EntityApiImpl` 已包含舊版 `BusinessEntityApiImpl`、`TreeEntityApiImpl` 的行為，舊專案仍可能引用後兩者，因此會用內建 `BusinessEntityApiImpl.java`、`TreeEntityApiImpl.java`、`EntityApiImpl.java` 模板補齊缺失的 legacy base class 並解析到 `EntityApiImpl` 契約。
- 繼承 API 也要寫成具體路由的 API 區塊，並在該路由的 `基本資訊` 中標明入口類型，在 `請求內容`、`回應內容` 中呈現契約；不要在 `基本資訊` 加 `源碼`、`源碼依據` 或來源依據列，也不要輸出獨立的 `Shared EntityApiImpl Contract`、`Unit API Bindings` 或 `Exported Routes` 這類頂層分組。
- `@Api.isFullPowers=true` 表示開發者自行解析 `request` 並使用 `response` 回應，此時 `@Api.isTokenRequired` 不再適用，不要依 token metadata 自動補 `Authorization` 標頭。
- Token 需求以處理器程式碼優先：若 handler 呼叫 `ApiContext.getTokenId()` / `ac.getTokenId()`，即使 `@Api(isTokenRequired=false)`，報告仍會標記 `是否需要 Token=true` 並補 `Authorization` 標頭，因為程式碼實際需要呼叫者 token。
- `TsUnit` metadata 中的 `FApiEnabled`、`FApiClassName` 與 Java class binding。
- SQL 初始化基線以每個 module project 自己的 `src/main/resources/QS-MODULE/data/sql/default/init.xml` 為準，互不影響。若某個 SQL 目錄有 `init.sql` 但沒有 `init.xml`，視為該 module 的 `init.sql` 已包含全部 SQL，只掃描 `init.sql`；若同時有 `init.xml`，讀取該檔 `<version>` 作為該 module 的初始化基線，`init.sql` 視為已包含該版本與更早版本的增量 SQL，因此只額外掃描檔名版本號高於該 module 基線的 `.sql`。
- 會先掃描內建 QS base `assets/templates/api-discovery/sql/` 目錄下全部 `.sql` 作為精簡產品 metadata，再疊加各 module 自己的 SQL metadata；該模板 SQL 以 `TsUnit` 為主，並可保留 API discovery 需要的少量欄位 metadata。若應用 API 類繼承 QS 產品 API 類，例如 ECP `UserApiImpl` 繼承 `com.jeedsoft.quicksilver.user.api.impl.UserApiImpl`，就用父類 `FApiClassName` 綁定到 `Qs.User`，不要求 ECP SQL 內另有 `Qs.User`。
- 若 SQL metadata、模板 SQL、可解析父類源碼都無法確認 unit，會優先用 `extends` 父類 FQCN 的路徑推斷 unit，再退回目前子類；`com.jeedsoft.quicksilver...` 推為產品前綴 `Qs`，其他路徑會略過 `com.xxx`、`org.xxx`、`net.xxx`、`cn.xxx` 這類 domain/organization 前綴，取第二個點後的段作為產品前綴並首字母大寫。例如 `com.jeedsoft.quicksilver.user.api.impl.UserApiImpl` 推為 `Qs.User` / `qs/user`，`com.chainsea.abc.order.OrderApiImpl` 推為 `Abc.Order` / `abc/order`，`org.foo.mes.order.OrderApiImpl` 推為 `Mes.Order` / `mes/order`。
- OpenAPI 路徑前綴，優先從 Home 類別的 `UNIT_ID` 反查 SQL 中 `TsUnit.FCode`，轉成小寫後將 `.` 換成 `_`，再把第一個 `_` 換成 `/`；如果這條路徑推不出來，再 fallback 到 Home 類別的 `CACHE_REGION`。例如 `Qs.Attachment` -> `qs_attachment` -> `openapi/qs/attachment/...`。
- `JsonUtil`、`JSONObject`、`HttpServletRequest`、`ApiContext` 等請求欄位讀取方式。
- 上傳 API 若處理器使用 `ApiContext.getFileItem()` 或 `ApiContext.getFileItems()`，即使 `@Api.input` 沒有宣告檔案，也要輸出為 `multipart/form-data`。前端調用說明使用 `FormData`：普通參數通常放入 `args` JSON 字串，例如 `formData.append("args", JSON.stringify({life: "temp"}))`，也可直接 append；檔案欄位名如 `file1`、`file2` 依 QS 上傳解析約定。`getFileItem()` 讀第一個上傳檔案，`getFileItems()` 讀檔案列表。

輸出文件是給前端開發者與 AI 使用的 API 調用參考，並優先保證 AI 能快速識別全部 API：先用醒目的 `# 報告摘要`，摘要屬性使用繁體中文，例如 `專案根目錄`、`掃描模組`、`API 總數`、`格式`。`專案根目錄` 只輸出邏輯專案名，不輸出本機絕對路徑；`格式` 使用 `路徑優先精簡 API 參考`。再寫 `# 完整 URL 拼接`，URL 拼接說明要保留為多行 Markdown，不壓成單行長句。接著先寫 `# Token API` 放 token 操作 API，再寫 `# 一般 API` 放其他 API，每個 API 只出現一次。每個 API 以 HTTP 方法加路徑作為醒目區塊標題，例如 ``## `POST openapi/qs/user/token/apply` `` 或 ``## `GET openapi/qs/file/download/{path}` ``，相鄰 API 區塊用 `---` 分隔。API 說明優先從最終 API path 推斷：先識別 token/upload/download/transfer/status/login/logout/password/import/export 等動作詞，再用小型領域詞庫翻譯必要業務對象，最後套用自然繁中動作模板；互動式分析時，如果本地詞庫、程式碼與 metadata 都無法確認未知業務詞，可以联网查詢公開技術/業務含義，保守採用確認後的譯法，並優先把可重用譯法沉澱回詞庫或腳本規則；處理器行為、`@Api.value` / `@Api.path`、單元名稱、返回類型、請求/回應組裝方式作為輔助證據。若無法從路徑或 metadata 推出精確業務用途，兜底翻譯目前 `@Api` handler 方法名，例如 `updateMessage` -> `更新消息。`、`agentIsWorkTime` -> `判斷客服是否工作時間。`；不得輸出 `處理downloadfax` 這類未翻譯或 camelCase 拼接描述。非實體 API 不使用單元名稱硬套業務對象；說明是不加標籤的短段落，放在 API 標題下面、`基本資訊` 前面，且每行以兩個全形空格縮排。每個 API 區塊內依序放 `基本資訊`、`路徑參數`、`請求參數`、`請求標頭`、`請求內容`、`回應內容` 等非空調用資訊，且請求/回應細節必須留在該 API 區塊內，不放到需要跨章節查找的共用目錄。`基本資訊` 只放調用與識別必要元資料，包含 `HTTP 方法`，不輸出 `源碼`、`源碼依據` 或來源依據列；來源依據只用於內部確認或欄位表的 `來源` 欄。欄位表來源值使用繁體中文，程式碼確認的欄位用 `處理器程式碼`，只由註解補出的欄位用 `API 註解`，混合來源用 `處理器程式碼 / API 註解`，不要直接輸出 `@Api.input` 或 `@Api.output`。除非使用者明確要求稽核/目錄式報表，不輸出 `Scope`、`Summary`、`Unit API Bindings`、`Exported Routes` 這類大型分組章節。

## 參考文件

- `references/create-qs-project.md`：QS 專案建立流程、目錄規則、模板渲染與 Gradle 設定。
- `references/unit.md`：單元新增、修改、刪除、SQL 位置、文字資源 SQL。
- `references/unit-core.md`：業務表與 `TsUnit` metadata。
- `references/unit-field.md`：`TsField` 與欄位控制規則。
- `references/unit-page-tool.md`：`TsPage`、`TsToolItem`、`TsToolSubItem`。
- `references/unit-form-list-query.md`：`TsForm`、`TsList`、`TsQuerySchema`。
- `references/unit-privilege-menu.md`：`TsPrivilege` 與 `TsMenu`。
- `references/unit-init.md`：QS 精簡 base metadata 搜尋索引。
- `references/unit-system-tables.md`：字典、選單、權限、角色等常用 QS 系統表欄位參考。
- `references/unit-icons.md`：QS 圖示路徑與版本差異。
- `references/api-discovery.md`：QS module API 掃描、路徑推導、請求/回應欄位分析與 Markdown 報告格式。

## 模板資源

- `assets/templates/create-qs-project/parent/`：父專案根目錄模板。
- `assets/templates/create-qs-project/build/`：`<project-name>-build` 模板。
- `assets/templates/create-qs-project/run/`：`<project-name>-run` 模板。
- `assets/templates/create-qs-project/lib/`：`lib` 子專案模板。
- `assets/templates/create-qs-project/module/`：`module` 子專案模板。
- `assets/templates/unit/java/`：單元 Java 層模板。
- `assets/templates/unit/sql/`：單元 SQL metadata 模板。
- `assets/templates/api-discovery/java/`：API annotation、繼承 API 與 API result contract 參考。

## 維護注意事項

- `SKILL.md` 只保留觸發後最常用的高階流程，詳細規則放在 `references/`。
- 更新單元生成邏輯時，優先同步 `references/unit.md` 與相關 focused reference。
- 更新模板時，確認 placeholder 能完整渲染，不要留下 `<placeholder>` 或 `{Placeholder}`。
- 修改 `TsTextResource` 規則時，保持新增、修改、刪除三種 SQL 行為一致。
- 更新 API 掃描邏輯時，優先同步 `references/api-discovery.md` 與 `assets/templates/api-discovery/java/` contract 參考。
