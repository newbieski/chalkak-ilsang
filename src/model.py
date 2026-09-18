"""채팅 모델 생성.

에이전트·태깅(index_photos)은 build_chat_model 로 Bedrock만 쓰고, 스로틀링 등으로
실패하면 다음 후보 모델로 자동 전환한다. 캡션 생성(generate_caption)만
CAPTION_LLM_PROVIDER(.env)로 Bedrock/Gemini 중 선택해 build_caption_model 로 만든다.
"""

import os

from botocore.exceptions import ClientError
from langchain_aws import ChatBedrockConverse

FALLBACK_MODEL_IDS = [
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-sonnet-4-6",
    "global.anthropic.claude-sonnet-4-6",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.amazon.nova-pro-v1:0",
    "us.amazon.nova-2-lite-v1:0",
    "global.amazon.nova-2-lite-v1:0",
    "us.amazon.nova-lite-v1:0",
]


def _build_bedrock_model(**kwargs):
    """기본 모델(.env의 BEDROCK_MODEL_ID)로 시도하고, Bedrock 쪽 오류(ClientError · 스로틀링·접근거부 등)면
    FALLBACK_MODEL_IDS 순서대로 다음 모델로 자동 전환하는 모델을 반환한다.

    반환값은 ChatBedrockConverse 가 아니라 RunnableWithFallbacks 이지만, invoke()·bind_tools() 를
    그대로 지원해 create_agent 등에 동일하게 쓸 수 있다.
    """
    region = os.environ.get("AWS_REGION", "us-east-1")
    primary_id = os.environ["BEDROCK_MODEL_ID"]
    candidate_ids = [primary_id] + [m for m in FALLBACK_MODEL_IDS if m != primary_id]

    models = [ChatBedrockConverse(model=model_id, region_name=region, **kwargs) for model_id in candidate_ids]
    primary, *fallbacks = models
    return primary.with_fallbacks(fallbacks, exceptions_to_handle=(ClientError,))


def _build_gemini_model(**kwargs):
    """.env의 GEMINI_MODEL_ID·GEMINI_API_KEY로 Gemini 모델을 만든다."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL_ID"],
        google_api_key=os.environ["GEMINI_API_KEY"],
        **kwargs,
    )


def build_chat_model(**kwargs):
    """에이전트·태깅용 Bedrock 채팅 모델을 반환한다 (항상 Bedrock, 스로틀링 시 자동 전환)."""
    return _build_bedrock_model(**kwargs)


def build_caption_model(**kwargs):
    """캡션 생성용 채팅 모델을 반환한다.

    CAPTION_LLM_PROVIDER(.env, 기본값 bedrock)가 gemini 면 Gemini를, 아니면 Bedrock을 쓴다.
    """
    provider = os.environ.get("CAPTION_LLM_PROVIDER", "bedrock").strip().lower()
    if provider == "bedrock":
        return _build_bedrock_model(**kwargs)
    if provider == "gemini":
        return _build_gemini_model(**kwargs)
    raise ValueError(f"알 수 없는 CAPTION_LLM_PROVIDER: {provider!r} (bedrock 또는 gemini 중 하나여야 함)")
