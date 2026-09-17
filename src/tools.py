"""찰칵일상 도메인 도구 — index_photos, generate_caption, search_photos, get_photo."""

import base64
import json
from pathlib import Path

from botocore.exceptions import ClientError
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from . import retriever
from .model import build_chat_model

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TONES_PATH = DATA_DIR / "tones.json"


def _vision_model():
    """이미지를 보는 도구들이 공용으로 쓰는 Bedrock 모델을 만든다. 스로틀링 시 대체 모델로 자동 전환."""
    return build_chat_model(temperature=0)


def _log_usage(label: str, response) -> None:
    """모델 호출 하나의 입출력 토큰 수와 실제로 응답한 모델을 콘솔에 남긴다."""
    usage = response.usage_metadata or {}
    model_name = (response.response_metadata or {}).get("model_name", "?")
    print(
        f"[tokens] {label} model={model_name} "
        f"input={usage.get('input_tokens', 0)} output={usage.get('output_tokens', 0)}"
    )


def _load_tones() -> dict:
    """톤 프리셋과 커스텀 톤 샘플을 읽는다."""
    with open(TONES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_tones(tones: dict) -> None:
    """톤 프리셋·커스텀 톤 정보를 tones.json 에 다시 저장한다."""
    with open(TONES_PATH, "w", encoding="utf-8") as f:
        json.dump(tones, f, ensure_ascii=False, indent=2)


def load_tones() -> dict:
    """톤 프리셋·커스텀 톤 정보를 반환한다 (앱이 현재 상태를 보여줄 때 사용)."""
    return _load_tones()


def update_custom_tone_samples(samples: list[str]) -> dict:
    """사용자가 등록한 커스텀 톤 글 샘플을 저장한다.

    에이전트(모델)를 거치지 않는 앱 기능이다 (SERVICE.md 3번 참고).
    """
    tones = _load_tones()
    tones["custom"]["samples"] = samples
    _save_tones(tones)
    return tones


def _default_tone_guide(tones: dict) -> str:
    """기본 톤(프리셋 중 default=true)의 안내 문장을 반환한다."""
    preset = next(p for p in tones["presets"] if p["default"])
    return preset["guide"]


def _tone_guide(tone: str | None) -> tuple[str, str]:
    """톤 이름(프리셋 id·이름 또는 커스텀 톤 id·이름)에 맞는 (안내 문장, 실제 적용된 톤 id)를 반환한다.

    지정하지 않았거나 모르는 톤이면 기본 톤으로 되돌린다
    (SERVICE.md 4번: 사용자가 지정하지 않은 톤을 임의로 바꾸지 않는다).
    """
    tones = _load_tones()
    default_id = next(p["id"] for p in tones["presets"] if p["default"])
    if not tone:
        return _default_tone_guide(tones), default_id

    # 에이전트가 프리셋 id("emotional") 대신 한국어 이름을 어미까지 붙여
    # ("감성적", "감성적인", "감성적으로") 넘기는 경우가 많아, 정확히 일치하지 않아도
    # id·name 이 서로 부분 문자열로 포함되면 매칭한다.
    normalized = tone.strip().lower()

    def _matches(id_: str, name: str) -> bool:
        id_, name = id_.lower(), name.strip().lower()
        return normalized == id_ or name in normalized or normalized in name

    for preset in tones["presets"]:
        if _matches(preset["id"], preset["name"]):
            return preset["guide"], preset["id"]
    custom = tones["custom"]
    if _matches(custom["id"], custom["name"]) and custom["samples"]:
        samples = "\n".join(custom["samples"])
        return f"{custom['guide']}\n샘플:\n{samples}", custom["id"]
    return _default_tone_guide(tones), default_id


def _image_to_data_url(filename: str) -> str | None:
    """사진 파일을 base64 data URL로 인코딩한다. 파일이 없으면 None."""
    path = DATA_DIR / filename
    if not path.exists():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    ext = path.suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{encoded}"


@tool
def index_photos(photo_ids: list[str] | None = None) -> str:
    """저장소 사진에 기본 태그를 일괄로 붙인다.

    photo_ids 를 주면 그 사진들만, 안 주면 아직 태그가 없는 모든 사진을 대상으로 한다.
    이미지 내용과 촬영일·장소(있는 경우)를 근거로 태그를 만들고, 신뢰도가 낮은 태그는
    "(추정)" 표시를 붙여 자동 확정하지 않는다.
    """
    photos = retriever.load_photos()
    if photo_ids is not None:
        targets = [p for p in photos if p["id"] in photo_ids]
    else:
        targets = [p for p in photos if not p.get("tags")]

    if not targets:
        return "태그를 붙일 사진이 없습니다."

    model = _vision_model()
    results = []
    for photo in targets:
        data_url = _image_to_data_url(photo["filename"])
        if data_url is None:
            results.append(f"{photo['id']}: 이미지 파일이 없어 건너뜀")
            continue

        context = f"촬영일: {photo.get('taken_at') or '알 수 없음'}, 장소: {photo.get('location') or '알 수 없음'}"
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "이 사진에서 실제로 확인되는 것만 태그로 뽑아줘. 이미지에 없는 사실은 지어내지 마. "
                        "사물·활동·분위기 위주로 5개 이내 한국어 단어로 뽑아줘. "
                        "지명·장소·건물 같은 고유명사는 아래 참고 정보(메타데이터)로 확인됐거나, "
                        "누가 봐도 알아볼 만큼 명백한 유명 랜드마크일 때만 써도 되고, "
                        "그 정도로 확실하지 않으면 '공원', '바다'처럼 일반적인 표현으로만 써. "
                        "쉼표로만 구분해서 태그만 답해. 확신이 낮은 태그는 뒤에 (추정)을 붙여줘. "
                        f"참고 정보 — {context}"
                    ),
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
        )
        # 사진마다 바로 저장한다 — 뒤 사진에서 실패해도 앞서 만든 태그가 날아가지 않게 한다.
        try:
            response = model.invoke([message])
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "ThrottlingException":
                results.append(f"{photo['id']}: Bedrock 스로틀링으로 중단 — 지금까지는 저장됨, 나머지는 나중에 재시도")
                break
            results.append(f"{photo['id']}: 태그 생성 실패 ({error_code or exc})")
            continue

        _log_usage(f"index_photos {photo['id']}", response)
        tags = [t.strip() for t in str(response.content).split(",") if t.strip()]
        retriever.update_photo(photo["id"], tags=tags)
        results.append(f"{photo['id']}: {', '.join(tags)}")

    return "\n".join(results)


