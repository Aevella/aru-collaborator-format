# Aru App 描述文件 v1（`aru.app.v1`）

状态：开发者规格，版本 1，按当前源码行为编写。

描述文件是一份 UTF-8 JSON，描述应用身份、发布者、网页入口及其他能力。
用户在 设置 → 应用与连接 中选择描述文件或粘贴描述文件链接。Aru 读取并展示预览，确认后写入安装并进入配置详情。

本轮新增链接安装、网页登录提示和桌面入口；客户端分发状态独立于本规格发布。

- 机器可读定义：[`schemas/aru-app-v1.schema.json`](schemas/aru-app-v1.schema.json)
- 示例：[`examples/aru-app`](examples/aru-app)

本规格对应 Aru 源码提交 `9ed0586b5`。链接安装、网页登录提示和桌面入口已完成源码与本机验证，尚未随客户端分发。
协议扩展时同步更新规格、Schema 和示例。返回[仓库首页](../README.md)。

## 1. 最小可用文件

一个只有网页入口的应用。以下名称和地址均为演示占位，不对应真实服务：

```json
{
  "protocol": "aru.app.v1",
  "id": "com.example.reading-room",
  "name": "示例网页应用",
  "version": "1.0.0",
  "publisher": { "name": "Example Studio" },
  "runtime": {
    "kind": "external-endpoint",
    "origin": "https://reading.example.com"
  },
  "requestedPermissions": [],
  "dataDestinations": ["https://reading.example.com"],
  "facets": [
    {
      "id": "main",
      "kind": "presentation",
      "title": "示例网页应用",
      "owner": { "kind": "external-connector", "id": "com.example.reading-room.page" },
      "launchPath": "/"
    }
  ]
}
```

建议文件名用 `<名字>.aruapp.json`。导入器只接受 `.json` 类型、一次一个文件，没有额外大小限制。

## 2. 解析规则

- 导入器忽略未知字段，保存时仅保留当前模型定义的字段。Schema 会报告未知字段，便于发现拼写错误。
- 标为“必填”的键需要出现；没有内容的数组写为 `[]`。
- 枚举值区分大小写，未定义的值会导致解析失败。
- 展示名、版本、发布者名、facet 标识和连接描述等字段会去除首尾空白；顶层 `id` 和 `protocol` 按原值校验。
  可选文本清理后为空时按未填写处理；权限、数据目的地和插件协议列表会去除空项和重复项。
- 解析或校验失败时，预览页显示错误，不写入安装数据。

Schema 用于编写阶段的结构检查，不等同于完整导入校验。facet `id` 的唯一性和 URL 的最终解析
由 `AppInstallationStore.decodeManifest` 校验；通过 Schema 后仍需在 Aru 中检查导入预览。
Schema 不执行字符串清理，编写文件时使用清理后的字段值。

仓库中的 Schema 回归检查：`uv run scripts/aru-app/test_manifest_schema.py`。

## 3. 顶层字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `protocol` | 是 | 固定为 `"aru.app.v1"`。 |
| `id` | 是 | 稳定的反向域名 id，匹配 `^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)+$`，例如 `com.example.app`。同一 id 再次导入会更新已有安装（见第 8 节）；同一应用的后续版本沿用此 id。 |
| `name` | 是 | 应用展示名，非空。启动器首字图标取它的第一个字符。 |
| `version` | 是 | 非空字符串，Aru 不解析格式。 |
| `publisher.name` | 是 | 发布者名，非空。目前没有签名验证，界面始终标为“发布者自称”。 |
| `runtime` | 是 | 运行位置，见第 4 节。 |
| `requestedPermissions` | 是 | 自由文本列表，原样展示给用户（“Manifest 自述”），不参与运行时权限控制。 |
| `dataDestinations` | 是 | 自由文本列表，说明数据会发往哪里。预览页会再合并各 facet 的实际端点一起展示。 |
| `facets` | 是 | 能力列表，可以为空，见第 5 节。 |

## 4. `runtime`

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `kind` | 是 | `external-endpoint`、`paired-node` 或 `local-device`。 |
| `origin` | `external-endpoint` 时必填 | 只能是 `http(s)://host[:port]`，路径只能为空或 `/`，不能带用户名密码、query 或 fragment。 |

目前能打开网页入口的只有 `external-endpoint`。`http` 可以用，但预览页会警告明文传输。

