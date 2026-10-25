"""Haqiqiy HTTP: lokal DEV to‘liq test oqimi (24 savol + natija)."""
from __future__ import annotations

import re
import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8788"
WEBAPP_ONLY = "true"


def _hidden(html: str, name: str) -> str:
    m = re.search(rf'name="{re.escape(name)}"\s+value="([^"]+)"', html)
    if not m:
        raise AssertionError(f"{name} topilmadi")
    return m.group(1)


def _option_ids(html: str) -> list[str]:
    ids = re.findall(r'name="option_id"\s+value="(\d+)"', html)
    if not ids:
        raise AssertionError("option_id yo‘q")
    return ids


def main() -> None:
    c = httpx.Client(base_url=BASE, follow_redirects=False, timeout=60.0, headers={"Host": "127.0.0.1:8788"})

    root = c.get("/")
    print("GET /", root.status_code, root.headers.get("location"))
    assert root.status_code == 303
    assert root.headers["location"] == "/personality/instructions"

    ins = c.get("/personality/instructions")
    print("GET instructions", ins.status_code)
    assert ins.status_code == 200
    assert "Telegram" not in ins.text or "webapp_only" not in ins.text.lower()

    start = c.post("/personality/start", data={"gender": "male"})
    assert start.status_code == 303
    intent = c.post("/personality/intent", data={"intent": "curiosity"})
    assert intent.status_code == 303
    token = intent.headers["location"].split("/test/")[1].split("?")[0]
    print("token", token)

    q = 0
    while True:
        page = c.get(f"/personality/test/{token}?q={q}")
        assert page.status_code == 200, (q, page.status_code, page.text[:300])
        ans = c.post(
            f"/personality/test/{token}/answer",
            data={
                "question_id": _hidden(page.text, "question_id"),
                "option_id": _option_ids(page.text)[0],
                "question_index": _hidden(page.text, "question_index"),
            },
        )
        assert ans.status_code == 303, (q, ans.status_code)
        loc = ans.headers["location"]
        if loc.endswith("/loading"):
            break
        q += 1
        assert q < 30, "savollar tugamadi"

    print("answered", q + 1, "questions")
    load = c.get(f"/personality/result/{token}/loading")
    assert load.status_code == 200
    result = c.get(f"/personality/result/{token}", follow_redirects=True)
    print("GET result (follow all)", result.status_code, str(result.url))
    assert result.status_code == 200, result.text[:500]
    assert "initData" not in result.text
    print("OK full HTTP flow without Telegram initData")


if __name__ == "__main__":
    main()
