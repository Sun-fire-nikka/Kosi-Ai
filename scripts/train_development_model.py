#!/usr/bin/env python
"""Train synthetic development models (Logistic Regression + Random Forest).

Usage: python scripts/train_development_model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kosi_ai.data import loaders          # noqa: E402
from kosi_ai.models import development     # noqa: E402


def main():
    df = loaders.load_synthetic_development()
    print(f"Loaded SYNTHETIC_DEVELOPMENT_ONLY dataset: {df.shape}")
    report = development.train_all(df)
    for name, r in report.items():
        m = r["metrics"]
        line = (f"{name}: precision={m['precision']} recall={m['recall']} "
                f"f1={m['f1']}")
        if "roc_auc" in m:
            line += f" roc_auc={m['roc_auc']} pr_auc={m['pr_auc']}"
        print(line)
    print("All artifacts labelled SYNTHETIC_DEVELOPMENT_ONLY.")
    print("These metrics do NOT represent real-world Kosi prediction accuracy.")


if __name__ == "__main__":
    main()
