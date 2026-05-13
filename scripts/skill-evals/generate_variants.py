#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jinja2>=3.1,<4", "pyyaml>=6,<7"]
# ///
"""Generate skill variants from a baseline SKILL.md without mutating the original.

Usage:
  uv run scripts/skill-evals/generate_variants.py --skill-dir skills/software-feature-planning
  uv run scripts/skill-evals/generate_variants.py --skill-dir skills/software-feature-planning --variant delivery-focused
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from jinja2 import BaseLoader, Environment

DEFAULT_TEMPLATE = """---
name: {{ name }}
description: {{ description }}
---

{% if body_prefix %}{{ body_prefix.rstrip() }}

{% endif %}{{ body.rstrip() }}
{% if body_suffix %}

{{ body_suffix.rstrip() }}
{% endif %}
"""

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter_and_body(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    frontmatter: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    body = text[match.end():].lstrip("\n")
    return frontmatter, body


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: variants config must be a YAML object")
    return payload


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "variant"


def apply_replacements(text: str, replacements: list[dict[str, Any]]) -> str:
    updated = text
    for index, replacement in enumerate(replacements):
        if not isinstance(replacement, dict):
            raise ValueError(f"Replacement at index {index} must be an object")
        old = str(replacement.get("old", ""))
        new = str(replacement.get("new", ""))
        if not old:
            raise ValueError(f"Replacement at index {index} must include a non-empty 'old'")
        count = updated.count(old)
        if count != 1:
            raise ValueError(f"Replacement at index {index} expected exactly one match for {old!r}, found {count}")
        updated = updated.replace(old, new, 1)
    return updated


def render_template(template_text: str, context: dict[str, Any]) -> str:
    environment = Environment(loader=BaseLoader(), autoescape=False, keep_trailing_newline=True)
    template = environment.from_string(template_text)
    return template.render(**context)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, required=True, help="Skill directory containing SKILL.md")
    parser.add_argument("--variants", type=Path, help="YAML variants config; defaults to <skill-dir>/evals/variants.yaml")
    parser.add_argument("--template", type=Path, help="Optional Jinja template path")
    parser.add_argument("--output-root", type=Path, default=Path("experiments/variants"), help="Output root for rendered variants")
    parser.add_argument("--variant", action="append", default=[], help="Render only the named variant id (repeatable)")
    args = parser.parse_args()

    skill_dir = args.skill_dir.expanduser().resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(skill_md)

    variants_path = (args.variants.expanduser().resolve() if args.variants else (skill_dir / "evals" / "variants.yaml"))
    if not variants_path.exists():
        raise FileNotFoundError(variants_path)

    template_path = args.template.expanduser().resolve() if args.template else None
    frontmatter, body = parse_frontmatter_and_body(skill_md)
    config = load_yaml(variants_path)
    variants = config.get("variants", [])
    if not isinstance(variants, list) or not variants:
        raise ValueError(f"{variants_path}: expected a non-empty 'variants' array")

    selected_ids = set(args.variant)
    name = frontmatter.get("name", skill_dir.name)
    description = frontmatter.get("description", "")

    if template_path is not None:
        template_text = template_path.read_text(encoding="utf-8")
    else:
        template_text = str(config.get("template", DEFAULT_TEMPLATE))

    base_context = {
        "name": name,
        "description": description,
        "body": body,
        "body_prefix": "",
        "body_suffix": "",
    }
    if isinstance(config.get("context"), dict):
        base_context.update(config["context"])

    output_root = args.output_root.expanduser().resolve() / slugify(name)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    base_sha256 = hashlib.sha256(skill_md.read_bytes()).hexdigest()

    for raw_variant in variants:
        if not isinstance(raw_variant, dict):
            raise ValueError("Each variant must be an object")
        variant_id = str(raw_variant.get("id", "")).strip()
        if not variant_id:
            raise ValueError("Each variant must include an 'id'")
        if selected_ids and variant_id not in selected_ids:
            continue

        context = dict(base_context)
        if isinstance(raw_variant.get("context"), dict):
            context.update(raw_variant["context"])
        if "description" in raw_variant:
            context["description"] = str(raw_variant["description"])
        if "body_prefix" in raw_variant:
            context["body_prefix"] = str(raw_variant["body_prefix"])
        if "body_suffix" in raw_variant:
            context["body_suffix"] = str(raw_variant["body_suffix"])
        context["variant_id"] = variant_id

        rendered = render_template(template_text, context).rstrip() + "\n"
        replacements = raw_variant.get("replacements", [])
        if replacements:
            if not isinstance(replacements, list):
                raise ValueError(f"Variant {variant_id!r}: replacements must be an array")
            rendered = apply_replacements(rendered, replacements)

        variant_dir = output_root / slugify(variant_id)
        variant_dir.mkdir(parents=True, exist_ok=True)
        output_path = variant_dir / "SKILL.md"
        output_path.write_text(rendered, encoding="utf-8")

        rendered_sha256 = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        metadata = {
            "variant_id": variant_id,
            "skill_name": name,
            "skill_dir": str(skill_dir),
            "base_skill": str(skill_md),
            "base_sha256": base_sha256,
            "rendered_sha256": rendered_sha256,
            "description": context.get("description", ""),
            "output": str(output_path),
        }
        (variant_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest.append(metadata)

    print(json.dumps({"variants": manifest, "output_root": str(output_root)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
