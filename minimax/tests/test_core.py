from pathlib import Path

from sddctx.config import ROOT
from sddctx.editing import extract_python_module, materialize_model_output, validate_source
from sddctx.embeddings import embed_text
from sddctx.minimax_api import build_messages
from sddctx.textutil import decide_action, lexical_score, parse_kv, scrub

SAMPLE = ROOT / "sample"


def test_embedding_is_stable_and_normalized():
    first = embed_text("节日加班 overtime_pay")
    second = embed_text("节日加班 overtime_pay")
    assert first == second
    assert abs(sum(value * value for value in first) - 1) < 1e-6


def test_parking_material_is_not_selected_by_lexical_overlap():
    task = (SAMPLE / "TASK.md").read_text(encoding="utf-8")
    spec = (SAMPLE / "docs" / "spec.md").read_text(encoding="utf-8")
    code = (SAMPLE / "src" / "shiftpay.py").read_text(encoding="utf-8")
    feature = (SAMPLE / "tests" / "test_feature_holiday.py").read_text(encoding="utf-8")
    parking = (SAMPLE / "docs" / "parking.md").read_text(encoding="utf-8")
    prefixed = "path: docs/parking.md\nsymbol: 停车\nkind: spec\nrole: decoy\n\n" + parking
    assert lexical_score(task, prefixed, {"symbol": "停车"}) == 0
    assert lexical_score(task, spec, {"symbol": "节日加班"}) > 0
    assert lexical_score(task, code, {"symbol": "overtime_pay"}) > 0
    assert lexical_score(task, feature, {"symbol": "test_holiday_overtime_uses_spec_multiplier"}) > 0


def test_extract_full_file_from_model_text():
    source = (SAMPLE / "src" / "shiftpay.py").read_text(encoding="utf-8")
    wrapped = "说明\n```python\n" + source + "```\n"
    assert extract_python_module(wrapped) == source if source.endswith("\n") else source + "\n"
    updated = materialize_model_output(source, wrapped)
    validate_source(updated)


def test_decide_action_uses_saved_verification():
    assert decide_action({}) == "empty"
    assert decide_action(parse_kv("verification=dry_run\nfeature_exit=1\nregression_exit=0")) == "continue_edit"
    assert (
        decide_action(parse_kv("verification=passed\nfeature_exit=0\nregression_exit=0"))
        == "skip_edit"
    )


def test_prompt_contains_context_and_scrub_removes_key():
    messages = build_messages("HOLIDAY_MULTIPLIER = 3.0\n")
    assert messages[1]["content"].startswith("HOLIDAY_MULTIPLIER = 3.0")
    assert "sk-secret" not in scrub("token sk-secret end", "sk-secret")
