from __future__ import annotations

import asyncio
import json
import re
import threading
from typing import AsyncIterator

from langchain_openai import ChatOpenAI

from .config import get_settings
from .vectorstore import get_vectorstore, get_qa_vectorstore, get_reranker, _l2_to_cosine

_inference_lock = threading.Lock()

_IDENTITY_PATTERNS = [
    "你是谁", "你叫什么", "你是什么",
    "who are you", "what are you", "your name",
    "介绍一下自己", "自我介绍",
]

_IDENTITY_RESPONSE = (
    "我是 **Evibot（循证）**，您的家庭医学知识助手。\n\n"
    "我基于本地循证医学教材知识库，通过智能检索为您解答各类医学健康问题。"
    "我的所有回答均以循证医学为核心理念，来源于权威医学教材资料。\n\n"
    "> **温馨提示**：我的回答仅供参考，不能替代专业医生的诊断和治疗建议。"
    "如有身体不适或紧急症状，请及时就医。"
)


def _is_identity_question(question: str) -> bool:
    lower = question.lower().strip()
    for pattern in _IDENTITY_PATTERNS:
        if pattern in lower:
            return True
    return False


SYSTEM_PROMPT = """
你是 Evibot（循证），一名专业的循证医学知识助手。你必须严格基于检索到的医学教材片段和问答知识库内容回答用户问题。

【角色定位】
- 你是循证医学知识助手，所有回答必须以检索到的权威医学资料为依据。
- 你不是医生，不能提供个性化诊断或治疗方案。
- 你的回答应体现循证医学精神：有据可依、分级推荐、明确证据等级。

【回答结构 - 必须严格遵守】
1. **概述**：先用 1-2 句话直接回答用户问题的核心要点，让用户快速获取关键信息。
2. **详细说明**：基于检索到的资料，分层次展开说明：
   - 使用二级标题(##)划分大章节，三级标题(###)划分子章节。
   - 每个要点使用 **加粗** 标记关键词，便于快速扫读。
   - 如涉及病因、症状、诊断、治疗等维度，分别用标题清晰区分。
3. **循证标注**：在引用具体医学数据或结论时，使用引用块标注来源，例如：
   > 《默沙东诊疗手册·心脏和血管疾病》第 142 页
4. **安全提示**：涉及以下情况时，必须在回答末尾添加醒目提示：
   - 诊断相关 → "⚠️ 以上信息仅供参考，不能替代专业医生的诊断。如有疑虑，请及时就医。"
   - 用药相关 → "⚠️ 用药必须在医生指导下进行，切勿自行用药。"
   - 急症相关 → "🚨 如出现紧急症状，请立即拨打 120 或前往最近的急诊。"
   - 综合情况 → "⚠️ 以上内容基于医学教材资料，仅供参考，不能替代专业医生的诊断和治疗建议。如有身体不适，请及时就医。"

【格式规范 - 必须严格遵守】
1. 使用标准中文 Markdown 格式输出，确保排版清晰可读。
2. 段落之间必须空一行分隔，禁止所有内容挤在一起。
3. 列表使用标准 Markdown 列表格式（- 或 1. 2. 3.），列表项之间空一行。
4. 重点内容使用 **加粗** 标记，引用使用 > 引用块。
5. 每个段落长度控制在 3-5 行，避免超长段落。
6. 禁止输出无意义的星号(***)或连续分隔符。
7. 医学术语首次出现时，用括号标注通俗解释，例如：心肌梗死（心脏肌肉因缺血而坏死）。

【内容约束 - 必须严格遵守】
1. 只能基于检索到的医学教材片段和问答知识库内容回答，不得编造任何医学信息。
2. 如果资料不足以回答，明确说"当前知识库资料不足以确认"，不要推测或编造。
3. 不回答与医学知识库无关的问题，礼貌说明你的专业范围。
4. 如果同时有教材资料和问答知识库内容，优先以教材资料为主干，问答内容作为补充。
5. 对于有争议的医学观点，如实呈现不同观点，并标注"医学界对此存在不同看法"。
6. 不得给出具体药物剂量建议，如资料中包含剂量信息，需注明"具体用量请遵医嘱"。
""".strip()


# ── 输出修复辅助 ────────────────────────────────────────────────


