"""
모델 훈련 및 평가 모듈

LSTM 모델 훈련, 검증, 평가 및 저장

Features:
- 조기 종료 (Early Stopping)
- 학습률 스케줄링 (ReduceLROnPlateau)
- 모델 체크포인트
- 성능 평가 (MSE, MAE, 방향 정확도)
- TensorBoard 로깅 (선택적)
"""

import logging
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Dict, Optional
import json

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """
    PyTorch Dataset for Time Series

    LSTM 모델용 시계열 데이터셋
    """

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        Args:
            X: 특징 시퀀스 (samples, timesteps, features)
            y: 타겟 값 (samples, 1)
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


class EarlyStopping:
    """
    조기 종료 헬퍼

    Validation loss가 개선되지 않으면 훈련 종료
    """

    def __init__(self, patience: int = 10, min_delta: float = 0.0001):
        """
        Args:
            patience: 개선 없이 기다릴 에폭 수
            min_delta: 개선으로 간주할 최소 변화량
        """
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            logger.info(f"EarlyStopping counter: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

        return self.early_stop


class LSTMTrainer:
    """
    LSTM 모델 훈련기

    Features:
    - 훈련/검증/테스트 파이프라인
    - 조기 종료
    - 학습률 스케줄링
    - 모델 체크포인트
    - 성능 평가
    """

    def __init__(
        self,
        model: nn.Module,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5
    ):
        """
        Args:
            model: PyTorch 모델
            device: "cuda" or "cpu"
            learning_rate: 학습률
            weight_decay: L2 정규화
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate

        # 손실 함수 (MSE for regression)
        self.criterion = nn.MSELoss()

        # 옵티마이저 (Adam)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        # 학습률 스케줄러 (ReduceLROnPlateau)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )

        # 훈련 기록
        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float('inf')

        logger.info(
            f"Trainer initialized:\n"
            f"  Device: {device}\n"
            f"  Learning rate: {learning_rate}\n"
            f"  Weight decay: {weight_decay}"
        )

    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        1 에폭 훈련

        Args:
            train_loader: 훈련 데이터 로더

        Returns:
            평균 훈련 손실
        """
        self.model.train()
        epoch_loss = 0.0

        for batch_X, batch_y in train_loader:
            # 디바이스로 이동
            batch_X = batch_X.to(self.device)
            batch_y = batch_y.to(self.device)

            # 순전파
            predictions = self.model(batch_X)

            # 손실 계산
            loss = self.criterion(predictions, batch_y)

            # 역전파
            self.optimizer.zero_grad()
            loss.backward()

            # 그래디언트 클리핑 (폭발 방지)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            # 가중치 업데이트
            self.optimizer.step()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)
        return avg_loss

    def validate(self, val_loader: DataLoader) -> float:
        """
        검증

        Args:
            val_loader: 검증 데이터 로더

        Returns:
            평균 검증 손실
        """
        self.model.eval()
        epoch_loss = 0.0

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                predictions = self.model(batch_X)
                loss = self.criterion(predictions, batch_y)

                epoch_loss += loss.item()

        avg_loss = epoch_loss / len(val_loader)
        return avg_loss

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 64,
        early_stopping_patience: int = 15,
        save_dir: str = "models/lstm"
    ) -> Dict:
        """
        모델 훈련

        Args:
            X_train: 훈련 특징
            y_train: 훈련 타겟
            X_val: 검증 특징
            y_val: 검증 타겟
            epochs: 최대 에폭 수
            batch_size: 배치 크기
            early_stopping_patience: 조기 종료 patience
            save_dir: 모델 저장 디렉토리

        Returns:
            훈련 기록 딕셔너리
        """
        logger.info("Starting training...")

        # Dataset 생성
        train_dataset = TimeSeriesDataset(X_train, y_train)
        val_dataset = TimeSeriesDataset(X_val, y_val)

        # DataLoader 생성
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0  # Windows 호환성
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0
        )

        # 조기 종료 헬퍼
        early_stopping = EarlyStopping(patience=early_stopping_patience)

        # 훈련 루프
        start_time = time.time()

        for epoch in range(epochs):
            # 훈련
            train_loss = self.train_epoch(train_loader)
            self.train_losses.append(train_loss)

            # 검증
            val_loss = self.validate(val_loader)
            self.val_losses.append(val_loss)

            # 학습률 스케줄링
            self.scheduler.step(val_loss)

            # 로깅
            logger.info(
                f"Epoch {epoch+1}/{epochs} | "
                f"Train Loss: {train_loss:.6f} | "
                f"Val Loss: {val_loss:.6f}"
            )

            # 최고 모델 저장
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.save_model(save_dir, "best_model.pth")
                logger.info(f"✅ Best model saved (val_loss: {val_loss:.6f})")

            # 조기 종료 확인
            if early_stopping(val_loss):
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

        elapsed_time = time.time() - start_time

        logger.info(
            f"✅ Training complete:\n"
            f"  Total epochs: {len(self.train_losses)}\n"
            f"  Best val loss: {self.best_val_loss:.6f}\n"
            f"  Training time: {elapsed_time:.2f}s"
        )

        # 훈련 기록 저장
        history = {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'best_val_loss': self.best_val_loss,
            'epochs_trained': len(self.train_losses),
            'training_time_seconds': elapsed_time
        }

        self.save_history(save_dir, history)

        return history

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        scaler
    ) -> Dict:
        """
        모델 평가

        Args:
            X_test: 테스트 특징
            y_test: 테스트 타겟
            scaler: 타겟 스케일러 (역변환용)

        Returns:
            평가 메트릭 딕셔너리
        """
        logger.info("Evaluating model...")

        self.model.eval()

        # Dataset 및 DataLoader 생성
        test_dataset = TimeSeriesDataset(X_test, y_test)
        test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

        # 예측
        predictions = []
        actuals = []

        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(self.device)
                batch_pred = self.model(batch_X)

                predictions.append(batch_pred.cpu().numpy())
                actuals.append(batch_y.numpy())

        predictions = np.concatenate(predictions)
        actuals = np.concatenate(actuals)

        # 스케일 복원
        predictions_original = scaler.inverse_transform_target(predictions)
        actuals_original = scaler.inverse_transform_target(actuals)

        # 메트릭 계산
        mse = np.mean((predictions_original - actuals_original) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions_original - actuals_original))
        mape = np.mean(np.abs((actuals_original - predictions_original) / actuals_original)) * 100

        # 방향 정확도 (상승/하락 예측)
        direction_correct = np.sum(np.sign(predictions - 0.5) == np.sign(actuals - 0.5))
        direction_accuracy = direction_correct / len(predictions) * 100

        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'direction_accuracy': float(direction_accuracy)
        }

        logger.info(
            f"✅ Evaluation complete:\n"
            f"  RMSE: {rmse:.2f}\n"
            f"  MAE: {mae:.2f}\n"
            f"  MAPE: {mape:.2f}%\n"
            f"  Direction Accuracy: {direction_accuracy:.2f}%"
        )

        return metrics

    def save_model(self, save_dir: str, filename: str = "model.pth"):
        """
        모델 저장

        Args:
            save_dir: 저장 디렉토리
            filename: 파일명
        """
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_loss': self.best_val_loss,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }, save_path)

    def load_model(self, load_path: str):
        """
        모델 로드

        Args:
            load_path: 로드 경로
        """
        checkpoint = torch.load(load_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.best_val_loss = checkpoint['best_val_loss']
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])

        logger.info(f"✅ Model loaded from {load_path}")

    def save_history(self, save_dir: str, history: Dict):
        """
        훈련 기록 저장

        Args:
            save_dir: 저장 디렉토리
            history: 훈련 기록
        """
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "training_history.json")

        with open(save_path, 'w') as f:
            json.dump(history, f, indent=2)

        logger.info(f"✅ Training history saved to {save_path}")


