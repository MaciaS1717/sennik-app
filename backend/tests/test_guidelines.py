from backend.services.recommendations.guidelines import load_guidelines


# guidelines, verified: do odpowiedzi trafia tylko zalecenie z verified: true;
# wpis z false albo bez pola verified jest pomijany (niesprawdzone nie może dotrzeć do użytkownika).
def test_only_verified_guidelines(tmp_path):
    path = tmp_path / "guidelines.yaml"
    path.write_text(
        "- {id: checked, title: A, text: A, sources: [], verified: true}\n"
        "- {id: rejected, title: B, text: B, sources: [], verified: false}\n"
        "- {id: no_flag, title: C, text: C, sources: []}\n",
        encoding="utf-8",
    )
    assert [g["id"] for g in load_guidelines(path)] == ["checked"]
