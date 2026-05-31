from __future__ import annotations

import json

from bench.run_scratch_live_gate import load_skillopt_review_evidence
from bench.run_skillopt_review_packet import build_review_packet, main, write_reports


def _write_skill(root, slug, *, review_required=True):
    review_line = (
        "    review_required: true"
        if review_required
        else "    review_required: false"
    )
    path = root / slug / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"name: {slug}",
                "description: generated test skill",
                "auto_generated:",
                "  by: skill-opt",
                "  date: 2026-05-31",
                "  source_goal: Build an audit workflow",
                "  planner_model: test-planner",
                review_line,
                "---",
                "",
                f"# {slug}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_skillopt_review_packet_collects_only_review_gated_skills(tmp_path):
    skills_root = tmp_path / ".skills"
    _write_skill(skills_root, "generated-one")
    _write_skill(skills_root, "already-reviewed", review_required=False)

    packet = build_review_packet(skills_root=skills_root)

    assert packet["benchmark"] == "skillopt-review-packet"
    assert packet["summary"]["review_gated_skills"] == 1
    assert packet["summary"]["release_ready"] is False
    assert packet["reviews"][0]["skill"] == "generated-one"
    assert packet["reviews"][0]["approved"] is None
    assert packet["reviews"][0]["reviewer"] == ""
    assert len(packet["reviews"][0]["sha256"]) == 64


def test_skillopt_review_packet_pending_rows_do_not_pass_live_gate(tmp_path):
    skills_root = tmp_path / ".skills"
    _write_skill(skills_root, "generated-one")
    packet = build_review_packet(skills_root=skills_root)
    json_path = tmp_path / "packet.json"
    md_path = tmp_path / "packet.md"

    write_reports(packet, json_path, md_path)
    normalized = load_skillopt_review_evidence(json_path)

    assert normalized["total_reviews"] == 0
    assert normalized["invalid_reviews"] == 1
    assert normalized["gate_passed"] is False
    assert "SkillOpt Human Review Packet" in md_path.read_text(encoding="utf-8")


def test_skillopt_review_packet_main_writes_reports(tmp_path):
    skills_root = tmp_path / ".skills"
    _write_skill(skills_root, "generated-one")
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"

    rc = main(
        [
            "--skills-root",
            str(skills_root),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--quiet",
        ]
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["summary"]["pending_reviews"] == 1
    assert "generated-one" in md_path.read_text(encoding="utf-8")
