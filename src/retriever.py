"""사진 메타데이터(RAG 파이프라인) — photos.json 읽기·쓰기와 태그·텍스트·의미 검색을 담당한다."""

import json
import math
from pathlib import Path

from .embeddings import embed_text

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PHOTOS_PATH = DATA_DIR / "photos.json"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SEMANTIC_MATCH_THRESHOLD = 0.25


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


def _photo_text(photo: dict) -> str:
    """임베딩에 쓸 사진 대표 텍스트를 만든다 (태그 + 캡션)."""
    parts = list(photo.get("tags") or [])
    if photo.get("caption"):
        parts.append(photo["caption"])
    return " ".join(parts)


def cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    """두 벡터의 코사인 유사도를 구한다. 벡터가 없으면 0을 반환한다."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def reembed(photo_id: str) -> dict | None:
    """사진의 태그·캡션을 기반으로 의미 검색용 임베딩을 다시 계산해 저장한다.

    index_photos 로 태그가 생기거나 generate_caption 으로 캡션이 생길 때마다 호출한다.
    태그·캡션이 둘 다 없으면 임베딩도 비운다.
    """
    photo = find_by_id(photo_id)
    if photo is None:
        return None
    text = _photo_text(photo)
    vector = embed_text(text) if text else None
    return update_photo(photo_id, embedding=vector)


def sync_new_photos() -> list[dict]:
    """`data/` 밑에 있지만 photos.json 에 등록 안 된 이미지 파일을 찾아 최소 항목으로 등록한다.

    업로드 기능이 없는 지금은 사용자가 파일을 폴더에 직접 넣는 방식이라, photos.json 을
    손으로 고치지 않아도 목록에 뜨도록 하기 위한 것. 새로 등록된 항목만 반환한다.
    """
    photos = load_photos()
    known_filenames = {p["filename"] for p in photos}

    max_num = 0
    for photo in photos:
        pid = photo["id"]
        if pid.startswith("p") and pid[1:].isdigit():
            max_num = max(max_num, int(pid[1:]))

    new_entries = []
    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        if path.name in known_filenames:
            continue
        max_num += 1
        new_entries.append(
            {
                "id": f"p{max_num:03d}",
                "filename": path.name,
                "taken_at": None,
                "location": None,
                "tags": [],
                "caption": None,
                "caption_tone": None,
            }
        )

    if new_entries:
        photos.extend(new_entries)
        save_photos(photos)
    return new_entries


def search(
    query: str = "",
    tags: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """자연어 질의어와 태그·기간 필터로 사진을 검색한다 (키워드 + 의미 검색 하이브리드).

    아직 인덱싱하지 않아 태그가 비어 있는 사진은 검색 대상에서 제외한다.
    tags(태그 필터)는 정확히 일치하는지만 본다. query(자연어 질의)는 임베딩 코사인
    유사도를 기본 점수로 삼고, 글자 그대로 겹치는 단어가 있으면 소폭 가산해 합산 점수가
    SEMANTIC_MATCH_THRESHOLD 이상일 때만 포함한다 — 짧은 질의("해질녘 다리")는 그
    자체만으론 유사도가 낮게 나오는 경향이 있어 키워드 가산이 이를 보완해준다.
    검색이 완벽하게 정밀하진 않을 수 있는데(예: "겨울"만 겹쳐도 약간 걸림), 최종적으로
    맞는 사진인지는 에이전트가 결과를 보고 판단한다 — 검색은 후보를 넓게 잡아주는 역할.
    """
    query_vector = embed_text(query) if query else None

    scored: list[tuple[float, dict]] = []
    for photo in load_photos():
        if not photo.get("tags"):
            continue
        if tags and not set(tags).issubset(set(photo["tags"])):
            continue
        if date_from and (not photo.get("taken_at") or photo["taken_at"] < date_from):
            continue
        if date_to and (not photo.get("taken_at") or photo["taken_at"] > date_to):
            continue

        score = 0.0
        if query:
            score = cosine_similarity(query_vector, photo.get("embedding"))

            haystack = " ".join(
                [photo.get("location") or "", photo.get("caption") or "", " ".join(photo.get("tags", []))]
            ).lower()
            for token in query.lower().split():
                if token in haystack:
                    score += 0.1  # 짧은 질의의 낮은 유사도를 보완하는 가산점

            if score < SEMANTIC_MATCH_THRESHOLD:
                continue

        scored.append((score, photo))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [photo for _, photo in scored]