@tool
def generate_caption(photo_id: str, tone: str | None = None, length: str = "2문장", guide: str | None = None) -> str:
    """사진 한 장의 설명 글(캡션)을 만든다.

    tone 을 지정하지 않으면 기본 톤을 쓰고, 사용자가 지정하지 않은 톤·분량을 임의로
    바꾸지 않는다. 사용자가 "내가 등록한 톤", "내 문체"처럼 자신만의 커스텀 톤을
    가리키면 tone="my_tone" 으로 호출한다 (등록된 샘플이 없으면 자동으로 기본 톤으로
    처리된다). 등록되지 않은 사진이거나 이미지 파일이 없으면 지어내지 않고
    그 사실을 그대로 답한다.
    """
    photo = retriever.find_by_id(photo_id)
    if photo is None:
        return f"{photo_id} 사진을 찾을 수 없습니다. 등록된 사진이 아닙니다."

    data_url = _image_to_data_url(photo["filename"])
    if data_url is None:
        return f"{photo_id} 사진 파일을 찾을 수 없어 캡션을 만들 수 없습니다."

    tone_guide, resolved_tone_id = _tone_guide(tone)
    context = f"촬영일: {photo.get('taken_at') or '알 수 없음'}, 장소: {photo.get('location') or '알 수 없음'}"
    guide_line = f"\n추가 가이드: {guide}" if guide else ""
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    f"이 사진을 보고 설명 글을 {length} 분량으로 써줘. 톤 지침: {tone_guide}\n"
                    f"사진에서 실제로 확인되지 않는 사실은 넣지 마. 참고 정보 — {context}{guide_line}"
                ),
            },
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )
    response = _vision_model().invoke([message])
    _log_usage(f"generate_caption {photo_id}", response)
    caption = str(response.content).strip()

    retriever.update_photo(photo_id, caption=caption, caption_tone=resolved_tone_id)
    return caption


@tool
def search_photos(
    query: str = "", tags: list[str] | None = None, date_from: str | None = None, date_to: str | None = None
) -> str:
    """자연어 질의어와 태그·기간 필터로 사진을 찾는다.

    아직 인덱싱을 거치지 않아 태그가 없는 사진은 검색되지 않는다. 조건에 맞는 사진이
    없으면 지어내지 않고 없다고 답한다.
    """
    results = retriever.search(query=query, tags=tags, date_from=date_from, date_to=date_to)
    if not results:
        return "조건에 맞는 사진을 찾지 못했습니다."

    lines = [
        f"{photo['id']} | {photo.get('location') or '위치 알 수 없음'} | "
        f"{photo.get('taken_at') or '날짜 알 수 없음'} | 태그: {', '.join(photo.get('tags', []))}"
        for photo in results
    ]
    return "\n".join(lines)


@tool
def get_photo(photo_id: str) -> str:
    """사진 한 장의 태그·촬영정보·기존 캡션을 상세 조회한다.

    등록되지 않은 사진 ID면 지어내지 않고 없다고 답한다.
    """
    photo = retriever.find_by_id(photo_id)
    if photo is None:
        return f"{photo_id} 사진을 찾을 수 없습니다. 등록된 사진이 아닙니다."

    return (
        f"id: {photo['id']}\n"
        f"위치: {photo.get('location') or '알 수 없음'}\n"
        f"촬영일: {photo.get('taken_at') or '알 수 없음'}\n"
        f"태그: {', '.join(photo.get('tags', [])) or '(아직 인덱싱 안 됨)'}\n"
        f"캡션: {photo.get('caption') or '(아직 없음)'}"
    )
