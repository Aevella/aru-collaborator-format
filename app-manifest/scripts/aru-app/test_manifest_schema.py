# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.26.0"]
# ///
"""Run with: uv run app-manifest/scripts/aru-app/test_manifest_schema.py"""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/aru-app-v1.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
EXAMPLES = ROOT / "examples/aru-app"


def example(name="web-page-with-mcp"):
    return json.loads((EXAMPLES / f"{name}.aruapp.json").read_text())


class ManifestSchemaTests(unittest.TestCase):
    def test_schema_and_examples(self):
        Draft202012Validator.check_schema(SCHEMA)
        for path in EXAMPLES.glob("*.json"):
            with self.subTest(file=path.name):
                VALIDATOR.validate(json.loads(path.read_text()))

    def test_setup_rejects_unknown_fields_and_other_variant_payload(self):
        for kind, payload in (
            ("mcp-server", example()["facets"][1]["setup"]),
            ("node-plugin", {
                "kind": "node-plugin",
                "nodePlugin": {
                    "pluginId": "test.plugin", "displayName": "Test", "version": "1",
                    "publisher": "Example", "source": "example", "packageMode": "oci",
                    "image": "example/plugin:1", "protocols": [], "resources": {},
                    "requestedPermissions": {"network": "none", "persistentVolume": False,
                                             "secretHandles": [], "hostPaths": [], "deviceAccess": False},
                },
            }),
        ):
            document = example()
            facet = document["facets"][1]
            facet["owner"]["kind"] = kind
            facet["setup"] = payload
            VALIDATOR.validate(document)
            for key in ("icon", "mcpServer" if kind == "node-plugin" else "nodePlugin"):
                with self.subTest(kind=kind, key=key):
                    invalid = copy.deepcopy(document)
                    invalid["facets"][1]["setup"][key] = {}
                    self.assertFalse(VALIDATOR.is_valid(invalid))

    def test_web_login_requires_a_page_and_token_parameter(self):
        document = example()
        document["facets"][0]["webLogin"] = {"method": "queryToken", "parameterName": "access_token"}
        VALIDATOR.validate(document)
        del document["facets"][0]["webLogin"]["parameterName"]
        self.assertFalse(VALIDATOR.is_valid(document))
        document["facets"][0]["webLogin"] = {"method": "httpBasic"}
        del document["facets"][0]["launchPath"]
        self.assertFalse(VALIDATOR.is_valid(document))

    def test_url_authority_preserves_hosts_ipv6_and_numeric_ports(self):
        for origin in ("https://example.com", "http://localhost:8080", "http://127.0.0.1:3000",
                       "https://[::1]:8443", "https://[2001:db8::1]", "https://例子.测试"):
            with self.subTest(origin=origin):
                document = example()
                document["runtime"]["origin"] = origin
                document["facets"][1]["setup"]["mcpServer"]["endpoint"] = origin + "/mcp"
                VALIDATOR.validate(document)

    def test_url_authority_rejects_invalid_ports_and_credentials(self):
        for origin in ("https://example.com:bad", "https://example.com:80:90",
                       "https://user:password@example.com", "https://[::1]:bad",
                       "https://example.com?token=value", "https://example.com#fragment"):
            for target in ("origin", "endpoint"):
                with self.subTest(origin=origin, target=target):
                    document = example()
                    if target == "origin":
                        document["runtime"]["origin"] = origin
                    else:
                        document["facets"][1]["setup"]["mcpServer"]["endpoint"] = origin
                    self.assertFalse(VALIDATOR.is_valid(document))


if __name__ == "__main__":
    unittest.main()
