"""
API 키 암호화/복호화 시스템

Features:
- AES-256 암호화
- 환경변수 기반 암호화 키 관리
- Base64 인코딩
- 안전한 키 저장/조회
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CryptoService:
    """
    API 키 암호화 서비스

    AES-256 암호화를 사용하여 민감한 정보를 안전하게 저장
    """

    def __init__(self):
        """암호화 키 초기화"""
        self.fernet = self._get_fernet()

    def _get_fernet(self) -> Fernet:
        """
        Fernet 암호화 인스턴스 생성

        환경변수 ENCRYPTION_KEY를 사용하여 암호화 키 생성
        키가 없으면 SECRET_KEY를 기반으로 생성
        """
        try:
            # 환경변수에서 암호화 키 가져오기
            encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)

            if not encryption_key:
                # ENCRYPTION_KEY가 없으면 SECRET_KEY 기반으로 생성
                logger.warning("ENCRYPTION_KEY not found, deriving from SECRET_KEY")
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'tradingbot_salt_do_not_change',  # 고정 salt (변경 시 기존 암호화 데이터 복호화 불가)
                    iterations=100000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
            else:
                key = encryption_key.encode()

            return Fernet(key)

        except Exception as e:
            logger.error(f"Failed to initialize Fernet: {str(e)}")
            raise

    def encrypt(self, plaintext: str) -> str:
        """
        문자열 암호화

        Args:
            plaintext: 암호화할 평문 (API 키 등)

        Returns:
            Base64 인코딩된 암호문
        """
        try:
            if not plaintext:
                raise ValueError("Plaintext cannot be empty")

            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            encrypted_str = encrypted_bytes.decode()

            logger.debug(f"Encrypted data (length: {len(encrypted_str)})")
            return encrypted_str

        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        암호문 복호화

        Args:
            ciphertext: Base64 인코딩된 암호문

        Returns:
            복호화된 평문
        """
        try:
            if not ciphertext:
                raise ValueError("Ciphertext cannot be empty")

            decrypted_bytes = self.fernet.decrypt(ciphertext.encode())
            decrypted_str = decrypted_bytes.decode()

            logger.debug("Decrypted data successfully")
            return decrypted_str

        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def encrypt_api_credentials(
        self,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None
    ) -> dict:
        """
        API 자격증명 암호화

        Args:
            api_key: API 키
            api_secret: API Secret
            passphrase: OKX Passphrase (선택)

        Returns:
            암호화된 자격증명 딕셔너리
        """
        encrypted_credentials = {
            "api_key": self.encrypt(api_key),
            "api_secret": self.encrypt(api_secret)
        }

        if passphrase:
            encrypted_credentials["passphrase"] = self.encrypt(passphrase)

        logger.info("API credentials encrypted successfully")
        return encrypted_credentials

    def decrypt_api_credentials(self, encrypted_credentials: dict) -> dict:
        """
        암호화된 API 자격증명 복호화

        Args:
            encrypted_credentials: 암호화된 자격증명

        Returns:
            복호화된 자격증명
        """
        decrypted_credentials = {
            "api_key": self.decrypt(encrypted_credentials["api_key"]),
            "api_secret": self.decrypt(encrypted_credentials["api_secret"])
        }

        if "passphrase" in encrypted_credentials:
            decrypted_credentials["passphrase"] = self.decrypt(
                encrypted_credentials["passphrase"]
            )

        logger.info("API credentials decrypted successfully")
        return decrypted_credentials


# 글로벌 인스턴스
crypto_service = CryptoService()


def generate_encryption_key() -> str:
    """
    새로운 암호화 키 생성

    .env 파일에 ENCRYPTION_KEY로 저장하세요

    Returns:
        Base64 인코딩된 Fernet 키
    """
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # 암호화 키 생성 테스트
    print("=== 새로운 암호화 키 생성 ===")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print("\n⚠️ 이 키를 .env 파일에 저장하세요!")
    print("⚠️ 키를 분실하면 암호화된 데이터를 복구할 수 없습니다!")
