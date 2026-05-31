from __future__ import annotations

import json
from pathlib import Path

from bench.run_qwen15b_quant_curve_report import build_report, main


def _write_manifest(tmp_path: Path) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifact": "qwen15b-quant-curve-manifest",
                "model_family": "Qwen2.5-Coder-1.5B-Instruct",
                "source_repo": "bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF",
                "required_quants": [
                    {
                        "quant": "Q8_0",
                        "filename": "Qwen2.5-Coder-1.5B-Instruct-Q8_0.gguf",
                        "smoke_json": str(
                            tmp_path / "results_v14_qwen15b_q8_0_smoke_schema_v1.json"
                        ),
                        "smoke_command": "run q8",
                    },
                    {
                        "quant": "Q6_K",
                        "filename": "Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf",
                        "smoke_json": str(
                            tmp_path / "results_v14_qwen15b_q6_k_smoke_schema_v1.json"
                        ),
                        "smoke_command": "run q6",
                    },
                    {
                        "quant": "Q4_K_M",
                        "filename": "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf",
                        "smoke_json": str(
                            tmp_path / "results_v14_qwen15b_q4_k_m_smoke_schema_v1.json"
                        ),
                        "smoke_command": "run q4",
                    },
                ],
                "final_artifacts": [
                    "bench/results_v14_qwen15b_quant_curve.json",
                    "bench/results_v14_qwen15b_quant_curve.md",
                    "bench/results_v14_qwen15b_quant_curve.pdf",
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _write_smoke(path: Path, quant: str, passed: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "benchmark": "schema-v1-smoke",
                "model": "Qwen2.5-Coder-1.5B-Instruct",
                "quant": quant,
                "calls": 4,
                "go_no_go": {"pass": passed},
                "summary": {
                    "parse_ok": 4 if passed else 1,
                    "parse_failed": 0 if passed else 3,
                },
            }
        ),
        encoding="utf-8",
    )


def test_quant_curve_report_blocks_when_smokes_are_missing(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    report = build_report(manifest)

    assert report["summary"]["release_ready"] is False
    assert report["summary"]["missing_quant_smokes"] == ["Q8_0", "Q6_K", "Q4_K_M"]
    assert all(row["present"] is False for row in report["rows"])


def test_quant_curve_report_writes_final_artifacts_only_when_ready(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path)
    for quant in ("Q8_0", "Q6_K", "Q4_K_M"):
        _write_smoke(
            tmp_path / f"results_v14_qwen15b_{quant.lower()}_smoke_schema_v1.json",
            quant,
        )
    json_path = tmp_path / "curve.json"
    md_path = tmp_path / "curve.md"
    pdf_path = tmp_path / "curve.pdf"

    rc = main(
        [
            "--manifest",
            str(manifest),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--pdf-output",
            str(pdf_path),
            "--quiet",
        ]
    )

    assert rc == 0
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"][
        "release_ready"
    ] is True
    assert "release ready: True" in md_path.read_text(encoding="utf-8")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")


def test_quant_curve_report_does_not_write_incomplete_outputs_by_default(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path)
    json_path = tmp_path / "curve.json"
    md_path = tmp_path / "curve.md"
    pdf_path = tmp_path / "curve.pdf"

    rc = main(
        [
            "--manifest",
            str(manifest),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--pdf-output",
            str(pdf_path),
            "--quiet",
        ]
    )

    assert rc == 1
    assert not json_path.exists()
    assert not md_path.exists()
    assert not pdf_path.exists()


def test_quant_curve_report_check_does_not_write_outputs(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    for quant in ("Q8_0", "Q6_K", "Q4_K_M"):
        _write_smoke(
            tmp_path / f"results_v14_qwen15b_{quant.lower()}_smoke_schema_v1.json",
            quant,
        )
    json_path = tmp_path / "curve.json"

    rc = main(
        [
            "--manifest",
            str(manifest),
            "--json-output",
            str(json_path),
            "--check",
            "--quiet",
        ]
    )

    assert rc == 0
    assert not json_path.exists()
