# Aru 接入与数据互操作

本仓库提供 Aru 的公开格式规格、使用说明、Schema、示例和校验工具。

| 目标 | 入口 | 格式 |
| --- | --- | --- |
| 将原始聊天导出转换为 Aru 可导入的数据 | [数据转换与导入指南](#把聊天记录带进-aru) · [AI 转换说明](CONVERT-WITH-AI.md) | `aru-collaborator` v1 |
| 将网页和连接能力接入 Aru 的应用入口 | [应用接入指南](app-manifest/README.md) · [描述文件规格](app-manifest/ARU-APP-MANIFEST.md) | `aru.app.v1` |

两套格式独立演进：协作者交换文件用于数据迁入，应用描述文件用于安装应用入口和声明连接能力。
本仓库保留原有名称和文件路径，既有转换教程、下载链接和 v1.0.0 发布保持有效。

## 把聊天记录带进 Aru

**Aru 协作者交换格式 v1**，用来迁入协作者、聊天记录、明确保存的记忆，以及头像和附件。

将原始聊天记录转换为这套格式，就可以在 Aru 中预览并迁入。纯文字使用 JSON；带文件时使用 `.arucollab` 包。

[下载入门包](https://github.com/Aevella/aru-collaborator-format/releases/latest/download/Aru-import-starter-kit.zip) · [交给 AI 的转换说明](CONVERT-WITH-AI.md) · [格式规范](ARU-COLLABORATOR-FORMAT.md) · [JSON Schema](schemas/aru-collaborator-v1.schema.json)

## 我应该怎么用？

1. **先看 Aru 是否已经支持原平台导出。** 支持的话，直接导入原文件即可。统一格式用于尚未支持的来源或自己制作的转换工具。
2. **准备原始聊天导出。** 保留原文件；需要 AI 转换时，将原文件和本仓库的转换说明、规范一起交给它。只需提供待转换的原始聊天导出。使用在线 AI 意味着它会接收到你选择提供的聊天内容。
3. **拿到转换结果并校验。** 纯文字保存为完整的 UTF-8 `.json` 文件。让能运行 Python 的转换工具执行本仓库的校验命令；校验通过仍需检查消息数量和内容是否齐全。
4. **在 Aru 中预览再导入。** 进入设置的「备份与恢复」区域，选择 **「迁入旧数据」**，选中 JSON 或 `.arucollab` 文件。确认协作者、对话和消息预览，留意跳过项，再确认导入。统一格式应走迁入入口。

导入支持已包含于 Aru 0.3（202609160540）的上传源码；TestFlight 的处理、审核与个人可安装状态由 Apple 渠道决定，本仓库发布不代表新手机包已经对所有人可用。

## 先试一个小样例

[下载纯文字示例](https://github.com/Aevella/aru-collaborator-format/releases/latest/download/minimal.json) 会创建一个名为「小灯」的示例协作者，包含两条虚构消息。

[下载带附件示例](https://github.com/Aevella/aru-collaborator-format/releases/latest/download/example.arucollab) 包含一份虚构聊天和文本附件。它用于验证格式，不是用户历史。

## 交给 AI 的简短说法

> 请按我提供的《Aru 协作者交换格式 v1》和转换说明，把这份原始聊天记录转换为可导入文件。保留原文、顺序及来源 ID，仅使用原始导出中明确存在的信息。先报告读到多少段对话和消息，再生成文件并运行校验，最后报告实际输出数量及无法转换的项目。输出 Aru 协作者交换文件。

完整要求见 [CONVERT-WITH-AI.md](CONVERT-WITH-AI.md)。AI 无法读取链接时，把下载包里的说明文件直接附给它。

## 常见问题

**只有文字也要压缩吗？** 不用。一份符合规范的 JSON 就可以。有附件或头像时，根目录为 `manifest.json`，文件放在 `assets/`，用工具打成 `.arucollab`。

**超长记录怎么办？** 可以分包，但同一来源和协作者的身份必须保持一致，消息 ID 保持稳定。让转换工具逐段处理，并核对总数。

**重复导入会怎样？** 相同来源身份的已导入项目不会重复新增；新消息会追加。删掉后续文件里的内容不会反向删除 Aru 中的内容。v1 不用于覆盖改写已经导入的旧消息；修正转换规则后重新生成不同 ID 可能造成重复，先核对身份。

**能迁移什么？** 聊天、来源明确的人设指令和长期记忆、可读推理、头像及附件。只有聊天时，就只迁入聊天内容。工具调用不能通过导入自动执行。

**提示跳过部分内容怎么办？** 查看导入报告，回到原文件定位对应项目再修正。修正时保持来源 ID 稳定。报告问题时提供去除私人内容的最小示例和错误文字，公开 Issues 只需提供可复现问题的脱敏材料。

## 给转换工具开发者

- [v1 规范](ARU-COLLABORATOR-FORMAT.md) 定义字段语义、来源身份和增量导入规则。
- [JSON Schema](schemas/aru-collaborator-v1.schema.json) 是机器可读字段契约。
- [示例目录](examples/aru-collaborator) 提供最小文件和带附件包的源材料。
- [Python 工具](scripts/aru-collaborator/aru_collaborator.py) 仅依赖标准库（Python 3.10+），校验和打包均在本地进行。

```sh
python3 scripts/aru-collaborator/aru_collaborator.py validate examples/aru-collaborator/minimal.json
python3 scripts/aru-collaborator/aru_collaborator.py pack examples/aru-collaborator/rich/manifest.json example.arucollab
python3 scripts/aru-collaborator/aru_collaborator.py validate example.arucollab
```

固定版本请使用 [v1.0.0](https://github.com/Aevella/aru-collaborator-format/tree/v1.0.0)，不要依赖会变化的 main 分支。格式里的 `version` 仍是整数 `1`；v1.0.0 是本套文档与工具的发布版本。

本仓库公开维护数据交换与应用接入规格、示例和工具；Aru 应用实现单独维护。未来 App 内的教程入口还需后续版本接入，目前可直接分享本页。
