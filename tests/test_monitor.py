import pandas as pd

from src.monitor import build_monitoring_profile, compare_monitoring_profile


def test_monitoring_profile_detects_large_numeric_shift():
    reference = pd.DataFrame(
        {
            "NoOfImage": list(range(1, 101)),
            "Industry": ["finance"] * 50 + ["retail"] * 50,
        }
    )
    current = pd.DataFrame(
        {
            "NoOfImage": list(range(1000, 1100)),
            "Industry": ["finance"] * 50 + ["retail"] * 50,
        }
    )

    profile = build_monitoring_profile(reference)
    report = compare_monitoring_profile(profile, current)

    assert report["status"] == "alert"
    assert any(item["feature"] == "NoOfImage" for item in report["alerts"])


def test_monitoring_profile_stays_quiet_for_same_batch():
    reference = pd.DataFrame(
        {
            "NoOfImage": list(range(1, 101)),
            "Industry": ["finance"] * 50 + ["retail"] * 50,
        }
    )

    profile = build_monitoring_profile(reference)
    report = compare_monitoring_profile(profile, reference.copy())

    assert report["status"] == "ok"
