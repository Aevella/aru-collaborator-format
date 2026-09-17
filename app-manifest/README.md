# 将网页应用接入 Aru

`aru.app.v1` 是应用描述文件格式。它声明应用名称、发布者、网页入口，以及可选的 MCP 或节点插件能力。

## 接入步骤

1. 下载[网页示例](examples/aru-app/web-page.aruapp.json)，修改应用 `id`、名称、发布者、`runtime.origin`、数据目的地和 `launchPath`。
2. 在 Aru 的「设置 → 应用与连接 → 从描述文件安装」中选择 JSON，检查预览并确认安装。
3. 在应用详情打开「显示在对话 Apps 中」，将已就绪的网页入口加入对话启动器。
4. 在 Aru 中打开页面，检查页面加载和图标显示。

图标来自原网页 HTML。页面加载完成时需存在 `<link rel="icon" href="...">` 声明，图片使用可直接下载的 HTTP(S) 地址，建议 PNG 或 JPEG。详细的读取顺序、缓存和回退行为见[图标出现的条件](ARU-APP-MANIFEST.md#72-图标出现的条件)。

示例使用 `example.com` 保留域名，安装前需替换为自己的服务地址。

## 规格与工具

- [描述文件完整规格](ARU-APP-MANIFEST.md)
- [JSON Schema](schemas/aru-app-v1.schema.json)
- [网页入口示例](examples/aru-app/web-page.aruapp.json)
- [网页与 MCP 示例](examples/aru-app/web-page-with-mcp.aruapp.json)

从仓库根目录运行 Schema 回归检查，需要 [uv](https://docs.astral.sh/uv/)：

```sh
uv run app-manifest/scripts/aru-app/test_manifest_schema.py
```

这条命令验证仓库示例及校验规则的反例，不连接示例服务。自编文件可用支持 JSON Schema 2020-12 的工具加载本目录 Schema；最终导入预览还会检查 facet ID 唯一性和 URL 解析。

文档与工具的发布独立于 Aru 客户端分发。协作者数据转换的 v1.0.0 下载包保持原有内容，不包含本目录。

[返回仓库首页](../README.md)