## 5. `facets`

每个 facet 是应用的一项能力。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `id` | 是 | 文件内唯一，不能含空白。更新版本时保持不变，用户的挂载、图标缓存和登录绑定都挂在它上面。 |
| `kind` | 是 | `presentation`、`model-capability`、`background-work`、`provider-role`、`artifact`。 |
| `title` | 否 | 页面标题；不填时用 `name`。与 `name` 不同时，启动器在图标下多显示一行。 |
| `owner.kind` | 是 | `external-connector`、`mcp-server`、`node-plugin`、`app-surface`。 |
| `owner.id` | 是 | 非空字符串，是 owner 的声明名，不用于匹配本机已有的服务。 |
| `launchPath` | 见下 | 网页入口路径。 |
| `destinationId` | 否 | 同一页面的多入口区分键，只参与已打开会话的去重，**不改变打开的 URL**。 |
| `setup` | 否 | 连接说明，见第 6 节。 |
| `webLogin` | 否 | 网页登录方式提示，见第 6.3 节；不包含凭据值。 |

### 5.1 当前支持的能力组合

| facet `kind` | `owner.kind` | 需要 | 当前行为 |
| --- | --- | --- | --- |
| `presentation` | `external-connector` | `runtime.kind = external-endpoint` 且填写 `launchPath` | 在 Aru 内置浏览器里打开 |
| `model-capability` | `mcp-server` | `setup.kind = mcp-server` | 连接为 MCP 工具，握手成功才算就绪 |
| `model-capability` / `background-work` | `node-plugin` | `setup.kind = node-plugin` | 用户选择自有节点并确认权限后安装插件 |
| `presentation` | `app-surface` | — | 预览会显示“应用自带页面”，但安装后不可用 |
| `provider-role`、`artifact` | 任意 | — | 只能声明，显示为不可用 |
| `mcp-server` / `node-plugin` owner | — | 缺少 `setup` | 显示“描述文件没有说明如何连接” |

### 5.2 `launchPath` 与打开的地址

- 只允许出现在 `presentation` + `external-connector` + `external-endpoint` 的 facet 上。
- 必须以 `/` 开头，不能以 `//` 开头，不能含 `\`、query 或 fragment。
- 打开的地址 = `runtime.origin` + `launchPath`，例如 `https://reading.example.com` + `/app` →
  `https://reading.example.com/app`。
- **没有默认值。** 不写 `launchPath` 的网页 facet 会显示“页面 owner 尚未接入”，无法打开。
  首页也要显式写 `"launchPath": "/"`。

## 6. `setup`

`setup` 描述连接参数和凭据类型，凭据值由用户在对应连接设置中配置。`kind` 是区分键，内容放在同名的兄弟键里。

### 6.1 MCP 服务

只能用于 `kind: model-capability` + `owner.kind: mcp-server`。

