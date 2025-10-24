"""
API 연결 테스트 스크립트
Binance와 OKX API 실제 연결 테스트
"""
import sys
import asyncio
from app.core.config import settings
from app.services.binance import BinanceFuturesClient
from app.services.okx_client import OKXClient

async def test_binance():
    """Binance API 연결 테스트"""
    print("\n=== Binance API 연결 테스트 ===")
    print(f"API Key: {settings.BINANCE_API_KEY[:10]}...")
    print(f"Testnet: {settings.BINANCE_TESTNET}")

    try:
        client = BinanceFuturesClient(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=settings.BINANCE_TESTNET
        )

        # 계정 정보 조회
        balance = await client.get_account_balance()
        print(f"✅ Binance 연결 성공!")
        print(f"총 잔액: {balance.get('totalWalletBalance', 0)} USDT")
        print(f"사용 가능 잔액: {balance.get('availableBalance', 0)} USDT")
        print(f"USDT 잔액: {balance.get('usdt', {}).get('balance', 0)} USDT")

        return True
    except Exception as e:
        print(f"❌ Binance 연결 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_okx():
    """OKX API 연결 테스트"""
    import requests
    import hmac
    import hashlib
    import base64
    from datetime import datetime

    print("\n=== OKX API 연결 테스트 ===")
    print(f"API Key: {settings.OKX_API_KEY[:10]}...")
    print(f"Testnet: {settings.OKX_TESTNET}")

    try:
        # 직접 HTTP 요청 (데코레이터 우회)
        base_url = "https://www.okx.com"
        endpoint = "/api/v5/account/balance"
        method = "GET"

        # 서명 생성
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        message = timestamp + method + endpoint
        mac = hmac.new(
            settings.OKX_API_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        )
        signature = base64.b64encode(mac.digest()).decode("utf-8")

        # 헤더
        headers = {
            "OK-ACCESS-KEY": settings.OKX_API_KEY,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": settings.OKX_PASSPHRASE,
            "Content-Type": "application/json"
        }

        # 요청
        response = requests.get(base_url + endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        result_data = response.json()

        # 결과 파싱
        if result_data.get("code") == "0" and result_data.get("data"):
            data = result_data["data"]
            if len(data) > 0:
                details = data[0].get("details", [])
                usdt_detail = next(
                    (item for item in details if item["ccy"] == "USDT"),
                    {"availBal": "0", "eq": "0"}
                )

                print(f"✅ OKX 연결 성공!")
                print(f"총 자산: {usdt_detail.get('eq', 0)} USDT")
                print(f"사용 가능: {usdt_detail.get('availBal', 0)} USDT")
            else:
                print(f"✅ OKX 연결 성공! (잔액 데이터 없음)")
        else:
            print(f"⚠️ OKX 응답: {result_data}")

        return True
    except Exception as e:
        print(f"❌ OKX 연결 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 테스트 함수"""
    print("=" * 50)
    print("API 연결 테스트 시작")
    print("=" * 50)

    binance_ok = await test_binance()
    okx_ok = test_okx()  # 동기 함수로 변경

    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    print(f"Binance: {'✅ 성공' if binance_ok else '❌ 실패'}")
    print(f"OKX: {'✅ 성공' if okx_ok else '❌ 실패'}")

    if binance_ok and okx_ok:
        print("\n🎉 모든 API 연결 테스트 통과!")
        sys.exit(0)
    else:
        print("\n⚠️ 일부 API 연결 실패")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
