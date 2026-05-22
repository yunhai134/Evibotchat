from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pdfplumber
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import Settings, get_settings

CJK_COMPAT_MAP = str.maketrans({
    "⼀": "一", "⼤": "大", "⼥": "女", "⽣": "生", "⽓": "气",
    "⽛": "牙", "⽔": "水", "⿏": "鼠", "⻅": "见", "⻜": "飞", "⻤": "鬼",
})

NOISE_PATTERNS = [
    r"默沙东诊疗手册.*", r"MSD.*Manual.*", r"打印", r"电子邮件", r"已审核/已修订.*", r"©.*",
]


def build_embeddings(settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.embedding_provider.lower() == "openai":
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    if settings.hf_endpoint:
        os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
    settings.resolved_embedding_cache_dir.mkdir(parents=True, exist_ok=True)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        cache_folder=str(settings.resolved_embedding_cache_dir),
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vectorstore(settings: Settings | None = None) -> Chroma:
    settings = settings or get_settings()
    return Chroma(
        collection_name=settings.collection_name,
        persist_directory=str(settings.resolved_chroma_dir),
        embedding_function=build_embeddings(settings),
    )


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(CJK_COMPAT_MAP)
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"(?<=[A-Za-z])\n(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+\n\s*(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(re.fullmatch(pattern, line, flags=re.I) for pattern in NOISE_PATTERNS):
            continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def table_to_markdown(table: list[list[object | None]]) -> str:
    rows = []
    max_cols = max((len(row) for row in table if row), default=0)
    if max_cols == 0:
        return ""
    for row in table:
        values = []
        for cell in (row or [])[:max_cols]:
            value = clean_text(str(cell or "")).replace("|", "\\|").replace("\n", "<br>")
            values.append(value)
        values.extend([""] * (max_cols - len(values)))
        if any(values):
            rows.append(values)
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    markdown = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * max_cols) + " |"]
    markdown.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(markdown)


def extract_pdf_documents(pdf_path: Path, root_dir: Path) -> Iterable[Document]:
    relative_path = str(pdf_path.relative_to(root_dir)) if pdf_path.is_relative_to(root_dir) else pdf_path.name
    category = root_dir.name
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            parts = []
            text = clean_text(page.extract_text(x_tolerance=1.5, y_tolerance=3) or "")
            if text:
                parts.append(text)
            table_parts = []
            for table_index, table in enumerate(page.extract_tables(), start=1):
                markdown_table = table_to_markdown(table)
                if markdown_table:
                    table_parts.append(f"表格 {table_index}:\n{markdown_table}")
            if table_parts:
                parts.append("\n\n".join(table_parts))
            content = clean_text("\n\n".join(parts))
            if len(content) < 20:
                continue
            yield Document(
                page_content=content,
                metadata={
                    "source": pdf_path.name,
                    "file_name": pdf_path.name,
                    "path": str(pdf_path),
                    "relative_path": relative_path,
                    "page": page_number,
                    "category": category,
                },
            )


def iter_pdf_documents(knowledge_dirs: list[Path]) -> Iterable[Document]:
    for root_dir in knowledge_dirs:
        if not root_dir.exists():
            raise FileNotFoundError(f"知识库目录不存在: {root_dir}")
        for pdf_path in sorted(root_dir.glob("**/*.[pP][dD][fF]")):
            yield from extract_pdf_documents(pdf_path, root_dir)


def build_knowledge_base(batch_size: int = 64) -> int:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ";", "，", ",", " ", ""],
    )
    vectorstore = get_vectorstore(settings)
    total = 0
    buffer: list[Document] = []
    for doc in splitter.split_documents(iter_pdf_documents(settings.resolved_knowledge_dirs)):
        buffer.append(doc)
        if len(buffer) >= batch_size:
            vectorstore.add_documents(buffer)
            total += len(buffer)
            print(f"已写入向量片段: {total}")
            buffer.clear()
    if buffer:
        vectorstore.add_documents(buffer)
        total += len(buffer)
        print(f"已写入向量片段: {total}")
    return total


# ── Huatuo-26M 问答对知识库 ──────────────────────────────────────────


