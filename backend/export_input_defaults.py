"""Transport defaults for stable client identities, derived from Pydantic and OpenAPI."""

import json
from pathlib import Path

from app import schemas
from pydantic_core import PydanticUndefined

contract = json.loads(Path("openapi.json").read_text())["components"]["schemas"]
nodes = {}


def reference(property_schema):
    refs = set()
    if "$ref" in property_schema:
        refs.add(property_schema["$ref"].rsplit("/", 1)[-1])
    for option in property_schema.get("anyOf", []) + property_schema.get("allOf", []):
        if "$ref" in option:
            refs.add(option["$ref"].rsplit("/", 1)[-1])
    return next(iter(refs)) if len(refs) == 1 else None


def visit(name):
    if name in nodes:
        return
    model = getattr(schemas, name, None)
    if model is None or not hasattr(model, "model_fields"):
        return
    node = dict(defaults={}, objects={}, arrays={})
    nodes[name] = node
    for field, schema in contract[name].get("properties", {}).items():
        definition = model.model_fields[field]
        if definition.default is not PydanticUndefined:
            node["defaults"][field] = definition.default
        elif definition.default_factory in (list, dict):
            node["defaults"][field] = definition.default_factory()
        # Do not execute UUID factories or guess a branch of a union.
        child = reference(schema)
        if child:
            node["objects"][field] = child
            visit(child)
        child = reference(schema.get("items", {}))
        if child:
            node["arrays"][field] = child
            visit(child)


for root in ("ProjectInput", "CalculationInput"):
    visit(root)
Path("../frontend/src/lib/input-defaults.generated.json").write_text(
    json.dumps(nodes, ensure_ascii=False, indent=2, default=str) + "\n"
)
