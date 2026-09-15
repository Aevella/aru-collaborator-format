# Aru Collaborator Package v1

Status: public interchange contract, version 1.

`aru-collaborator` is a data-only format for bringing an assistant identity and
its shared history into Aru as a collaborator. It is intentionally smaller than
an Aru native backup: exporters do not need to know Aru's SQLite schema, and a
collaborator package never restores app settings, credentials, executable
tools, or runtime state.

中文概括：普通聊天记录只需生成一份符合下方结构的 JSON；有头像、背景或附件时，把同一份
JSON 命名为根目录 `manifest.json`，连同 `assets/` 一起压成 `.arucollab`。Aru 会先展示
预览，用户确认后才把它追加为原生协作者、对话、消息、记忆与资产。

## Containers

The same logical document has two containers:

- A UTF-8 `.json` file for text-only imports. Its root object is the v1
  manifest described below. An `assets` array is not useful in this container
  because no binaries accompany it.
- A ZIP file whose filename ends in `.arucollab`. It contains exactly one root
  `manifest.json` plus optional binary files below `assets/`.

The package extension is a product affordance, not an alternative schema.
Renaming an arbitrary ZIP to `.arucollab` does not make it valid.

## Smallest valid document

```json
{
  "format": "aru-collaborator",
  "version": 1,
  "source": {
    "namespace": "com.example.chat",
    "displayName": "Example Chat"
  },
  "collaborator": {
    "id": "assistant-1",
    "displayName": "Little Light"
  },
  "conversations": [
    {
      "id": "conversation-1",
      "title": "First meeting",
      "messages": [
        {
          "id": "message-1",
          "role": "user",
          "content": "Hello.",
          "createdAt": "2025-08-20T21:14:00+08:00"
        },
        {
          "id": "message-2",
          "role": "assistant",
          "content": "I'm here.",
          "createdAt": "2025-08-20T21:14:03+08:00"
        }
      ]
    }
  ]
}
```

The authoritative machine-readable definition is
[`schemas/aru-collaborator-v1.schema.json`](schemas/aru-collaborator-v1.schema.json).
Ready-to-run samples live under [`examples/aru-collaborator`](examples/aru-collaborator).

## Identity and incremental reimport

`source.namespace` identifies the exporter or source family. Use a stable,
collision-resistant value such as a reverse-DNS name and do not change it
between exports. `collaborator.id`, conversation IDs, message IDs, memory IDs,
asset IDs, and attachment IDs are source-owned stable identities.

Aru combines the namespace, object kind, parent identity where needed, and
source ID to form its import identity. Reimport is one-way and additive:

- an already imported source object is not duplicated;
- a new message in an existing source conversation is appended;
- deleting something from a later export does not delete it from Aru;
- conversations or memories created only in Aru are not overwritten.

Version 1 treats an existing source ID as immutable. An exporter must not reuse
one ID for unrelated content or silently rewrite an earlier message under that
ID. If a package nevertheless repeats an ID in one owner scope, Aru keeps the
first usable item, skips later conflicts, and reports them. Revision exchange
can be introduced in a later format version without changing v1's meaning.

Emit one package per collaborator. A large history may be split into several
packages that keep the same `source.namespace` and `collaborator.id`; additive
reimport reunites their conversations and messages without duplicating earlier
source objects.

## Collaborator fields

`collaborator.id` and `collaborator.displayName` are required. The remaining
fields are optional:

- `systemPrompt` is an explicit, durable identity instruction. It becomes the
  collaborator's prompt after the user confirms the import. Do not infer it
  from ordinary conversation text.
- `messageTemplate` is the source's explicit per-message template. Do not put
  transient system events or tool wrappers here.
- `memories` contains explicit long-term memory records from the source. Chat
  messages are not memories merely because they are old.
- `presentation` may reference packaged assistant avatar, user avatar, and
  background assets. Missing or invalid assets degrade presentation without
  discarding healthy conversations.
- `createdAt` and `updatedAt` use RFC 3339 timestamps with an explicit UTC
  offset or `Z`.

If the source contains only transcripts, omit `systemPrompt` and `memories`.
Aru may later offer an editable calibration proposal, but derived personality
text is not imported source truth.

