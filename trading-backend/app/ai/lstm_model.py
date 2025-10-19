"""
LSTM 모델 아키텍처

PyTorch 기반 LSTM 모델로 시계열 가격 예측

Features:
- Multi-layer LSTM with Dropout
- Batch Normalization
- Residual Connections (선택적)
- 학습률 스케줄링
"""

import logging
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class PricePredictionLSTM(nn.Module):
    """
    가격 예측 LSTM 모델

    Architecture:
    - Input Layer: (batch, sequence_length, input_features)
    - LSTM Layers: Multiple stacked LSTM layers with dropout
    - Batch Normalization
    - Fully Connected Layers
    - Output Layer: (batch, 1) - 예측 가격
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2,
        output_size: int = 1
    ):
        """
        Args:
            input_size: 입력 특징 개수 (기술적 지표 개수)
            hidden_size: LSTM 히든 레이어 크기
            num_layers: LSTM 레이어 개수
            dropout: 드롭아웃 비율
            output_size: 출력 크기 (기본: 1 = 가격 예측)
        """
        super(PricePredictionLSTM, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.output_size = output_size

        # LSTM Layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=False
        )

        # Batch Normalization
        self.batch_norm = nn.BatchNorm1d(hidden_size)

        # Fully Connected Layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)

        # 가중치 초기화
        self._init_weights()

        logger.info(
            f"LSTM Model initialized:\n"
            f"  Input size: {input_size}\n"
            f"  Hidden size: {hidden_size}\n"
            f"  Num layers: {num_layers}\n"
            f"  Dropout: {dropout}\n"
            f"  Total parameters: {self.count_parameters():,}"
        )

    def _init_weights(self):
        """가중치 초기화 (Xavier Uniform)"""
        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.zeros_(param)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        순전파

        Args:
            x: (batch_size, sequence_length, input_size)

        Returns:
            predictions: (batch_size, output_size)
        """
        batch_size = x.size(0)

        # LSTM forward
        # lstm_out: (batch, seq_len, hidden_size)
        # h_n, c_n: (num_layers, batch, hidden_size)
        lstm_out, (h_n, c_n) = self.lstm(x)

        # 마지막 타임스텝의 출력 사용
        # last_output: (batch, hidden_size)
        last_output = lstm_out[:, -1, :]

        # Batch Normalization
        # (batch, hidden) → (batch, hidden) for BatchNorm1d
        normalized = self.batch_norm(last_output)

        # Fully Connected Layers
        fc1_out = self.fc1(normalized)
        fc1_out = self.relu(fc1_out)
        fc1_out = self.dropout_fc(fc1_out)

        # 최종 출력
        predictions = self.fc2(fc1_out)

        return predictions

    def count_parameters(self) -> int:
        """학습 가능한 파라미터 개수 계산"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_model_summary(self) -> str:
        """모델 요약 정보"""
        summary = [
            "=" * 60,
            "LSTM Model Architecture",
            "=" * 60,
            f"Input Size:        {self.input_size}",
            f"Hidden Size:       {self.hidden_size}",
            f"Num Layers:        {self.num_layers}",
            f"Dropout:           {self.dropout}",
            f"Output Size:       {self.output_size}",
            "-" * 60,
            f"Total Parameters:  {self.count_parameters():,}",
            "=" * 60
        ]
        return "\n".join(summary)


class BidirectionalLSTM(nn.Module):
    """
    양방향 LSTM 모델 (더 높은 정확도, 더 느린 추론)

    Bidirectional LSTM은 과거와 미래를 모두 참조하므로
    실시간 예측보다는 백테스팅에 적합합니다.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1
    ):
        super(BidirectionalLSTM, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True  # 양방향
        )

        # Batch Normalization (hidden_size * 2 because bidirectional)
        self.batch_norm = nn.BatchNorm1d(hidden_size * 2)

        # FC Layers
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size)
        self.relu = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # LSTM forward
        lstm_out, _ = self.lstm(x)

        # 마지막 타임스텝
        last_output = lstm_out[:, -1, :]

        # Batch Norm
        normalized = self.batch_norm(last_output)

        # FC Layers
        fc1_out = self.fc1(normalized)
        fc1_out = self.relu(fc1_out)
        fc1_out = self.dropout_fc(fc1_out)

        predictions = self.fc2(fc1_out)

        return predictions


class AttentionLSTM(nn.Module):
    """
    Attention Mechanism을 추가한 LSTM 모델

    중요한 시간 스텝에 더 많은 가중치를 부여하여
    예측 정확도를 향상시킵니다.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1
    ):
        super(AttentionLSTM, self).__init__()

        self.hidden_size = hidden_size

        # LSTM
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Attention Layer
        self.attention = nn.Linear(hidden_size, 1)

        # FC Layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)

    def attention_net(self, lstm_output: torch.Tensor) -> torch.Tensor:
        """
        Attention Mechanism

        Args:
            lstm_output: (batch, seq_len, hidden_size)

        Returns:
            context_vector: (batch, hidden_size)
        """
        # Attention scores: (batch, seq_len, 1)
        attention_scores = self.attention(lstm_output)

        # Softmax to get attention weights: (batch, seq_len, 1)
        attention_weights = torch.softmax(attention_scores, dim=1)

        # Context vector: weighted sum
        # (batch, seq_len, hidden_size) * (batch, seq_len, 1) → (batch, hidden_size)
        context_vector = torch.sum(lstm_output * attention_weights, dim=1)

        return context_vector

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # LSTM
        lstm_out, _ = self.lstm(x)

        # Attention
        context_vector = self.attention_net(lstm_out)

        # FC Layers
        fc1_out = self.fc1(context_vector)
        fc1_out = self.relu(fc1_out)
        fc1_out = self.dropout_fc(fc1_out)

        predictions = self.fc2(fc1_out)

        return predictions


# =======================
# 모델 선택 함수
# =======================

def create_model(
    input_size: int,
    model_type: str = "standard",
    hidden_size: int = 128,
    num_layers: int = 3,
    dropout: float = 0.2
) -> nn.Module:
    """
    모델 타입에 따라 LSTM 모델 생성

    Args:
        input_size: 입력 특징 개수
        model_type: "standard", "bidirectional", "attention"
        hidden_size: LSTM 히든 크기
        num_layers: LSTM 레이어 개수
        dropout: 드롭아웃 비율

    Returns:
        PyTorch 모델
    """
    if model_type == "standard":
        model = PricePredictionLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
    elif model_type == "bidirectional":
        model = BidirectionalLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
    elif model_type == "attention":
        model = AttentionLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    logger.info(f"✅ Created {model_type} LSTM model")

    return model


# =======================
# 사용 예시
# =======================

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 모델 생성
    model = create_model(
        input_size=20,  # 20개 기술적 지표
        model_type="standard",
        hidden_size=128,
        num_layers=3,
        dropout=0.2
    )

    print(model.get_model_summary())

    # 테스트 입력
    batch_size = 32
    sequence_length = 60
    input_features = 20

    x = torch.randn(batch_size, sequence_length, input_features)

    # 순전파
    predictions = model(x)

    print(f"\nInput shape: {x.shape}")
    print(f"Output shape: {predictions.shape}")
    print(f"Sample prediction: {predictions[0].item():.4f}")
