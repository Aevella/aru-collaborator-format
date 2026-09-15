#!/usr/bin/env python3
"""Validate and pack Aru Collaborator Package v1 files without dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable


FORMAT = "aru-collaborator"
VERSION = 1
NAMESPACE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
TOP_KEYS = {"format", "version", "source", "collaborator", "conversations", "assets", "extensions"}
SOURCE_KEYS = {"namespace", "displayName"}
COLLABORATOR_KEYS = {
    "id", "displayName", "systemPrompt", "messageTemplate", "memories",
    "presentation", "createdAt", "updatedAt",
}
MEMORY_KEYS = {"id", "content", "createdAt", "updatedAt"}
PRESENTATION_KEYS = {
    "assistantAvatarAssetId", "userAvatarAssetId", "backgroundAssetId", "showsAvatars",
}
CONVERSATION_KEYS = {"id", "title", "createdAt", "updatedAt", "messages"}
MESSAGE_KEYS = {"id", "role", "content", "reasoning", "attachments", "createdAt", "updatedAt"}
ATTACHMENT_KEYS = {"id", "assetId", "filename", "createdAt"}
ASSET_KEYS = {"id", "path", "mediaType", "filename", "sha256", "createdAt"}


class ValidationError(Exception):
    pass


def object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=object_without_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(f"{label}: invalid UTF-8 JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{label}: root must be an object")
    return value


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    return value


def require_array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path} must be an array")
    return value


def require_string(value: Any, path: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        suffix = "a non-empty string" if nonempty else "a string"
        raise ValidationError(f"{path} must be {suffix}")
    return value


def reject_unknown(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValidationError(f"{path} has unknown core fields: {', '.join(unknown)}")


def require_timestamp(value: Any, path: str) -> None:
    text = require_string(value, path)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{path} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None:
        raise ValidationError(f"{path} must include a timezone offset or Z")


def optional_timestamp(value: dict[str, Any], key: str, path: str) -> None:
    if key in value:
        require_timestamp(value[key], f"{path}.{key}")


def require_unique(items: list[dict[str, Any]], path: str) -> None:
    ids = [require_string(item.get("id"), f"{path}[{index}].id") for index, item in enumerate(items)]
    if len(ids) != len(set(ids)):
        raise ValidationError(f"{path} IDs must be unique")


def valid_asset_path(value: str) -> bool:
    if not value.startswith("assets/") or "\\" in value:
        return False
    parts = PurePosixPath(value).parts
    return len(parts) > 1 and all(part not in ("", ".", "..") for part in parts)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_document(
    document: dict[str, Any],
    asset_loader: Callable[[str], bytes] | None,
) -> tuple[int, int, int, int]:
    reject_unknown(document, TOP_KEYS, "root")
    if document.get("format") != FORMAT or document.get("version") != VERSION:
        raise ValidationError("format/version must be aru-collaborator v1")

    source = require_object(document.get("source"), "source")
    reject_unknown(source, SOURCE_KEYS, "source")
    namespace = require_string(source.get("namespace"), "source.namespace")
    if not NAMESPACE.fullmatch(namespace):
        raise ValidationError("source.namespace may contain only letters, digits, dot, dash, and underscore")
    if "displayName" in source:
        require_string(source["displayName"], "source.displayName", nonempty=False)

    collaborator = require_object(document.get("collaborator"), "collaborator")
    reject_unknown(collaborator, COLLABORATOR_KEYS, "collaborator")
    require_string(collaborator.get("id"), "collaborator.id")
    require_string(collaborator.get("displayName"), "collaborator.displayName")
    for key in ("systemPrompt", "messageTemplate"):
        if key in collaborator:
            require_string(collaborator[key], f"collaborator.{key}", nonempty=False)
    optional_timestamp(collaborator, "createdAt", "collaborator")
    optional_timestamp(collaborator, "updatedAt", "collaborator")

    memories = require_array(collaborator.get("memories", []), "collaborator.memories")
    memory_objects = [require_object(item, f"collaborator.memories[{index}]") for index, item in enumerate(memories)]
    require_unique(memory_objects, "collaborator.memories")
    for index, memory in enumerate(memory_objects):
        path = f"collaborator.memories[{index}]"
        reject_unknown(memory, MEMORY_KEYS, path)
        require_string(memory.get("content"), f"{path}.content")
        optional_timestamp(memory, "createdAt", path)
        optional_timestamp(memory, "updatedAt", path)

    if "presentation" in collaborator:
        presentation = require_object(collaborator["presentation"], "collaborator.presentation")
        reject_unknown(presentation, PRESENTATION_KEYS, "collaborator.presentation")
        for key in ("assistantAvatarAssetId", "userAvatarAssetId", "backgroundAssetId"):
            if key in presentation:
                require_string(presentation[key], f"collaborator.presentation.{key}")
        if "showsAvatars" in presentation and not isinstance(presentation["showsAvatars"], bool):
            raise ValidationError("collaborator.presentation.showsAvatars must be a boolean")

    assets = require_array(document.get("assets", []), "assets")
    asset_objects = [require_object(item, f"assets[{index}]") for index, item in enumerate(assets)]
    require_unique(asset_objects, "assets")
    asset_ids: set[str] = set()
    for index, asset in enumerate(asset_objects):
        path = f"assets[{index}]"
        reject_unknown(asset, ASSET_KEYS, path)
        asset_id = require_string(asset.get("id"), f"{path}.id")
        asset_ids.add(asset_id)
        archive_path = require_string(asset.get("path"), f"{path}.path")
        if not valid_asset_path(archive_path):
            raise ValidationError(f"{path}.path must stay below assets/ without dot segments or backslashes")
        media_type = require_string(asset.get("mediaType"), f"{path}.mediaType")
        if "/" not in media_type or any(character.isspace() for character in media_type):
            raise ValidationError(f"{path}.mediaType must be a MIME media type")
        digest = require_string(asset.get("sha256"), f"{path}.sha256")
        if not SHA256.fullmatch(digest):
            raise ValidationError(f"{path}.sha256 must be 64 hexadecimal characters")
        if "filename" in asset:
            require_string(asset["filename"], f"{path}.filename", nonempty=False)
        optional_timestamp(asset, "createdAt", path)
        if asset_loader is not None:
            try:
                payload = asset_loader(archive_path)
            except (KeyError, FileNotFoundError) as error:
                raise ValidationError(f"{path}.path is missing: {archive_path}") from error
            if sha256(payload) != digest.lower():
                raise ValidationError(f"{path}.sha256 does not match {archive_path}")

    conversations = require_array(document.get("conversations"), "conversations")
    conversation_objects = [require_object(item, f"conversations[{index}]") for index, item in enumerate(conversations)]
    require_unique(conversation_objects, "conversations")
    message_count = 0
    attachment_count = 0
    for conversation_index, conversation in enumerate(conversation_objects):
        conversation_path = f"conversations[{conversation_index}]"
        reject_unknown(conversation, CONVERSATION_KEYS, conversation_path)
        if "title" in conversation:
            require_string(conversation["title"], f"{conversation_path}.title", nonempty=False)
        optional_timestamp(conversation, "createdAt", conversation_path)
        optional_timestamp(conversation, "updatedAt", conversation_path)
        messages = require_array(conversation.get("messages"), f"{conversation_path}.messages")
        message_objects = [require_object(item, f"{conversation_path}.messages[{index}]") for index, item in enumerate(messages)]
        require_unique(message_objects, f"{conversation_path}.messages")
        message_count += len(message_objects)
        for message_index, message in enumerate(message_objects):
            message_path = f"{conversation_path}.messages[{message_index}]"
            reject_unknown(message, MESSAGE_KEYS, message_path)
            role = require_string(message.get("role"), f"{message_path}.role")
            if role not in ("user", "assistant"):
                raise ValidationError(f"{message_path}.role must be user or assistant")
            content = message.get("content", "")
            reasoning = message.get("reasoning", "")
            if "content" in message:
                require_string(content, f"{message_path}.content", nonempty=False)
            if "reasoning" in message:
                require_string(reasoning, f"{message_path}.reasoning", nonempty=False)
            attachments = require_array(message.get("attachments", []), f"{message_path}.attachments")
            attachment_objects = [require_object(item, f"{message_path}.attachments[{index}]") for index, item in enumerate(attachments)]
            require_unique(attachment_objects, f"{message_path}.attachments")
            if not str(content).strip() and not str(reasoning).strip() and not attachment_objects:
                raise ValidationError(f"{message_path} must contain content, reasoning, or attachments")
            attachment_count += len(attachment_objects)
            optional_timestamp(message, "createdAt", message_path)
            optional_timestamp(message, "updatedAt", message_path)
            for attachment_index, attachment in enumerate(attachment_objects):
                attachment_path = f"{message_path}.attachments[{attachment_index}]"
                reject_unknown(attachment, ATTACHMENT_KEYS, attachment_path)
                asset_id = require_string(attachment.get("assetId"), f"{attachment_path}.assetId")
                if asset_id not in asset_ids:
                    raise ValidationError(f"{attachment_path}.assetId references an unknown asset")
                if "filename" in attachment:
                    require_string(attachment["filename"], f"{attachment_path}.filename", nonempty=False)
                optional_timestamp(attachment, "createdAt", attachment_path)

    if "extensions" in document and not isinstance(document["extensions"], dict):
        raise ValidationError("extensions must be an object")
    return len(conversation_objects), message_count, len(asset_objects), attachment_count


def directory_loader(manifest_path: Path) -> Callable[[str], bytes]:
    base = manifest_path.parent.resolve()

    def load(path: str) -> bytes:
        candidate = (base / path).resolve()
        try:
            candidate.relative_to(base)
        except ValueError as error:
            raise ValidationError(f"asset path escapes the manifest directory: {path}") from error
        return candidate.read_bytes()

    return load


def zip_loader(archive: zipfile.ZipFile) -> Callable[[str], bytes]:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValidationError("package contains duplicate ZIP entry names")
    for name in names:
        if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts:
            raise ValidationError(f"package contains an unsafe ZIP path: {name}")

    def load(path: str) -> bytes:
        return archive.read(path)

    return load


def read_and_validate(path: Path) -> tuple[dict[str, Any], tuple[int, int, int, int]]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            try:
                data = archive.read("manifest.json")
            except KeyError as error:
                raise ValidationError("package is missing root manifest.json") from error
            document = load_json(data, "manifest.json")
            counts = validate_document(document, zip_loader(archive))
            return document, counts
    document = load_json(path.read_bytes(), str(path))
    loader = directory_loader(path) if document.get("assets") else None
    return document, validate_document(document, loader)


def command_validate(path: Path) -> None:
    _, counts = read_and_validate(path)
    conversations, messages, assets, attachments = counts
    print(
        f"valid aru-collaborator v1: {conversations} conversations, "
        f"{messages} messages, {assets} assets, {attachments} attachments"
    )


def command_pack(manifest_path: Path, output_path: Path) -> None:
    document = load_json(manifest_path.read_bytes(), str(manifest_path))
    validate_document(document, directory_loader(manifest_path) if document.get("assets") else None)
    output_path = output_path.resolve()
    if output_path.suffix.lower() != ".arucollab":
        raise ValidationError("output filename must end in .arucollab")
    if output_path == manifest_path.resolve():
        raise ValidationError("output package cannot overwrite the source manifest")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    fixed_time = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest_info = zipfile.ZipInfo("manifest.json", fixed_time)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(manifest_info, manifest_bytes)
        loader = directory_loader(manifest_path)
        for asset in document.get("assets", []):
            asset_info = zipfile.ZipInfo(asset["path"], fixed_time)
            asset_info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(asset_info, loader(asset["path"]))
    print(f"wrote {output_path}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate JSON or .arucollab")
    validate.add_argument("input", type=Path)
    pack = commands.add_parser("pack", help="pack a manifest and its assets")
    pack.add_argument("manifest", type=Path)
    pack.add_argument("output", type=Path)
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "validate":
            command_validate(arguments.input)
        else:
            command_pack(arguments.manifest, arguments.output)
    except (OSError, ValidationError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
