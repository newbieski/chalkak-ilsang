"""Bedrock 텍스트 임베딩 — 사진 태그·캡션의 의미 검색(RAG)에 쓴다."""

import os

from langchain_aws import BedrockEmbeddings

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"


def _client() -> BedrockEmbeddings:
    return BedrockEmbeddings(
        model_id=EMBEDDING_MODEL_ID,
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


def embed_text(text: str) -> list[float]:
    """텍스트 하나를 임베딩 벡터로 바꾼다."""
    return _client().embed_query(text)