```json
"setup": {
  "kind": "mcp-server",
  "mcpServer": {
    "endpoint": "https://garden.example.com/mcp",
    "transport": "streamable-http",
    "credentialRequirement": "configured-headers",
    "suggestedHandle": "garden",
    "summary": "搜索帖子、读取楼层、发布回复"
  }
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `endpoint` | 是 | `http(s)` URL，不能带用户名密码、query 或 fragment。 |
| `transport` | 是 | `streamable-http` 或 `sse`。 |
| `credentialRequirement` | 是 | `none`、`configured-headers`、`configured-query-parameters`、`oauth`。只说明需要哪类凭据，凭据由用户在 Aru 里填写。 |
| `suggestedHandle` | 否 | 建议的工具前缀。 |
| `summary` | 否 | 展示用简介。 |

如果本机已经有端点相同的 MCP 服务，Aru 直接认领它；否则安装后由用户点“连接”再创建。
创建出来的服务默认每次调用都要确认。

### 6.2 自有节点插件

只能用于 `kind: model-capability` 或 `background-work`，且 `owner.kind: node-plugin`。
`nodePlugin` 的十个键全部必填：

| 字段 | 说明 |
| --- | --- |
| `pluginId` | 匹配 `^[a-z0-9][a-z0-9._-]{0,127}$`。 |
| `displayName`、`version`、`publisher`、`source` | 非空字符串。 |
| `packageMode` | `oci` 或 `source-node`。 |
| `image` | 字符串。 |
| `protocols` | 字符串数组。 |
| `requestedPermissions` | `{ "network": "none" \| "outbound", "persistentVolume": bool, "secretHandles": [], "hostPaths": [...], "deviceAccess": bool }`，五个键都要写；`secretHandles` 必须为空。 |
| `resources` | 对象必须出现，内部 `memoryMiB`、`cpuMillis`、`pids` 都是可选整数。 |

这里的权限只是请求，节点返回的授权回执和用户确认才是实际授予。

### 6.3 网页登录提示

有网页入口的 `presentation` + `external-connector` facet 可声明：

```json
"webLogin": { "method": "queryToken", "parameterName": "access_token" }
```

`method` 支持 `httpBasic`、`queryToken`、`persistentQueryToken`。后两种需要非空、无空白的
`parameterName`；HTTP Basic 不使用该字段。省略 `webLogin` 时，网页可以使用自己的登录表单。
安装后在“网页登录方式”中输入凭据；已有安装的配置优先于描述文件提示，更新文件不会替换用户凭据。
网页与 MCP 采用各自认证流程，只有网页登录成功不能证明 MCP 已授权。

### 6.4 多个 MCP

一份描述文件可以包含多个 `model-capability` + `mcp-server` facet，每项使用独立的 facet id、
endpoint 和凭据要求。也可以完全不包含网页；见 [MCP 工具组示例](examples/aru-app/mcp-bundle.aruapp.json)。

安装后选择“连接或检查 MCP”，按顺序推进待连接和待检查的服务。每项连接结果独立保留；需要凭据或 OAuth
时进入该项设置完成授权，返回应用详情继续检查。取消批处理停止继续推进后续项；已开始的连接通过该项的
取消操作处理。重试使用现有服务关系，不重复安装已经连接的服务。

## 7. 在对话和桌面显示

### 7.1 出现在对话 Apps 启动器

安装预览可选择“显示在对话 Apps 中”；也可以安装后，在 设置 → 应用与连接 → 应用详情 里打开
“显示在对话 Apps 中”。这个开关只对已就绪的网页 facet 出现，打开后在所有对话里显示。
当前版本的挂载位置由用户在 Aru 中设置。

启动器里的“管理应用”会跳到设置页，启动器本身不能增删应用。

安装预览和应用详情也可以选择协作者桌面。桌面的“已安装应用”区域提供添加、打开和移除入口。
桌面位置按协作者隔离；移除入口不卸载应用，卸载则移除该应用的全部入口。网页复用同一安装的登录存储。

### 7.2 图标出现的条件

图标来自原网页的 HTML。应用安装后，在 Aru 内打开页面；页面加载完成时存在可用的图标声明，
且图标图片能成功下载并解码，启动器和 Dock 就可以显示该图标。

网页作者可在 `<head>` 中添加：

```html
<head>
  <link rel="icon" type="image/png" href="/icons/icon-180.png">
  <link rel="apple-touch-icon" href="/icons/icon-180.png">