_FIX_NUMBER_LOSS = [
    # 时间量词前缺 "1": "通常 周后" → "通常1周后"
    (re.compile(r"(?<=[通常约仅不足不到])\s+(?=[周天月年日])"), " 1"),
    # "维生素 " → "维生素C" (注意替换里不加"可"，lookahead已保留)
    (re.compile(r"维生素\s+(?=可)"), "维生素C"),
    # "无C效" → "无效"
    (re.compile(r"无C效"), "无效"),
    # 孤立上标 "1" 被换行/空格环绕 "导\n1\n致" → "导致"
    (re.compile(r"([\u4e00-\u9fff])\s+1\s+([\u4e00-\u9fff])"), r"\1\2"),
    # 孤立上标 "1" 直接嵌入 "导1致" → "导致"、"对1它" → "对它"
    (re.compile(r"(导|对)1([\u4e00-\u9fff])"), r"\1\2"),
]


def _clean_output(s: str) -> str:
    """清除 HTML 标签并修复 PDF 提取时的数字丢失问题。"""
    s = re.sub(r"<[^>]+>", "", s)
    for pattern, replacement in _FIX_NUMBER_LOSS:
        s = pattern.sub(replacement, s)
    return s


def _format_docs(docs) -> str:
    blocks = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "未知资料")
        page = doc.metadata.get("page", "?")
        blocks.append(f"[资料{index}]《{source}》第 {page} 页\n{_clean_output(doc.page_content)}")
    return "\n\n".join(blocks)


def _merged_sources_payload(book_docs: list, deduped_qa: list[tuple]) -> list[dict]:
    """合并教材和问答来源的引用信息。"""
    seen: set[tuple[str, str]] = set()
    sources: list[dict] = []

    for doc in book_docs:
        source = str(doc.metadata.get("source", "未知资料"))
        page = str(doc.metadata.get("page", "?"))
        key = (source, page)
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "page": page})

    for doc, _score, _deduped in deduped_qa:
        q = doc.metadata.get("question", "")
        key = ("Huatuo-26M", q[:30])
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": "Huatuo-26M 问答库",
                "page": q[:20] + ("..." if len(q) > 20 else ""),
            })

    return sources


# ── 去重算法 ──────────────────────────────────────────────────────


def _char_ngrams(text: str, n: int = 4) -> set[str]:
    """计算文本的字符 n-gram 集合。"""
    text = text.strip()
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _jaccard_sim(a: set[str], b: set[str]) -> float:
    """计算两个集合的 Jaccard 相似度。"""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


_ZH_SENT_SPLIT = re.compile(r"(?<=[。！？；\n])|(?<=[.!?;]\s)")


def _split_sentences(text: str) -> list[str]:
    """中英文混合分句。"""
    parts = _ZH_SENT_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 4]


def _deduplicate_qa_against_books(
    qa_answer: str,
    book_contents: list[str],
    threshold: float = 0.35,
) -> str:
    """从 QA 回答中移除与教材内容重复的句子。

    算法：对 QA 回答逐句与教材每句做字符 4-gram Jaccard 相似度比较，
    取最大相似度，超过阈值的句子视为重复，予以剔除。
    """
    book_sent_ngrams: list[set[str]] = []
    for content in book_contents:
        for sent in _split_sentences(content):
            ng = _char_ngrams(sent)
            if ng:
                book_sent_ngrams.append(ng)

    if not book_sent_ngrams:
        return qa_answer

    kept: list[str] = []
    for sent in _split_sentences(qa_answer):
        sent_ng = _char_ngrams(sent)
        if not sent_ng:
            continue
        max_sim = max(_jaccard_sim(sent_ng, bng) for bng in book_sent_ngrams)
        if max_sim < threshold:
            kept.append(sent)

    return "".join(kept)


# ── 检索 ──────────────────────────────────────────────────────────


def _deduplicate_docs(
    docs: list,
    threshold: float = 0.45,
) -> list:
    """对文档列表进行内容去重（保留第一个出现的内容，移除后续高相似度的）。

    使用 4-gram Jaccard 比较每对文档的内容相似度，
    超过 threshold 的视为重复，只保留第一个（通常是最相关的）。
    返回去重后列表。
    """
    deduped: list = []
    kept_ngrams: list[set[str]] = []
    for doc in docs:
        ng = _char_ngrams(doc.page_content)
        if not ng:
            deduped.append(doc)
            continue
        is_dup = False
        for kng in kept_ngrams:
            if _jaccard_sim(ng, kng) >= threshold:
                is_dup = True
                break
        if not is_dup:
            kept_ngrams.append(ng)
            deduped.append(doc)
    return deduped


