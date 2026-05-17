import tempfile
from pathlib import Path
import pytest
from harness.skill_hash import compute_skill_hash


def _make_skill_dir(files: dict[str, str]) -> Path:
    tmp = tempfile.mkdtemp()
    d = Path(tmp)
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return d


def test_hash_starts_with_prefix():
    d = _make_skill_dir({"SKILL.md": "# Hello", "references/rules.md": "rules"})
    h = compute_skill_hash(d)
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 16


def test_hash_is_deterministic():
    d = _make_skill_dir({"SKILL.md": "# Hello", "references/rules.md": "rules"})
    assert compute_skill_hash(d) == compute_skill_hash(d)


def test_hash_changes_when_file_changes(tmp_path):
    f = tmp_path / "SKILL.md"
    f.write_text("original")
    h1 = compute_skill_hash(tmp_path)
    f.write_text("modified")
    h2 = compute_skill_hash(tmp_path)
    assert h1 != h2


def test_hash_changes_when_file_added(tmp_path):
    (tmp_path / "SKILL.md").write_text("base")
    h1 = compute_skill_hash(tmp_path)
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "extra.md").write_text("extra")
    h2 = compute_skill_hash(tmp_path)
    assert h1 != h2
