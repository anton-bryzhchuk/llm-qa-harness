"""Suite 4: invariance / metamorphic tests."""
from __future__ import annotations

from llmqa.suites.invariance import _keyword_guard, run_invariance, t_typo, t_upper


def test_good_profile_is_invariant(good_make):
    res = run_invariance(good_make)
    assert res.passed
    assert res.metrics["violations"] == 0
    assert res.metrics["checks"] > 0
    # all five transforms were actually exercised
    assert set(res.metrics["per_transform"]) == {
        "uppercase",
        "trailing_whitespace",
        "strip_trailing_punct",
        "polite_wrapper",
        "typo",
    }


def test_transforms_change_the_string():
    text = "The app crashes on startup."
    assert t_upper(text) != text
    typo = t_typo(text, _keyword_guard())
    # the keyword 'crashes' must be preserved by the typo transform
    assert "crashes" in typo.lower()
    assert typo != text
