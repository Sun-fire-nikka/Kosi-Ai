"""Baseline models and training pipeline for Kosi Embankment AI/ML.

Currently provides scaffolding for:
- Logistic Regression
- Random Forest
- XGBoost (optional)

The pipeline is designed to be supervised-learning ready once verified
historical breach/failure event labels are collected. Until then, the
engineering vulnerability index (Phase 6) serves as the primary risk engine.

All model outputs are kept separate from the vulnerability index schema.
"""

from kosi_ai.config import settings
from pathlib import Path
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Model registry - track which models are available
AVAILABLE_MODELS = {}

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    AVAILABLE_MODELS["logistic_regression"] = "sklearn"
    AVAILABLE_MODELS["random_forest"] = "sklearn"
    logger.info("Scikit-learn models available")
except ImportError:
    logger.warning("Scikit-learn not available; baseline models disabled")

try:
    import xgboost as xgb
    AVAILABLE_MODELS["xgboost"] = "xgboost"
    logger.info("XGBoost available")
except ImportError:
    logger.info("XGBoost not available; will install if needed")


class BaselineModelRegistry:
    """Registry for baseline models with version tracking."""

    def __init__(self):
        self.models = {}  # name -> fitted model
        self.model_metadata = {}  # name -> dict of metadata
        self.feature_names = {}  # name -> list of feature names

    def register(self, name: str, model, feature_names: list,
                 metadata: dict = None):
        """Register a fitted model."""
        self.models[name] = model
        self.feature_names[name] = feature_names
        if metadata is None:
            metadata = {}
        self.model_metadata[name] = {
            "version": settings.model_version,
            "model_status": settings.model_status,
            "trained_on": str(pd.Timestamp.now()),
            "n_features": len(feature_names),
            "metadata": metadata,
        }
        logger.info(f"Registered model: {name} with {len(feature_names)} features")

    def get(self, name: str):
        """Get a registered model by name."""
        return self.models.get(name)

    def get_metadata(self, name: str) -> dict:
        """Get metadata for a registered model."""
        return self.model_metadata.get(name, {})

    def list_models(self) -> list:
        """List registered model names."""
        return list(self.models.keys())