def _retrieve_both_sources(
    question: str, settings
) -> tuple[list[tuple], bool, list[tuple]]:
    """同时检索教材库和问答库，在单次锁内完成以提升性能。

    返回 (book_results, is_reranked, qa_results)。
      book_results: [(Document, score), ...]
      qa_results:   [(Document, cosine_score), ...]
    """
    with _inference_lock:
        # 教材库检索
        vectorstore = get_vectorstore(settings)
        book_raw = vectorstore.similarity_search_with_score(
            question, k=settings.retrieval_k
        )

        reranker = get_reranker(settings)
        if reranker and len(book_raw) > 1:
            docs = [d for d, _ in book_raw]
            reranked = reranker.rerank(question, docs)
            book_results = reranked[: min(settings.final_k, len(reranked))]
            is_reranked = True
        else:
            book_results = book_raw[: settings.final_k]
            is_reranked = False

    # 问答库检索（独立锁，避免与教材库检索争用）
    qa_results: list[tuple] = []
    try:
        with _inference_lock:
            qa_vs = get_qa_vectorstore(settings)
            if qa_vs._collection.count() > 0:
                qa_raw = qa_vs.similarity_search_with_score(
                    question, k=settings.qa_retrieval_k
                )
                qa_results = [
                    (doc, _l2_to_cosine(score))
                    for doc, score in qa_raw
                    if _l2_to_cosine(score) >= settings.qa_similarity_threshold
                ]
    except Exception:
        pass  # QA 库不可用时静默降级

    return book_results, is_reranked, qa_results


def _is_book_relevant(top_score: float, is_reranked: bool, settings) -> bool:
    """判断教材库检索结果是否与问题真正相关。"""
    if is_reranked:
        return top_score >= settings.rerank_relevance_threshold
    return _l2_to_cosine(top_score) >= settings.qa_similarity_threshold


# ── 流式输出 ──────────────────────────────────────────────────────


async def stream_rag_answer(question: str) -> AsyncIterator[str]:
    if _is_identity_question(question):
        for char in _IDENTITY_RESPONSE:
            yield f"data: {char}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    settings = get_settings()
    loop = asyncio.get_running_loop()

    # Phase 1: 解析中 - 检索知识库
    yield "event: phase\ndata: retrieving\n\n"

    # 1. 同时检索教材库和问答库
    book_results, is_reranked, qa_results = await loop.run_in_executor(
        None, _retrieve_both_sources, question, settings
    )

    book_docs = [doc for doc, _ in book_results]
    top_score = book_results[0][1] if book_results else 0.0
    book_relevant = _is_book_relevant(top_score, is_reranked, settings)

    # 2a. 教材内部去重：移除内容高度重叠的 chunk
    if len(book_docs) > 1:
        book_docs = _deduplicate_docs(book_docs, threshold=0.45)

    # 2b. 去重：移除 QA 中与教材重复的内容
    book_contents = [doc.page_content for doc in book_docs]
    deduped_qa: list[tuple] = []  # (doc, score, deduped_answer)
    for doc, score in qa_results:
        qa_answer = doc.metadata.get("answer", "")
        deduped = _deduplicate_qa_against_books(qa_answer, book_contents)
        if deduped.strip():
            deduped_qa.append((doc, score, deduped))

    # 3. 无结果
    if not book_docs and not deduped_qa:
        yield "data: 当前知识库资料不足以确认您的问题。教材库和问答库中均未找到相关内容。\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    # Phase 2: 思考中 - 准备生成
    yield "event: phase\ndata: thinking\n\n"

    # 4. 格式化输出
    if not settings.openai_api_key:
        async for chunk in _stream_programmatic(book_docs, book_relevant, deduped_qa):
            yield chunk
    else:
        async for chunk in _stream_with_llm(
            question, book_docs, book_relevant, deduped_qa, settings
        ):
            yield chunk


# ── 无 LLM：程序化格式化 ─────────────────────────────────────────