</head>
```

网页需要满足以下条件：

- 图标声明在页面加载完成时已经存在。写在初始 HTML 中即可满足；脚本插入的声明也需要在读取前完成。
  单页应用之后切换路由不会单独触发图标读取。
- 图标地址为 HTTP(S)。相对路径会由浏览器解析为绝对地址；用于持久缓存的地址还需不含用户名和密码。
- 图片可直接下载，不依赖网页的登录 Cookie 或额外认证请求头。
- 建议使用 PNG 或 JPEG 正方形图片，例如 180 × 180 像素；180px 不是校验下限。
  当前图片组件对 SVG 和 ICO 的解码支持不作保证。

Aru 每次收到页面加载完成事件时，从主页面的 `<link rel>` 中选择图标：

1. 优先选择第一个 `rel` 空白分隔词中包含 `icon` 的声明，例如 `icon` 或 `shortcut icon`。
2. 没有上述声明时，选择第一个 `rel` 包含 `apple-touch-icon` 的声明。
3. 对选中的地址执行 HTTP(S) 校验；未通过校验时，本次不取得图标，不继续尝试后面的声明。

如果页面提供多种格式，将 PNG 或 JPEG 声明放在第一个 `rel="icon"` 位置。
当前实现不按图片尺寸或格式择优选择，也不会在第一张图片下载失败后尝试下一张。

通过缓存校验的图标 URL 按安装和 facet 保存。后续读取到合格的新地址时更新缓存；本次未取得可缓存地址时保留旧缓存。
启动器和 Dock 优先使用当前页面图标，其次使用缓存。图片下载或解码失败时，启动器显示 `name`
的首字图标，底色由应用 `id` 决定；Dock 显示应用网格符号。

图标未显示时，依次检查：是否在 Aru 中打开过页面、加载完成时的首个图标声明、解析后的图片地址、
以及图片能否独立下载和解码。`aru.app.v1` 的图标配置位于网页 HTML，描述文件中的 `icon` 字段不参与读取。

### 7.3 名称

启动器和 Dock 显示描述文件的 `name`。Dock 的第二行是会话标题，页面加载后可能被页面 `<title>` 替换。
页面图标和标题只是装饰，不会改变应用身份，也不证明发布者。

## 8. 更新、重新安装与卸载

- **同一 `id` 再次导入 = 更新。** 预览页会提示“这个应用已经安装过”。确认后替换描述文件，保留：
  - 原来的安装记录；
  - 对话中的显示开关；
  - 已缓存的图标；
  - 网页登录状态。
- **facet 被删掉或改了 id**：它的显示开关失效，依赖它的连接会被释放。
- **`setup` 的 endpoint 或 pluginId 变了**：对应的连接会被释放，需要重新连接。
- **`runtime.origin` 或 `launchPath` 变了**：已打开的旧页面会话不再可用，重新打开即可。
- **卸载**：移除安装和对话中的显示开关，不删除它认领过的 MCP 服务或节点插件。
  之后用同一 `id` 重新安装，需要重新打开“显示在对话 Apps 中”。

## 9. 登录与凭据

描述文件记录连接配置和凭据类型；凭据值由对应的登录或连接设置管理：

- 网页应用的登录方式在 Aru 设置里配置，每个安装有独立的网页登录存储。可选方式有：
  - 网页内自己登录；
  - HTTP Basic；
  - 一次性 URL token；
  - 持续 URL token。
- 从描述文件安装后，应用详情的“网页登录方式”也可配置 HTTP Basic 或 URL token。
  每个网页入口分别配置；网页自身登录直接在“打开”后的页面完成。
- MCP 凭据由用户在 MCP 服务设置里填写，描述文件只声明 `credentialRequirement`。
- 节点插件不能通过描述文件请求注入密钥（`secretHandles` 必须为空）。

## 10. 与“通过网址连接”的关系

在设置里直接输入网址连接网页应用时，Aru 会在内部生成一份同样的 `aru.app.v1` 描述文件：

- `id`：`external.<倒序域名>.page.<页面 URL 的哈希>`；
- `name`：用户输入的名字；
- `version`：`"1"`；
- `publisher.name`：小写主机名；
- `runtime`：`external-endpoint`，`origin` 取该网址的协议、主机和端口；
- `dataDestinations`：只含这个 origin；
- `facets`：一个 `id: "main"` 的 `presentation` + `external-connector`，`launchPath` 取网址路径（为空时用 `/`）。

自己写描述文件和通过网址连接走的是同一套安装、显示和图标流程。

## 11. 当前实现范围

- 图标通过网页 HTML 声明，读取条件见第 7.2 节。
- 挂载位置在 Aru 中设置，支持对话 Apps 和协作者桌面；网页登录配置位于应用详情。
- `app-surface`、`provider-role`、`artifact` 还没有运行时。
- 发布者只是自称，没有签名或受信来源验证。
- `requestedPermissions` 与 `dataDestinations` 是自述文本，Aru 不据此强制任何限制。

同一协议版本的兼容扩展保留既有文件的解析和行为。需要改变既有字段语义或必填要求时，
另行定义协议版本及迁移方案。

## 12. 安装链接

网站可提供指向 `aru://install-app?url=<编码后的描述文件URL>` 的“安装到 Aru”按钮。
`url` 是 HTTP(S) 描述文件地址，使用 URL 查询参数编码。例：

```html
<a href="aru://install-app?url=https%3A%2F%2Fexample.com%2Fapp.aruapp.json">安装到 Aru</a>
```

点击后 Aru 获取文件并显示安装预览，不自动提交安装或授权。未安装 Aru 时，网站应同时提供
描述文件下载和客户端获取说明。描述文件仍可通过文件选择器导入。
