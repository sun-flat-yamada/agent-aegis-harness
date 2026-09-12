"""
Unit tests for WeeklyGovernanceReporter
Verifies 5 core governance KPIs calculation and international standards footnotes rendering.
"""
from datetime import datetime
import pytest
from aegis.refiner.weekly_reporter import WeeklyGovernanceReporter


def test_weekly_governance_report_aggregation():
    events = [
        {
            "trace_id": "tr-001",
            "timestamp": "2026-09-10T10:00:00Z",
            "environment": {"repository": "app-checkout", "user_hash": "user_A"},
            "trigger": {"redaction_applied": ["[REDACTED_API_KEY]"]},
            "sentinel_verdict": {"status": "PASS", "violations": []},
        },
        {
            "trace_id": "tr-002",
            "timestamp": "2026-09-11T12:00:00Z",
            "environment": {"repository": "app-billing", "user_hash": "user_B"},
            "trigger": {"redaction_applied": []},
            "sentinel_verdict": {
                "status": "BLOCK",
                "violations": [{"message": "Dangerous recursive disk deletion detected"}],
            },
        },
        {
            "trace_id": "tr-003",
            "timestamp": "2026-09-12T14:00:00Z",
            "environment": {"repository": "app-checkout", "user_hash": "user_A"},
            "trigger": {"redaction_applied": ["[REDACTED_PASSWORD]", "[REDACTED_JWT]"]},
            "sentinel_verdict": {"status": "PASS", "violations": []},
        },
    ]

    reporter = WeeklyGovernanceReporter(events)
    report = reporter.aggregate_metrics()

    assert report.total_tool_executions == 3
    assert report.total_active_projects == 2  # app-checkout, app-billing
    assert report.total_active_users == 2  # user_A, user_B
    assert len(report.kpi_metrics) == 5

    # 1. マスキング数 (1 + 0 + 2 = 3件)
    kpi_sec_1 = next(k for k in report.kpi_metrics if k.kpi_id == "KPI-SEC-01")
    assert kpi_sec_1.current_value == 3.0

    # 2. ブロック数 (1件)
    kpi_sec_2 = next(k for k in report.kpi_metrics if k.kpi_id == "KPI-SEC-02")
    assert kpi_sec_2.current_value == 1.0

    # 3. インシデント詳細
    assert len(report.incident_highlights) == 1
    assert "Dangerous recursive disk deletion detected" in report.incident_highlights[0]["violations"]


def test_weekly_governance_report_footnotes_rendering():
    """レポート末尾に国際標準の引用リンクと改善意図フッターが正しくレンダリングされることを検証"""
    reporter = WeeklyGovernanceReporter([])
    report = reporter.aggregate_metrics()
    md = reporter.render_markdown(report)

    # 主要セクションの存在確認
    assert "# 🛡️ 週次 AI 開発ガバナンス監査レポート" in md
    assert "## 1. エグゼクティブ・サマリー" in md
    assert "## 2. 5大ガバナンス KPI ダッシュボード" in md
    assert "## 3. インシデント & ヒヤリハット詳細" in md
    assert "## 4. 監査役・法務レビュー承認欄 (Sign-off)" in md
    assert "## 📚 付録: 監査 KPI の引用元・規格参照および改善ガイダンス" in md

    # 国際規格の引用リンク・解説の確認 (必須要件)
    assert "NIST AI RMF 1.0" in md
    assert "https://airc.nist.gov/AI-RMF-Knowledge-Base" in md
    assert "ISO/IEC 42001:2023" in md
    assert "https://www.iso.org/standard/81230.html" in md
    assert "EU AI Act 第12条" in md
    assert "https://artificialintelligenceact.eu/article/12/" in md
    assert "OWASP Top 10 for LLM" in md
    assert "SOC 2 Type II" in md
    assert "https://www.rfc-editor.org/rfc/rfc6962" in md

    # 承認チェックボックスの確認
    assert "- [ ] 常勤監査役 確認承認" in md
    assert "- [ ] 法務・コンプライアンス責任者 確認承認" in md
