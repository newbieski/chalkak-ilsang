"""사진 메타데이터(RAG 파이프라인) — photos.json 읽기·쓰기와 태그·텍스트 검색을 담당한다."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PHOTOS_PATH = DATA_DIR / "photos.json"


def load_photos() -> list[dict]:
    """photos.json 을 읽어 사진 메타데이터 목록을 반환한다."""
    with open(PHOTOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_photos(photos: list[dict]) -> None:
    """사진 메타데이터 목록을 photos.json 에 통째로 다시 저장한다."""
    with open(PHOTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(photos, f, ensure_ascii=False, indent=2)


def find_by_id(photo_id: str) -> dict | None:
    """사진 ID로 메타데이터 한 건을 찾는다. 등록되지 않은 ID면 None."""
    for photo in load_photos():
        if photo["id"] == photo_id:
            return photo
    return None


def update_photo(photo_id: str, **fields) -> dict | None:
    """사진 한 건의 필드를 갱신하고 저장한다. 등록되지 않은 ID면 아무것도 하지 않고 None."""
    photos = load_photos()
    for photo in photos:
        if photo["id"] == photo_id:
            photo.update(fields)
            save_photos(photos)
            return photo
    return None


def search(
    query: str = "",
    tags: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """자연어 질의어와 태그·기간 필터로 사진을 검색한다.

    아직 인덱싱하지 않아 태그가 비어 있는 사진은 검색 대상에서 제외한다.
    query 는 태그·위치·캡션 텍스트에 부분 일치하는 만큼 점수를 매겨 정렬한다.
    """
    scored: list[tuple[int, dict]] = []
    for photo in load_photos():
        if not photo.get("tags"):
            continue
        if tags and not set(tags).issubset(set(photo["tags"])):
            continue
        if date_from and (not photo.get("taken_at") or photo["taken_at"] < date_from):
            continue
        if date_to and (not photo.get("taken_at") or photo["taken_at"] > date_to):
            continue

        score = 0
        if query:
            haystack = " ".join(
                [photo.get("location") or "", photo.get("caption") or "", " ".join(photo.get("tags", []))]
            ).lower()
            for token in query.lower().split():
                if token in haystack:
                    score += 1
            if score == 0:
                continue
        scored.append((score, photo))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [photo for _, photo in scored]