def get_qa_vectorstore(settings: Settings | None = None) -> Chroma:
    """获取 Huatuo-26M QA 对向量库（独立集合）。"""
    settings = settings or get_settings()
    return Chroma(
        collection_name=settings.qa_collection_name,
        persist_directory=str(settings.resolved_chroma_dir),
        embedding_function=build_embeddings(settings),
    )


def search_qa_suggestions(
    question: str,
    threshold: float | None = None,
    k: int | None = None,
    settings: Settings | None = None,
) -> list[tuple[Document, float]]:
    """在 QA 库中检索相似问题，返回 (文档, 分数) 列表。

    仅返回分数 >= threshold 的结果，按分数降序排列。
    """
    settings = settings or get_settings()
    threshold = threshold if threshold is not None else settings.qa_similarity_threshold
    k = k or settings.qa_retrieval_k
    vectorstore = get_qa_vectorstore(settings)
    results = vectorstore.similarity_search_with_score(question, k=k)
    return [(doc, score) for doc, score in results if score >= threshold]


def iter_huatuo_documents(settings: Settings | None = None) -> Iterable[Document]:
    """从 Hugging Face 加载 Huatuo26M-Lite 并生成 Document 对象。"""
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("请安装 datasets: pip install datasets")

    print("正在从 Hugging Face 加载 Huatuo26M-Lite 数据集...")
    dataset = load_dataset(
        "FreedomIntelligence/Huatuo26M-Lite",
        split="train",
        streaming=True,
    )
    seen = set()
    count = 0
    for example in dataset:
        question = (example.get("questions") or "").strip()
        answer = (example.get("answers") or "").strip()
        if not question or not answer:
            continue
        dedup_key = question[:50]
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        yield Document(
            page_content=question,
            metadata={
                "source": "Huatuo-26M-Lite",
                "question": question,
                "answer": answer,
                "department": example.get("Hospital Department", "") or "",
                "disease": example.get("Related Diseases", "") or "",
            },
        )
        count += 1
        if count % 5000 == 0:
            print(f"已读取 {count} 条 QA 对...")
    print(f"共读取 {count} 条 QA 对。")


def build_qa_knowledge_base(batch_size: int = 128) -> int:
    """下载 Huatuo26M-Lite 并构建 QA 对向量库。"""
    settings = get_settings()
    vectorstore = get_qa_vectorstore(settings)
    total = 0
    buffer: list[Document] = []
    for doc in iter_huatuo_documents(settings):
        buffer.append(doc)
        if len(buffer) >= batch_size:
            vectorstore.add_documents(buffer)
            total += len(buffer)
            print(f"已写入问答对向量片段: {total}")
            buffer.clear()
    if buffer:
        vectorstore.add_documents(buffer)
        total += len(buffer)
        print(f"已写入问答对向量片段: {total}")
    return total


# ── Rerank 重排序 ─────────────────────────────────────────────────────


class Reranker:
    """跨编码器重排序器，对检索候选片段进行重新打分排序。"""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from FlagEmbedding import FlagReranker
        except ImportError:
            raise ImportError("请安装 FlagEmbedding: pip install FlagEmbedding")
        print(f"正在加载 Rerank 模型: {self.model_name}")
        self._model = FlagReranker(
            self.model_name,
            use_fp16=False,
            device=self.device,
        )
        print("Rerank 模型加载完成")

    def rerank(self, query: str, docs: list[Document]) -> list[tuple[Document, float]]:
        """对候选文档列表重新打分，返回 (文档, 分数) 列表（降序）。"""
        self._load()
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self._model.compute_score(pairs)
        scored = list(zip(docs, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


_reranker_instance: Reranker | None = None


def get_reranker(settings: Settings | None = None) -> Reranker | None:
    """获取全局单例 Reranker（未启用时返回 None）。"""
    global _reranker_instance
    if _reranker_instance is not None:
        return _reranker_instance
    settings = settings or get_settings()
    if not settings.rerank_enabled:
        return None
    os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
    _reranker_instance = Reranker(settings.rerank_model, settings.rerank_device)
    return _reranker_instance