async def _stream_programmatic(
    book_docs: list,
    book_relevant: bool,
    deduped_qa: list[tuple],
) -> AsyncIterator[str]:
    """无 LLM 时的程序化格式化输出。"""
    from collections import defaultdict

    parts: list[str] = []

    # ── 教材内容：按 (来源, 页码) 分组合并同源分段 ──
    if book_docs:
        relevance_tag = "" if book_relevant else "（相关度较低）"
        parts.append(f"### 教材资料{relevance_tag}\n\n")
        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
        for doc in book_docs:
            source = doc.metadata.get("source", "未知资料")
            page = doc.metadata.get("page", "?")
            grouped[(source, page)].append(_clean_output(doc.page_content))
        for (source, page), contents in grouped.items():
            merged = "\n\n".join(contents)
            parts.append(f"**《{source}》第 {page} 页**\n\n{merged}\n\n")

    # ── 免责提示 ──
    parts.append(
        "---\n\n> **温馨提示**：以上内容仅供参考，不能替代专业医生的诊断和治疗建议。"
        "如有身体不适，请及时就医。\n"
    )

    output = "".join(parts)
    # 使用 SSE 多行 data 格式发送，保留 \n 换行符
    for line in output.split("\n"):
        yield f"data: {line}\n"
    yield "\n"  # 事件分隔符

    # 来源
    sources = _merged_sources_payload(book_docs, deduped_qa)
    yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"

    # QA 选项（二级选择菜单）
    if deduped_qa:
        qa_options = [
            {
                "question": doc.metadata.get("question", ""),
                "answer": _clean_output(deduped),
                "disease": doc.metadata.get("disease", ""),
                "score": round(score, 4),
            }
            for doc, score, deduped in deduped_qa
        ]
        yield f"event: qa_options\ndata: {json.dumps(qa_options, ensure_ascii=False)}\n\n"

    yield "event: done\ndata: [DONE]\n\n"


# ── 有 LLM：综合 + 程序化补充 ────────────────────────────────────


async def _stream_with_llm(
    question: str,
    book_docs: list,
    book_relevant: bool,
    deduped_qa: list[tuple],
    settings,
) -> AsyncIterator[str]:
    """有 LLM 时的综合输出。LLM 负责内容综合，程序控制输出结构。"""

    # 构建 system prompt
    system = SYSTEM_PROMPT
    if not book_relevant and deduped_qa:
        system += (
            "\n\n注意：教材库中未找到与用户问题高度相关的资料，"
            "但问答知识库中有相关内容。请优先基于问答知识库的内容回答，"
            "同时说明教材库资料不足，并提示不能替代医生面诊。"
        )
    elif not book_relevant:
        system += (
            "\n\n注意：教材库和问答库中均未找到高度相关的资料。"
            "请如实告知当前知识库资料不足以确认。"
        )

    # 构建上下文：教材 + 去重后的 QA
    context_parts = []
    if book_docs:
        context_parts.append("## 教材资料\n\n" + _format_docs(book_docs))
    if deduped_qa:
        qa_text = "\n\n".join(
            f"**相似问题**：{doc.metadata.get('question', '')}\n**参考回答**：{_clean_output(deduped)}"
            for doc, _score, deduped in deduped_qa
        )
        context_parts.append("## 问答知识库补充（已去重）\n\n" + qa_text)

    context = "\n\n".join(context_parts)

    messages = [
        ("system", system),
        (
            "human",
            "请严格基于以下医学资料回答问题，不要编造资料中没有的内容。\n\n"
            f"问题：{question}\n\n{context}\n\n"
            "请按照以下结构回答：\n"
            "1. 先用 1-2 句话概述核心答案\n"
            "2. 基于资料分层次详细说明\n"
            "3. 引用资料时标注来源\n"
            "4. 根据内容类型添加相应的安全提示"
        ),
    ]

    llm = ChatOpenAI(
        model=settings.chat_model,
        temperature=0.1,
        streaming=True,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    # Phase 3: 输出中 - LLM 生成
    yield "event: phase\ndata: generating\n\n"

    # 流式输出 LLM 回答
    try:
        async for chunk in llm.astream(messages):
            token = chunk.content or ""
            if token:
                yield f"data: {token}\n\n"
    except Exception as e:
        yield f"data: ⚠️ 大模型服务调用失败（{type(e).__name__}），已降级至本地知识库检索模式。\n\n"
        # 降级到程序化输出
        async for fallback in _stream_programmatic(book_docs, book_relevant, deduped_qa):
            yield fallback
        return

    # 来源
    sources = _merged_sources_payload(book_docs, deduped_qa)
    yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"

    # QA 选项（二级选择菜单）
    if deduped_qa:
        qa_options = [
            {
                "question": doc.metadata.get("question", ""),
                "answer": _clean_output(deduped),
                "disease": doc.metadata.get("disease", ""),
                "score": round(score, 4),
            }
            for doc, score, deduped in deduped_qa
        ]
        yield f"event: qa_options\ndata: {json.dumps(qa_options, ensure_ascii=False)}\n\n"

    yield "event: done\ndata: [DONE]\n\n"