# =======================
# 사용 예시
# =======================

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 데이터 준비 (이전 단계)
    from app.ai.data_collector import MarketDataCollector
    from app.ai.data_preprocessor import LSTMDataPreprocessor
    from app.ai.lstm_model import create_model

    # 1. 데이터 수집
    collector = MarketDataCollector()
    df = collector.prepare_dataset(symbol="BTCUSDT", interval="1h", days=365)

    # 2. 데이터 전처리
    preprocessor = LSTMDataPreprocessor(lookback_window=60, prediction_horizon=1)
    data = preprocessor.prepare_lstm_data(df)

    # 3. 모델 생성
    input_size = data['X_train'].shape[2]  # 특징 개수
    model = create_model(
        input_size=input_size,
        model_type="standard",
        hidden_size=128,
        num_layers=3,
        dropout=0.2
    )

    # 4. 훈련
    trainer = LSTMTrainer(model, learning_rate=0.001)

    history = trainer.fit(
        X_train=data['X_train'],
        y_train=data['y_train'],
        X_val=data['X_val'],
        y_val=data['y_val'],
        epochs=100,
        batch_size=64,
        early_stopping_patience=15
    )

    # 5. 평가
    metrics = trainer.evaluate(
        X_test=data['X_test'],
        y_test=data['y_test'],
        scaler=preprocessor
    )

    print("\n평가 결과:")
    for metric, value in metrics.items():
        print(f"{metric}: {value}")