class VulnerabilityTrainer:
    """Training pipeline for supervised models once labeled breach data is available.

    This class is intentionally kept as a skeleton/infrastructure until verified
    historical breach/failure event labels are collected. Do NOT train on synthetic
    labels as if they were real Kosi data.
    """

    def __init__(self, model_registry: BaselineModelRegistry = None):
        self.registry = model_registry or BaselineModelRegistry()
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.train_metrics = {}
        self.test_metrics = {}

    def prepare_training_data(self,
                              df: pd.DataFrame,
                              target_column: str = "failure_event_within_horizon",
                              feature_columns: list = None,
                              test_size: float = 0.3,
                              random_state: int = 42) -> dict:
        """Prepare training data from a DataFrame.

        Args:
            df: Input DataFrame with features and target
            target_column: Name of the binary target column (0/1)
            feature_columns: List of feature column names; if None, use all
                             engineered features except ID/target
            test_size: Fraction of data for test holdout
            random_state: Random seed

        Returns:
            dict with X_train, X_test, y_train, y_test, feature_names
        """
        np.random.seed(random_state)

        if feature_columns is None:
            # Automatically detect feature columns (exclude ID-like and target)
            exclude = {"segment_id", "latitude", "longitude", "chainage",
                       "dataset_status", target_column}
            feature_columns = [c for c in df.columns
                               if c not in exclude and
                               df[c].dtype in [np.float64, np.float32, np.int64, np.int32]
                               and df[col].nunique() > 1]
            logger.info(f"Auto-detected {len(feature_columns)} feature columns")

        # Check target column exists
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")

        # Split into features and target
        X = df[feature_columns].copy()
        y = df[target_column].copy()

        # Handle missing values
        X = X.fillna(X.median(numeric_only=True))

        # Chronological/temporal split: sort by time and split
        # This is a placeholder - actual implementation would use proper
        # temporal/event-aware splitting
        df_sorted = df.sort_values(by="river_level" if "river_level" in df.columns else df.index)
        split_idx = int(len(df_sorted) * (1 - test_size))

        train_df = df_sorted.iloc[:split_idx]
        test_df = df_sorted.iloc[split_idx:]

        self.X_train = train_df[feature_columns]
        self.X_test = test_df[feature_columns]
        self.y_train = train_df[target_column]
        self.y_test = test_df[target_column]

        self.registry.register(
            "baseline_trial",
            None,  # model will be trained separately
            feature_names=feature_columns,
            metadata={"test_size": test_size, "random_state": random_state}
        )

        logger.info(f"Training data prepared: {len(self.X_train)} train, "
                    f"{len(self.X_test)} test samples")

        return {
            "X_train": self.X_train,
            "X_test": self.X_test,
            "y_train": self.y_train,
            "y_test": self.y_test,
            "feature_names": feature_columns
        }

    def train_logistic_regression(self,
                                  penalty: str = "l2",
                                  C: float = 1.0,
                                  max_iter: int = 1000) -> dict:
        """Train a Logistic Regression baseline.

        Only call after prepare_training_data() has been executed.
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            precision_score, recall_score, f1_score, roc_auc_score,
            confusion_matrix, classification_report
        )

        if self.X_train is None or self.X_test is None:
            raise RuntimeError("Training data not prepared. Call "
                              "prepare_training_data() first.")

        logger.info("Training Logistic Regression baseline...")

        model = LogisticRegression(
            penalty=penalty,
            C=C,
            max_iter=max_iter,
            random_state=settings.default_seed,
            solver="lbfgs"
        )

        model.fit(self.X_train, self.y_train)

        # Predictions
        y_train_pred = model.predict(self.X_train)
        y_test_pred = model.predict(self.X_test)
        y_test_proba = model.predict_proba(self.X_test)[:, 1]

        # Metrics
        self.train_metrics = {
            "precision": precision_score(self.y_train, y_train_pred, zero_division=0),
            "recall": recall_score(self.y_train, y_train_pred, zero_division=0),
            "f1": f1_score(self.y_train, y_train_pred, zero_division=0),
        }

        self.test_metrics = {
            "precision": precision_score(self.y_test, y_test_pred, zero_division=0),
            "recall": recall_score(self.y_test, y_test_pred, zero_division=0),
            "f1": f1_score(self.y_test, y_test_pred, zero_division=0),
            "roc_auc": roc_auc_score(self.y_test, y_test_proba)
            if len(np.unique(self.y_test)) > 1 else float("nan"),
            "confusion_matrix": confusion_matrix(self.y_test, y_test_pred).tolist(),
        }

        # Register the model
        self.registry.register(
            "logistic_regression",
            model,
            feature_names=list(self.X_train.columns),
            metadata={"penalty": penalty, "C": C, "metrics": self.test_metrics}
        )

        logger.info(f"Logistic Regression trained. Test metrics: "
                     f"precision={self.test_metrics['precision']:.3f}, "
                     f"recall={self.test_metrics['recall']:.3f}, "
                     f"f1={self.test_metrics['f1']:.3f}, "
                     f"roc_auc={self.test_metrics['roc_auc']:.3f}")

        return {
            "model": model,
            "train_metrics": self.train_metrics,
            "test_metrics": self.test_metrics
        }

    def train_random_forest(self,
                            n_estimators: int = 100,
                            max_depth: int = None,
                            min_samples_leaf: int = 1) -> dict:
        """Train a Random Forest baseline.

        Only call after prepare_training_data() has been executed.
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import (
            precision_score, recall_score, f1_score, roc_auc_score,
            confusion_matrix
        )

        if self.X_train is None or self.X_test is None:
            raise RuntimeError("Training data not prepared. Call "
                              "prepare_training_data() first.")

        logger.info("Training Random Forest baseline...")

        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=settings.default_seed,
            n_jobs=-1,
            class_weight="balanced"  # handle imbalance
        )

        model.fit(self.X_train, self.y_train)

        # Predictions
        y_train_pred = model.predict(self.X_train)
        y_test_pred = model.predict(self.X_test)
        y_test_proba = model.predict_proba(self.X_test)[:, 1]

        # Metrics
        self.train_metrics = {
            "precision": precision_score(self.y_train, y_train_pred, zero_division=0),
            "recall": recall_score(self.y_train, y_train_pred, zero_division=0),
            "f1": f1_score(self.y_train, y_train_pred, zero_division=0),
        }

        self.test_metrics = {
            "precision": precision_score(self.y_test, y_test_pred, zero_division=0),
            "recall": recall_score(self.y_test, y_test_pred, zero_division=0),
            "f1": f1_score(self.y_test, y_test_pred, zero_division=0),
            "roc_auc": roc_auc_score(self.y_test, y_test_proba)
            if len(np.unique(self.y_test)) > 1 else float("nan"),
            "confusion_matrix": confusion_matrix(self.y_test, y_test_pred).tolist(),
        }

        # Register the model
        self.registry.register(
            "random_forest",
            model,
            feature_names=list(self.X_train.columns),
            metadata={
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "min_samples_leaf": min_samples_leaf,
                "metrics": self.test_metrics
            }
        )

        logger.info(f"Random Forest trained. Test metrics: "
                     f"precision={self.test_metrics['precision']:.3f}, "
                     f"recall={self.test_metrics['recall']:.3f}, "
                     f"f1={self.test_metrics['f1']:.3f}, "
                     f"roc_auc={self.test_metrics['roc_auc']:.3f}")

        return {
            "model": model,
            "train_metrics": self.train_metrics,
            "test_metrics": self.test_metrics
        }

    def train_xgboost(self,
                      n_estimators: int = 100,
                      max_depth: int = 6,
                      eval_metric: str = "logloss") -> dict:
        """Train an XGBoost baseline (optional, if available).

        Only call after prepare_training_data() has been executed.
        """
        if "xgboost" not in AVAILABLE_MODELS:
            raise ImportError(
                "XGBoost not available. Install with: pip install xgboost"
            )

        from xgboost import XGBClassifier
        from sklearn.metrics import (
            precision_score, recall_score, f1_score, roc_auc_score,
            confusion_matrix
        )

        if self.X_train is None or self.X_test is None:
            raise RuntimeError("Training data not prepared. Call "
                              "prepare_training_data() first.")

        logger.info("Training XGBoost baseline...")

        model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            eval_metric=eval_metric,
            random_state=settings.default_seed,
            use_label_encoder=False,
            n_jobs=-1,
            scale_pos_weight="balanced"
        )

        model.fit(self.X_train, self.y_train,

                  # Early stopping on validation set
                  eval_set=[(self.X_test, self.y_test)],
                  early_stopping_rounds=20,
                  verbose=False)

        # Predictions
        y_test_pred = model.predict(self.X_test)
        y_test_proba = model.predict_proba(self.X_test)[:, 1]

        # Metrics
        self.test_metrics = {
            "precision": precision_score(self.y_test, y_test_pred, zero_division=0),
            "recall": recall_score(self.y_test, y_test_pred, zero_division=0),
            "f1": f1_score(self.y_test, y_test_pred, zero_division=0),
            "roc_auc": roc_auc_score(self.y_test, y_test_proba)
            if len(np.unique(self.y_test)) > 1 else float("nan"),
            "confusion_matrix": confusion_matrix(self.y_test, y_test_pred).tolist(),
        }

        # Store train metrics from best iteration
        self.train_metrics = {
            "precision": float("nan"),
            "recall": float("nan"),
            "f1": float("nan"),
        }

        # Register the model
        self.registry.register(
            "xgboost",
            model,
            feature_names=list(self.X_train.columns),
            metadata={
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "metrics": self.test_metrics
            }
        )

        logger.info(f"XGBoost trained. Test metrics: "
                     f"precision={self.test_metrics['precision']:.3f}, "
                     f"recall={self.test_metrics['recall']:.3f}, "
                     f"f1={self.test_metrics['f1']:.3f}, "
                     f"roc_auc={self.test_metrics['roc_auc']:.3f}")

        return {
            "model": model,
            "train_metrics": self.train_metrics,
            "test_metrics": self.test_metrics
        }

    def feature_importance(self, model_name: str = "random_forest",
                          plot: bool = False) -> dict:
        """Extract feature importance from a trained model.

        Returns dict with feature names and importance scores.
        """
        model = self.registry.get(model_name)
        if model is None:
            logger.error(f"Model '{model_name}' not found in registry")
            return {}

        importances = {}
        feat_names = self.registry.feature_names.get(model_name, [])

        if feat_names is None or len(feat_names) == 0:
            logger.warning(f"No feature names found for model '{model_name}'")
            return {}

        # Get importance from model
        if hasattr(model, "feature_importances_"):
            # Tree-based models
            raw_importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            # Linear models
            raw_importances = np.abs(model.coef_[0])
        else:
            logger.warning(f"Model '{model_name}' has no feature_importances_ or coef_")
            return {}

        # Normalize to sum to 1
        if raw_importances.sum() > 0:
            importances = {name: float(val / raw_importances.sum())
                           for name, val in zip(feat_names, raw_importances)}
        else:
            importances = {name: 1.0 / len(feat_names) for name in feat_names}

        # Sort by importance descending
        importances = dict(sorted(importances.items(),
                                  key=lambda x: x[1],
                                  reverse=True))

        return importances