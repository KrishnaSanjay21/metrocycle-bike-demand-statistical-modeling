from scripts.health_check import collect_status


def test_health_check_reports_ready_pipeline():
    status = collect_status()
    assert status["ready"] is True
    assert status["critical_quality_failures"] == 0
    assert status["analytical_rows"] == 17_379
    assert status["best_model"] == "Gradient Boosting"
