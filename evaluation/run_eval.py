"""test_queries.csv 인-아웃 세트로 에이전트를 실행해 채점하는 스크립트."""

import argparse
import csv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from src.agent import ask  # noqa: E402

CSV_PATH = Path(__file__).resolve().parent / "test_queries.csv"


def _split(value: str) -> list[str]:
    """세미콜론으로 구분된 필드를 리스트로 쪼갠다."""
    return [v.strip() for v in value.split(";") if v.strip()]


def load_cases() -> list[dict]:
    """test_queries.csv 를 읽어 문항 목록을 반환한다."""
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def grade_case(case: dict) -> dict:
    """문항 하나를 에이전트로 실행하고, expected_tools·forbidden 기준으로 채점한다.

    expected_traits 는 자동 채점이 어려워 사람이 보도록 답변과 나란히 남긴다
    (MINIPJT.md 4-4 규약).
    """
    result = ask(case["input"])
    answer = result["answer"]
    called_tools = {step["step"] for step in result["trace"]}

    reasons = []
    passed = True

    expected_tools = _split(case.get("expected_tools", ""))
    if expected_tools:
        missing = [t for t in expected_tools if t not in called_tools]
        if missing:
            passed = False
            reasons.append(f"기대한 도구 안 불림: {', '.join(missing)}")

    forbidden = _split(case.get("forbidden", ""))
    hit = [f for f in forbidden if f in answer]
    if hit:
        passed = False
        reasons.append(f"금지 표현 발견: {', '.join(hit)}")

    return {
        **case,
        "answer": answer,
        "called_tools": ", ".join(sorted(called_tools)),
        "passed": passed,
        "reasons": "; ".join(reasons) if reasons else "",
    }


def run(limit: int | None = None) -> list[dict]:
    """문항을 채점하고 결과 목록을 반환한다. limit 을 주면 앞에서부터 그만큼만 돈다."""
    cases = load_cases()
    if limit:
        cases = cases[:limit]
    return [grade_case(case) for case in cases]


def summarize(results: list[dict]) -> str:
    """카테고리별·전체 통과율과 문항별 결과를 마크다운으로 만든다."""
    lines = ["# 자체 평가 결과", ""]
    total = len(results)
    total_passed = sum(r["passed"] for r in results)
    lines.append(f"전체 통과율: {total_passed} / {total}")
    lines.append("")

    categories = sorted({r["category"] for r in results})
    lines.append("## 카테고리별 통과율")
    for cat in categories:
        rows = [r for r in results if r["category"] == cat]
        passed = sum(r["passed"] for r in rows)
        lines.append(f"- {cat}: {passed} / {len(rows)}")
    lines.append("")

    lines.append("## 문항별 결과")
    lines.append("| id | category | 통과 | 사유 | expected_traits | answer |")
    lines.append("|---|---|---|---|---|---|")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        answer_preview = r["answer"].replace("\n", " ")[:80]
        lines.append(
            f"| {r['id']} | {r['category']} | {mark} | {r['reasons']} | "
            f"{r['expected_traits']} | {answer_preview} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="test_queries.csv 채점 스크립트")
    parser.add_argument("--limit", type=int, default=None, help="앞에서부터 N건만 채점 (스로틀링 테스트용)")
    parser.add_argument("--out", type=str, default=None, help="결과를 저장할 파일 경로")
    args = parser.parse_args()

    results = run(limit=args.limit)
    report = summarize(results)
    print(report)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\n저장됨: {args.out}")
