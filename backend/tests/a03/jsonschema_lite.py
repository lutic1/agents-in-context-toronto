"""A small local reading of MongoDB's `$jsonSchema` subset, for tests without Atlas.

It covers only the keywords the A03 validators use. It is a test aid, not the
judge: the Atlas tests (`MONGODB_URI` set) are the proof that Atlas rejects a
document. `$expr` is not evaluated here; the Atlas tests cover it.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def _is_type(value: Any, bson_type: str) -> bool:
    if bson_type == "string":
        return isinstance(value, str)
    if bson_type in ("int", "long"):
        return isinstance(value, int) and not isinstance(value, bool)
    if bson_type in ("double", "number", "decimal"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if bson_type == "bool":
        return isinstance(value, bool)
    if bson_type == "date":
        return isinstance(value, datetime)
    if bson_type == "null":
        return value is None
    if bson_type == "object":
        return isinstance(value, dict)
    if bson_type == "array":
        return isinstance(value, list)
    raise ValueError(f"unsupported bsonType {bson_type}")


def errors(schema: dict[str, Any], value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if "bsonType" in schema:
        types = schema["bsonType"] if isinstance(schema["bsonType"], list) else [schema["bsonType"]]
        if not any(_is_type(value, t) for t in types):
            return [f"{path}: not {types}"]
    if "enum" in schema and not any(value == e and type(value) is type(e) for e in schema["enum"]):
        found.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            found.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            found.append(f"{path}: too short")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            found.append(f"{path}: below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            found.append(f"{path}: above {schema['maximum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                found.append(f"{path}: missing {key}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                found += errors(sub, value[key], f"{path}.{key}")
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                found.append(f"{path}: unexpected {sorted(extra)}")
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            found.append(f"{path}: fewer than {schema['minProperties']} properties")
    if isinstance(value, list):
        if "items" in schema:
            for i, item in enumerate(value):
                found += errors(schema["items"], item, f"{path}[{i}]")
        if "minItems" in schema and len(value) < schema["minItems"]:
            found.append(f"{path}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems") and len({repr(v) for v in value}) != len(value):
            found.append(f"{path}: items not unique")
    if "anyOf" in schema and not any(not errors(s, value, path) for s in schema["anyOf"]):
        found.append(f"{path}: matches none of anyOf")
    if "oneOf" in schema:
        matches = sum(1 for s in schema["oneOf"] if not errors(s, value, path))
        if matches != 1:
            found.append(f"{path}: matches {matches} of oneOf, needs exactly 1")
    for sub in schema.get("allOf", []):
        found += errors(sub, value, path)
    if "not" in schema and not errors(schema["not"], value, path):
        found.append(f"{path}: matches a forbidden schema")
    return found


def validate(validator: dict[str, Any], doc: dict[str, Any]) -> list[str]:
    return errors(validator["$jsonSchema"], doc)
