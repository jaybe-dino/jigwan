"""엔진 CLI — 주소 하나를 감정해 UI 데이터(JSON)를 stdout으로 출력.

Next.js API 라우트가 child_process로 호출한다.

    python3 engine_cli.py "서울 마포구 월드컵로 212"

API 키(KAKAO_REST_KEY 등)가 있으면 실주소를 감정하고, 없으면 픽스처로 폴백한다.
"""

import json
import sys

from web.render import build_from_address


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "주소를 입력하세요"}, ensure_ascii=False))
        return 2
    address = sys.argv[1]
    try:
        data = build_from_address(address)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
