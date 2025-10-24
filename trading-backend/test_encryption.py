"""
데이터베이스 암호화 저장 테스트

Features:
- API 키 암호화 저장
- 복호화 및 실제 API 호출 검증
- 전체 프로세스 테스트
"""
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.crypto import crypto_service
from app.models.api_key import ApiKey
from app.services.binance import BinanceFuturesClient
from app.services.okx_client import OKXClient


def test_crypto_service():
    """암호화 서비스 기본 테스트"""
    print("\n=== 암호화 서비스 기본 테스트 ===")

    # 테스트 데이터
    test_api_key = "test_api_key_12345"
    test_secret = "test_secret_67890"
    test_passphrase = "test_passphrase"

    try:
        # 암호화
        encrypted = crypto_service.encrypt_api_credentials(
            api_key=test_api_key,
            api_secret=test_secret,
            passphrase=test_passphrase
        )

        print(f"✅ 암호화 성공")
        print(f"  - API Key 길이: {len(encrypted['api_key'])} bytes")
        print(f"  - Secret 길이: {len(encrypted['api_secret'])} bytes")
        print(f"  - Passphrase 길이: {len(encrypted['passphrase'])} bytes")

        # 복호화
        decrypted = crypto_service.decrypt_api_credentials(encrypted)

        print(f"✅ 복호화 성공")

        # 검증
        assert decrypted['api_key'] == test_api_key, "API Key 불일치"
        assert decrypted['api_secret'] == test_secret, "Secret 불일치"
        assert decrypted['passphrase'] == test_passphrase, "Passphrase 불일치"

        print(f"✅ 암호화/복호화 검증 완료")
        return True

    except Exception as e:
        print(f"❌ 암호화 서비스 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_encryption():
    """데이터베이스 암호화 저장 테스트"""
    print("\n=== 데이터베이스 암호화 저장 테스트 ===")

    # DB 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 테스트용 사용자 ID 생성
        test_user_id = "test_user_encryption"

        # 테스트 사용자 생성 (없으면)
        from app.models.user import User

        existing_user = db.query(User).filter(User.id == test_user_id).first()
        if not existing_user:
            # 간단한 더미 패스워드 사용 (bcrypt 호환성 문제 우회)
            test_user = User(
                id=test_user_id,
                email="test_encryption@test.com",
                name="Test User Encryption",
                password="$2b$12$dummy_hashed_password_for_testing",  # Pre-hashed dummy password
                total_xp=0,
                level=1,
                total_trades=0
            )
            db.add(test_user)
            db.commit()
            print(f"✅ 테스트 사용자 생성 완료: {test_user_id}")

        # 실제 API 키 암호화
        encrypted_binance = crypto_service.encrypt_api_credentials(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET
        )

        encrypted_okx = crypto_service.encrypt_api_credentials(
            api_key=settings.OKX_API_KEY,
            api_secret=settings.OKX_API_SECRET,
            passphrase=settings.OKX_PASSPHRASE
        )

        # 기존 테스트 데이터 삭제
        db.execute(text("DELETE FROM api_keys WHERE user_id = :user_id"), {"user_id": test_user_id})
        db.commit()

        # Binance API 키 저장
        binance_key = ApiKey(
            id=f"test_binance_{test_user_id}",
            user_id=test_user_id,
            exchange="binance",
            api_key=encrypted_binance['api_key'],
            api_secret=encrypted_binance['api_secret'],
            testnet=False,
            is_active=True
        )
        db.add(binance_key)

        # OKX API 키 저장
        okx_key = ApiKey(
            id=f"test_okx_{test_user_id}",
            user_id=test_user_id,
            exchange="okx",
            api_key=encrypted_okx['api_key'],
            api_secret=encrypted_okx['api_secret'],
            passphrase=encrypted_okx['passphrase'],
            testnet=False,
            is_active=True
        )
        db.add(okx_key)

        db.commit()
        print(f"✅ 암호화된 API 키 데이터베이스 저장 완료")

        # DB에서 다시 조회
        saved_binance = db.query(ApiKey).filter(ApiKey.id == binance_key.id).first()
        saved_okx = db.query(ApiKey).filter(ApiKey.id == okx_key.id).first()

        print(f"✅ 데이터베이스에서 조회 완료")
        print(f"  - Binance: {saved_binance.exchange}, Active: {saved_binance.is_active}")
        print(f"  - OKX: {saved_okx.exchange}, Active: {saved_okx.is_active}")

        # 복호화 테스트
        decrypted_binance = crypto_service.decrypt_api_credentials({
            'api_key': saved_binance.api_key,
            'api_secret': saved_binance.api_secret
        })

        decrypted_okx = crypto_service.decrypt_api_credentials({
            'api_key': saved_okx.api_key,
            'api_secret': saved_okx.api_secret,
            'passphrase': saved_okx.passphrase
        })

        print(f"✅ 복호화 완료")

        # 원본과 비교
        assert decrypted_binance['api_key'] == settings.BINANCE_API_KEY, "Binance API Key 불일치"
        assert decrypted_binance['api_secret'] == settings.BINANCE_API_SECRET, "Binance Secret 불일치"
        assert decrypted_okx['api_key'] == settings.OKX_API_KEY, "OKX API Key 불일치"
        assert decrypted_okx['api_secret'] == settings.OKX_API_SECRET, "OKX Secret 불일치"
        assert decrypted_okx['passphrase'] == settings.OKX_PASSPHRASE, "OKX Passphrase 불일치"

        print(f"✅ 복호화 검증 완료 - 원본과 일치")

        return True, decrypted_binance, decrypted_okx, binance_key.id, okx_key.id

    except Exception as e:
        print(f"❌ 데이터베이스 암호화 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False, None, None, None, None

    finally:
        db.close()


async def test_decrypted_api_calls(decrypted_binance, decrypted_okx):
    """복호화된 API 키로 실제 API 호출 테스트"""
    print("\n=== 복호화된 API 키로 실제 호출 테스트 ===")

    # Binance 테스트
    print("\n[Binance API 호출]")
    try:
        client = BinanceFuturesClient(
            api_key=decrypted_binance['api_key'],
            api_secret=decrypted_binance['api_secret'],
            testnet=False
        )

        balance = await client.get_account_balance()
        print(f"✅ Binance API 호출 성공 (복호화된 키 사용)")
        print(f"  - 잔액: {balance.get('totalWalletBalance', 0)} USDT")
        binance_ok = True

    except Exception as e:
        print(f"❌ Binance API 호출 실패: {str(e)}")
        binance_ok = False

    # OKX 테스트 (직접 HTTP 요청)
    print("\n[OKX API 호출]")
    try:
        import requests
        import hmac
        import hashlib
        import base64
        from datetime import datetime

        base_url = "https://www.okx.com"
        endpoint = "/api/v5/account/balance"
        method = "GET"

        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        message = timestamp + method + endpoint
        mac = hmac.new(
            decrypted_okx['api_secret'].encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        )
        signature = base64.b64encode(mac.digest()).decode("utf-8")

        headers = {
            "OK-ACCESS-KEY": decrypted_okx['api_key'],
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": decrypted_okx['passphrase'],
            "Content-Type": "application/json"
        }

        response = requests.get(base_url + endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == "0":
            print(f"✅ OKX API 호출 성공 (복호화된 키 사용)")
            okx_ok = True
        else:
            print(f"⚠️ OKX 응답: {result}")
            okx_ok = False

    except Exception as e:
        print(f"❌ OKX API 호출 실패: {str(e)}")
        okx_ok = False

    return binance_ok and okx_ok


def cleanup_test_data(binance_id, okx_id):
    """테스트 데이터 정리"""
    print("\n=== 테스트 데이터 정리 ===")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        if binance_id:
            db.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": binance_id})
        if okx_id:
            db.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": okx_id})

        db.commit()
        print(f"✅ 테스트 데이터 삭제 완료")

    except Exception as e:
        print(f"⚠️ 테스트 데이터 정리 실패: {str(e)}")
        db.rollback()

    finally:
        db.close()


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("데이터베이스 암호화 저장 전체 프로세스 테스트")
    print("=" * 60)

    # 1. 암호화 서비스 기본 테스트
    crypto_ok = test_crypto_service()

    if not crypto_ok:
        print("\n❌ 암호화 서비스 테스트 실패 - 종료")
        sys.exit(1)

    # 2. 데이터베이스 암호화 저장 테스트
    db_ok, decrypted_binance, decrypted_okx, binance_id, okx_id = test_database_encryption()

    if not db_ok:
        print("\n❌ 데이터베이스 암호화 테스트 실패 - 종료")
        sys.exit(1)

    # 3. 복호화된 키로 실제 API 호출
    api_ok = await test_decrypted_api_calls(decrypted_binance, decrypted_okx)

    # 4. 테스트 데이터 정리
    cleanup_test_data(binance_id, okx_id)

    # 5. 최종 결과
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"1. 암호화 서비스: {'✅ 성공' if crypto_ok else '❌ 실패'}")
    print(f"2. 데이터베이스 저장: {'✅ 성공' if db_ok else '❌ 실패'}")
    print(f"3. API 호출 (복호화): {'✅ 성공' if api_ok else '❌ 실패'}")

    if crypto_ok and db_ok and api_ok:
        print("\n🎉 모든 암호화 저장 테스트 통과!")
        print("\n✅ 검증 완료:")
        print("  - API 키가 AES-256으로 안전하게 암호화됨")
        print("  - 데이터베이스에 암호화된 상태로 저장됨")
        print("  - 복호화하여 실제 API 호출 가능")
        print("  - 전체 프로세스 정상 작동")
        sys.exit(0)
    else:
        print("\n⚠️ 일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
