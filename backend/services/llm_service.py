from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, CHUNK_SIZE

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

SUMMARIZE_SYSTEM = (
    "你是一名专业的学术论文分析助手。请对用户提供的论文内容生成一份结构化的中文摘要总结。"
    "摘要应包含以下部分：\n"
    "## 研究背景\n## 研究方法\n## 主要发现\n## 结论与意义\n\n"
    "请使用 Markdown 格式输出，语言简洁准确。"
)

TRANSLATE_SYSTEM = (
    "你是一名专业的学术论文翻译助手。请将用户提供的英文论文段落翻译为准确、流畅的中文。"
    "保持学术用语的专业性。直接输出翻译结果，不要添加额外解释。"
)


def _chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks that respect paragraph boundaries."""
    paragraphs = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) > size and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += len(para)

    if current:
        chunks.append("\n".join(current))
    return chunks


async def stream_summarize(text: str) -> AsyncGenerator[str, None]:
    """Stream a summary of the given text."""
    chunks = _chunk_text(text)
    if len(chunks) == 1:
        content = text
    else:
        content = (
            f"以下是一篇论文的全文，分为 {len(chunks)} 个部分。"
            "请综合所有部分生成完整的结构化摘要。\n\n"
            + "\n\n---\n\n".join(
                f"【第 {i+1} 部分】\n{chunk}" for i, chunk in enumerate(chunks)
            )
        )

    stream = await client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SUMMARIZE_SYSTEM},
            {"role": "user", "content": content},
        ],
        stream=True,
        temperature=0.3,
        max_tokens=4096,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def stream_translate(paragraphs: list[str]) -> AsyncGenerator[str, None]:
    """Stream translation of paragraphs, yielding JSON events."""
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue

        translated_parts: list[str] = []
        stream = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": TRANSLATE_SYSTEM},
                {"role": "user", "content": para},
            ],
            stream=True,
            temperature=0.3,
            max_tokens=4096,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                translated_parts.append(delta.content)
                event = {
                    "type": "chunk",
                    "index": i,
                    "content": delta.content,
                }
                yield json.dumps(event, ensure_ascii=False)

        event_done = {
            "type": "paragraph_done",
            "index": i,
            "original": para,
            "translated": "".join(translated_parts),
        }
        yield json.dumps(event_done, ensure_ascii=False)

    yield json.dumps({"type": "done"}, ensure_ascii=False)