## Conversations and messages

Conversation and message array order is the authoritative source order.
Timestamps are strongly recommended because they preserve real-world temporal
meaning; when present, they must be RFC 3339 with a timezone.

Version 1 admits only `user` and `assistant` message roles. This is deliberate:
foreign `system` and `tool` records do not receive instruction or execution
authority by being imported. Aru skips and reports those records while keeping
healthy sibling messages. A stable source-owned identity prompt belongs in
`collaborator.systemPrompt`; tool traces and other unsupported records belong
under a namespaced `extensions` payload or remain in the source export.

`content` is Markdown-capable plain text and is never HTML or script execution.
`reasoning` may be supplied only when the source explicitly exported readable
reasoning; an exporter must not synthesize or guess it. A message must contain
at least one of `content`, `reasoning`, or `attachments`.

## Assets and attachments

Binary assets exist only in the `.arucollab` ZIP container. Each manifest asset
declares a stable ID, relative `assets/` path, media type, and lowercase or
uppercase SHA-256 digest. Message attachments and collaborator presentation
refer to that asset ID.

Paths must remain below `assets/`; absolute paths, backslashes, empty segments,
`.` and `..` segments are invalid. Aru verifies every digest before publishing
the asset. A missing, unsafe, or mismatched asset is skipped and reported while
otherwise valid text remains importable.

## Extensions and forward compatibility

Exporters may place source-specific, non-core data in the top-level
`extensions` object under a namespace they own. Aru v1 does not activate these
values and reports that they were not imported. Unknown core fields make an
export non-conforming to the producer schema; Aru's recovery-oriented importer
ignores and reports them instead of discarding otherwise healthy history.
Future portable behavior belongs in a new schema version or a specified
extension promoted through review.

## Recovery policy

The schema and validator are deliberately strict for producers so mistakes are
caught before distribution. Aru's importer is deliberately more forgiving for
user-owned history. It rejects the whole input only when it cannot establish a
safe root: unreadable JSON/ZIP, a wrong or unsupported format version, a missing
stable source namespace, or a missing collaborator identity. After that root is
known, recovery is item-scoped:

- unsupported message roles, empty child records, and later duplicate IDs are
  skipped and reported;
- unknown fields and invalid optional timestamps are ignored and reported;
- unsafe, missing, unreadable, or hash-mismatched assets are skipped together
  with only the references that need them;
- healthy collaborators, memories, conversations, messages, and text continue
  into preview and can be imported after confirmation.

This asymmetry is intentional: producers get a precise conformance target,
while one damaged item does not take a user's entire archive hostage.

## Security and authority

An Aru collaborator package is data, never code. It cannot contain or activate:

- provider API keys or account cookies;
- MCP servers, HTTP headers, or connection credentials;
- JavaScript, executable HTML, CSS recipes, plugins, or skills;
- scheduled/proactive actions or tool calls to replay;
- app settings, native backup rows, or database files.

Import follows preview, explicit confirmation, canonical publication, and an
import report. A root-level failure performs no live writes; item-level damage
appears in preview and is omitted from publication. Importing a package does
not select the new collaborator or change unrelated collaborators.

## Producer workflow

The repository ships a dependency-free helper:

```bash
python3 scripts/aru-collaborator/aru_collaborator.py validate path/to/manifest.json
python3 scripts/aru-collaborator/aru_collaborator.py pack path/to/manifest.json output.arucollab
python3 scripts/aru-collaborator/aru_collaborator.py validate output.arucollab
```

`pack` reads asset paths relative to the manifest directory, verifies their
digests, and writes a deterministic package layout. The JSON Schema remains the
normative field contract; the helper provides friendlier local diagnostics.

## Conformance

An importer claiming v1 support must prove at least:

1. minimal text-only JSON import;
2. `.arucollab` ZIP import with verified attachments and presentation assets;
3. stable additive reimport without duplicates or reverse deletion;
4. rejection of unsupported root versions, plus item-scoped recovery around
   duplicate child IDs and unsupported roles;
5. containment of unsafe asset paths and degradation of missing/corrupt assets;
6. no instruction authority for foreign system/tool traces.
