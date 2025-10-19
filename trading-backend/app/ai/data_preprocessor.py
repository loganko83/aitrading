"""
데이터 전처리 모듈

LSTM 모델 훈련을 위한 데이터 전처리 및 시퀀스 생성

Features:
- MinMaxScaler를 이용한 정규화
- 시계열 시퀀스 생성 (lookback window)
- Train/Test/Validation 분리
- 데이터 증강 (선택적)
"""

import logging
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

logger = logging.getLogger(__name__)


class LSTMDataPreprocessor:
    """
    LSTM 모델용 데이터 전처리기

    Features:
    - 데이터 정규화 (0-1 스케일링)
    - 시계열 시퀀스 생성
    - Train/Test 분리
    """

    def __init__(
        self,
        lookback_window: int = 60,
        prediction_horizon: int = 1,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15
    ):
        """
        Args:
            lookback_window: 과거 데이터 참조 길이 (예: 60 = 60시간)
            prediction_horizon: 예측 기간 (예: 1 = 1시간 후)
            train_ratio: 훈련 데이터 비율 (0.7 = 70%)
            val_ratio: 검증 데이터 비율 (0.15 = 15%, 나머지는 테스트)
        """
        self.lookback_window = lookback_window
        self.prediction_horizon = prediction_horizon
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio

        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))

        self.feature_columns = None
        self.target_column = 'close'

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        데이터 정규화 및 변환

        Args:
            df: 원본 데이터프레임

        Returns:
            (정규화된 특징, 정규화된 타겟)
        """
        logger.info("Fitting and transforming data...")

        # 타겟 컬럼 (종가) 분리
        target = df[self.target_column].values.reshape(-1, 1)

        # 특징 컬럼 (타겟 제외한 모든 컬럼)
        feature_cols = [col for col in df.columns if col != self.target_column]
        self.feature_columns = feature_cols

        features = df[feature_cols].values

        # 정규화
        scaled_features = self.feature_scaler.fit_transform(features)
        scaled_target = self.target_scaler.fit_transform(target)

        logger.info(
            f"✅ Data normalized:\n"
            f"   Features: {len(feature_cols)} columns\n"
            f"   Target: {self.target_column}\n"
            f"   Samples: {len(df)}"
        )

        return scaled_features, scaled_target

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        새 데이터를 기존 스케일러로 변환 (추론 시 사용)

        Args:
            df: 새 데이터프레임

        Returns:
            (정규화된 특징, 정규화된 타겟)
        """
        if self.feature_columns is None:
            raise ValueError("Scaler not fitted. Call fit_transform first.")

        target = df[self.target_column].values.reshape(-1, 1)
        features = df[self.feature_columns].values

        scaled_features = self.feature_scaler.transform(features)
        scaled_target = self.target_scaler.transform(target)

        return scaled_features, scaled_target

    def inverse_transform_target(self, scaled_target: np.ndarray) -> np.ndarray:
        """
        정규화된 타겟을 원래 스케일로 복원

        Args:
            scaled_target: 정규화된 타겟 값

        Returns:
            원래 스케일의 타겟 값
        """
        return self.target_scaler.inverse_transform(scaled_target.reshape(-1, 1))

    def create_sequences(
        self,
        features: np.ndarray,
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        시계열 시퀀스 생성

        LSTM 입력 형태:
        - X: (samples, lookback_window, features)
        - y: (samples, 1)

        Args:
            features: 정규화된 특징 (samples, features)
            target: 정규화된 타겟 (samples, 1)

        Returns:
            (X 시퀀스, y 타겟)
        """
        logger.info(f"Creating sequences with lookback={self.lookback_window}...")

        X = []
        y = []

        for i in range(self.lookback_window, len(features) - self.prediction_horizon + 1):
            # 과거 lookback_window 시간의 특징
            X.append(features[i - self.lookback_window:i])

            # prediction_horizon 시간 후의 종가
            y.append(target[i + self.prediction_horizon - 1])

        X = np.array(X)
        y = np.array(y)

        logger.info(
            f"✅ Sequences created:\n"
            f"   X shape: {X.shape} (samples, timesteps, features)\n"
            f"   y shape: {y.shape} (samples, targets)"
        )

        return X, y

    def split_data(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Train/Validation/Test 분리

        Args:
            X: 특징 시퀀스
            y: 타겟 값

        Returns:
            (X_train, y_train, X_val, y_val, X_test, y_test)
        """
        total_samples = len(X)

        train_size = int(total_samples * self.train_ratio)
        val_size = int(total_samples * self.val_ratio)

        # 시계열 데이터이므로 순서 유지하며 분리
        X_train = X[:train_size]
        y_train = y[:train_size]

        X_val = X[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]

        X_test = X[train_size + val_size:]
        y_test = y[train_size + val_size:]

        logger.info(
            f"✅ Data split:\n"
            f"   Train: {len(X_train)} samples ({self.train_ratio*100:.0f}%)\n"
            f"   Val:   {len(X_val)} samples ({self.val_ratio*100:.0f}%)\n"
            f"   Test:  {len(X_test)} samples ({(1-self.train_ratio-self.val_ratio)*100:.0f}%)"
        )

        return X_train, y_train, X_val, y_val, X_test, y_test

    def prepare_lstm_data(
        self,
        df: pd.DataFrame
    ) -> dict:
        """
        LSTM 훈련용 완전한 데이터 준비

        Args:
            df: 기술적 지표가 포함된 데이터프레임

        Returns:
            {
                'X_train': ...,
                'y_train': ...,
                'X_val': ...,
                'y_val': ...,
                'X_test': ...,
                'y_test': ...,
                'feature_columns': [...],
                'scaler_params': {...}
            }
        """
        logger.info("Preparing LSTM training data...")

        # 1. 정규화
        scaled_features, scaled_target = self.fit_transform(df)

        # 2. 시퀀스 생성
        X, y = self.create_sequences(scaled_features, scaled_target)

        # 3. Train/Val/Test 분리
        X_train, y_train, X_val, y_val, X_test, y_test = self.split_data(X, y)

        # 4. 결과 딕셔너리
        result = {
            'X_train': X_train,
            'y_train': y_train,
            'X_val': X_val,
            'y_val': y_val,
            'X_test': X_test,
            'y_test': y_test,
            'feature_columns': self.feature_columns,
            'lookback_window': self.lookback_window,
            'prediction_horizon': self.prediction_horizon
        }

        logger.info("✅ LSTM data preparation complete")

        return result

    def save_scalers(self, save_dir: str = "models/scalers"):
        """
        스케일러 저장 (추론 시 재사용)

        Args:
            save_dir: 저장 디렉토리
        """
        os.makedirs(save_dir, exist_ok=True)

        feature_scaler_path = os.path.join(save_dir, "feature_scaler.pkl")
        target_scaler_path = os.path.join(save_dir, "target_scaler.pkl")

        joblib.dump(self.feature_scaler, feature_scaler_path)
        joblib.dump(self.target_scaler, target_scaler_path)

        logger.info(f"✅ Scalers saved to {save_dir}")

    def load_scalers(self, save_dir: str = "models/scalers"):
        """
        저장된 스케일러 로드

        Args:
            save_dir: 저장 디렉토리
        """
        feature_scaler_path = os.path.join(save_dir, "feature_scaler.pkl")
        target_scaler_path = os.path.join(save_dir, "target_scaler.pkl")

        if not os.path.exists(feature_scaler_path) or not os.path.exists(target_scaler_path):
            raise FileNotFoundError(f"Scalers not found in {save_dir}")

        self.feature_scaler = joblib.load(feature_scaler_path)
        self.target_scaler = joblib.load(target_scaler_path)

        logger.info(f"✅ Scalers loaded from {save_dir}")

    def get_feature_importance(self, feature_names: List[str]) -> pd.DataFrame:
        """
        특징 중요도 분석 (스케일러의 데이터 범위 기반)

        Args:
            feature_names: 특징 이름 리스트

        Returns:
            특징 중요도 데이터프레임
        """
        if self.feature_scaler.data_range_ is None:
            raise ValueError("Scaler not fitted yet")

        importance = pd.DataFrame({
            'feature': feature_names,
            'data_range': self.feature_scaler.data_range_,
            'min_value': self.feature_scaler.data_min_,
            'max_value': self.feature_scaler.data_max_
        })

        importance = importance.sort_values('data_range', ascending=False)

        return importance


# =======================
# 사용 예시
# =======================

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 데이터 수집 (이전 단계)
    from app.ai.data_collector import MarketDataCollector

    collector = MarketDataCollector()
    df = collector.prepare_dataset(symbol="BTCUSDT", interval="1h", days=365)

    # 전처리기 생성
    preprocessor = LSTMDataPreprocessor(
        lookback_window=60,  # 60시간(2.5일) 과거 데이터 참조
        prediction_horizon=1,  # 1시간 후 예측
        train_ratio=0.7,
        val_ratio=0.15
    )

    # LSTM 데이터 준비
    data = preprocessor.prepare_lstm_data(df)

    print("\n준비된 데이터:")
    print(f"X_train shape: {data['X_train'].shape}")
    print(f"y_train shape: {data['y_train'].shape}")
    print(f"X_val shape: {data['X_val'].shape}")
    print(f"y_val shape: {data['y_val'].shape}")
    print(f"X_test shape: {data['X_test'].shape}")
    print(f"y_test shape: {data['y_test'].shape}")

    # 스케일러 저장
    preprocessor.save_scalers()

    # 특징 중요도
    importance = preprocessor.get_feature_importance(data['feature_columns'])
    print("\n특징 중요도:")
    print(importance.head(10))
