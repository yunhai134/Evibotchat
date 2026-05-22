from __future__ import annotations

import json
from typing import AsyncIterator

from langchain_openai import ChatOpenAI

from .config import get_settings
from .vectorstore import get_vectorstore, get_reranker, search_qa_suggestions

SYSTEM_PROMPT = """
你是医学知识库问答助手，只能基于检索到的医学教材片段回答。
要求：
1. 如果资料不足以回答，明确说"当前知识库资料不足以确认"，不要编造。
2. 回答应结构清晰，尽量使用中文 Markdown。
3. 涉及诊断、用药、治疗方案时必须提示：不能替代医生面诊，实际处置需由执业医师结合病情决定。
4. 不回答与医学教材知识库无关的问题。
""".strip()


def _format_docs(docs) -> str:
    blocks = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "未知资料")
        page = doc.metadata.get("page", "?")
        blocks.append(f"[资料{index}]《{source}》第 {page} 页\n{doc.page_content}")
    return "\n\n".join(blocks)


def _sources_payload(docs) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    sources = []
    for doc in docs:
        source = str(doc.metadata.get("source", "未知资料"))
        page = str(doc.metadata.get("page", "?"))
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append({"source": source, "page": page})
    return sources


def _retrieve_and_rerank(question: str, settings) -> list[tuple[object, float]]:
    """向量检索 → 可选 Rerank 重排序，返回 (文档, 分数) 列表。"""
    vectorstore = get_vectorstore(settings)
    candidate_k = settings.retrieval_k
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=candidate_k)

    reranker = get_reranker(settings)
    if reranker and len(docs_with_scores) > 1:
        docs = [doc for doc, _ in docs_with_scores]
        reranked = reranker.rerank(question, docs)
        final_k = min(settings.final_k, len(reranked))
        return reranked[:final_k]
    return docs_with_scores[: settings.final_k]


async def stream_rag_answer(question: str) -> AsyncIterator[str]:
    settings = get_settings()

    # 向量检索 + 可选 Rerank
    docs_with_scores = _retrieve_and_rerank(question, settings)
    docs = [doc for doc, _ in docs_with_scores]

    if not docs:
        yield "event: token\n"
        yield "data: 当前知识库资料不足以确认。请先运行向量库构建脚本，或检查医学资料目录。\n\n"
        yield "event: done\n"
        yield "data: [DONE]\n\n"
        return

    # 检查教材库检索分数 —— 若最高分低于阈值，从 Huatuo-26M 找相似问题推荐
    top_score = docs_with_scores[0][1] if docs_with_scores else 0.0
    suggestion = None
    if top_score < settings.qa_similarity_threshold:
        qa_results = search_qa_suggestions(question, settings=settings)
        if qa_results:
            best_doc, best_score = qa_results[0]
            suggestion = {
                "question": best_doc.metadata.get("question", ""),
                "score": round(best_score, 4),
                "disease": best_doc.metadata.get("disease", ""),
            }

    if not settings.openai_api_key:
        preview = docs[0].page_content[:900]
        fallback = (
            "当前未配置 OPENAI_API_KEY，已返回最相关教材片段供联调：\n\n"
            f"> {preview}\n\n"
            "配置后端 `.env` 后即可启用大模型基于知识库生成回答。"
        )
        for char in fallback:
            yield f"data: {char}\n\n"
        if suggestion:
            yield (
                f"event: suggestion\ndata: {json.dumps(suggestion, ensure_ascii=False)}\n\n"
            )
        yield f"event: sources\ndata: {json.dumps(_sources_payload(docs), ensure_ascii=False)}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    llm = ChatOpenAI(
        model=settings.chat_model,
        temperature=0.2,
        streaming=True,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    # 如果存在推荐问题，在 system prompt 中添加提示，让 LLM 引导用户
    system = SYSTEM_PROMPT
    if suggestion:
        hint = "您是不是想问：『{}』？".format(suggestion["question"])
        system += (
            "\n\n注意：教材库中可能没有完全匹配您问题的资料。"
            "下面是一个与您问题相似的已知问题，请先判断用户是否想问这个，"
            "如果是，可以引导用户：{}"
            "如果不是，请如实告知当前教材库资料不足。"
        ).format(hint)

    messages = [
        ("system", system),
        (
            "human",
            "请基于以下医学教材资料回答问题。\n\n"
            f"问题：{question}\n\n"
            f"医学教材资料：\n{_format_docs(docs)}",
        ),
    ]

    async for chunk in llm.astream(messages):
        token = chunk.content or ""
        if token:
            yield f"data: {token}\n\n"

    if suggestion:
        yield (
            f"event: suggestion\ndata: {json.dumps(suggestion, ensure_ascii=False)}\n\n"
        )
    yield f"event: sources\ndata: {json.dumps(_sources_payload(docs), ensure_ascii=False)}\n\n"
    yield "event: done\ndata: [DONE]\n\n"
