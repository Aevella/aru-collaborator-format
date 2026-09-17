# 将网页应用接入 Aru

`aru.app.v1` 是应用描述文件格式。它声明应用名称、发布者、网页入口，以及可选的 MCP 或节点插件能力。

## 接入步骤

1. 根据应用选择[网页示例](examples/aru-app/web-page.aruapp.json)、[网页与 MCP 示例](examples/aru-app/web-page-with-mcp.aruapp.json)或[多个 MCP 示例](examples/aru-app/mcp-bundle.aruapp.json)，修改身份和服务地址。
2. 在 Aru 的「设置 → 应用与连接」选择描述文件，或粘贴 JSON 文件链接，检查预览并确认安装。
3. 安装后进入应用详情：打开网页、配置网页登录、连接 MCP；需要授权的 MCP 可进入各自设置完成登录或填写凭据。
4. 按需放入对话 Apps 或协作者桌面，再检查页面加载和图标显示。

网站可按[安装链接说明](ARU-APP-MANIFEST.md#12-安装链接)提供「安装到 Aru」按钮。`webLogin` 只声明登录方式，凭据由用户在 Aru 中填写。网页和 MCP 的授权分别管理。

以上新流程对应源码 `9ed0586b5`，已通过本机服务和 Simulator 验证，尚未随客户端分发。旧版客户端可继续用文件导入；安装链接、登录配置和桌面入口需等待包含该实现的版本。

图标来自原网页 HTML。页面加载完成时需存在 `<link rel="icon" href="...">` 声明，图片使用可直接下载的 HTTP(S) 地址，建议 PNG 或 JPEG。详细的读取顺序、缓存和回退行为见[图标出现的条件](ARU-APP-MANIFEST.md#72-图标出现的条件)。

示例使用 `example.com` 保留域名，安装前需替换为自己的服务地址。

## 规格与工具

- [描述文件完整规格](ARU-APP-MANIFEST.md)
- [JSON Schema](schemas/aru-app-v1.schema.json)
- [网页入口示例](examples/aru-app/web-page.aruapp.json)
- [网页与 MCP 示例](examples/aru-app/web-page-with-mcp.aruapp.json)
- [多个 MCP 示例](examples/aru-app/mcp-bundle.aruapp.json)

从仓库根目录运行 Schema 回归检查，需要 [uv](https://docs.astral.sh/uv/)：

```sh
uv run app-manifest/scripts/aru-app/test_manifest_schema.py
```

这条命令验证仓库示例及校验规则的反例，不连接示例服务。自编文件可用支持 JSON Schema 2020-12 的工具加载本目录 Schema；最终导入预览还会检查 facet ID 唯一性和 URL 解析。

文档与工具的发布独立于 Aru 客户端分发。协作者数据转换的 v1.0.0 下载包保持原有内容，不包含本目录。

[返回仓库首页](../README.md)
