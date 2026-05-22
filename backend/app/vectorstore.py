from __future__ import annotations

# =============================================================================
# 数据来源与版权声明
# =============================================================================
# 医学知识库（PDF 教材）：
#   内容来源于默沙东诊疗手册（MSD Manuals）
#   https://www.msdmanuals.cn/home/content/permissions
#   Copyright © Merck & Co., Inc., Rahway, NJ, USA 及其附属公司。
#   保留所有权利。在美国和加拿大以外的地区被称为默沙东。
#
# 问答对数据集：
#   Huatuo-26M-Lite (FreedomIntelligence/Huatuo26M-Lite)
#   @misc{li2023huatuo26m,
#         title={Huatuo-26M, a Large-scale Chinese Medical QA Dataset},
#         author={Jianquan Li and Xidong Wang and Xiangbo Wu and Zhiyi Zhang
#                 and Xiaolong Xu and Jie Fu and Prayag Tiwari and Xiang Wan
#                 and Benyou Wang},
#         year={2023}, eprint={2305.01526}, archivePrefix={arXiv},
#         primaryClass={cs.CL}}
#
# 向量化模型：BAAI/bge-m3 (MIT License)
#   https://huggingface.co/BAAI/bge-m3
# 重排序模型：BAAI/bge-reranker-v2-m3 (MIT License)
#   https://huggingface.co/BAAI/bge-reranker-v2-m3
# =============================================================================

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterable

# 禁用 ChromaDB 遥测（避免 posthog 版本不兼容导致的 capture() 报错）
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import pdfplumber

# 必须在 torch 之前加载 sentence_transformers（避免 DLL 加载顺序冲突）
from sentence_transformers import SentenceTransformer  # noqa: E402

# 必须先加载 torch CUDA，再加载 chromadb（避免 Windows DLL 加载顺序冲突）
import torch  # noqa: F401

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
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


_embeddings_instance = None
_vectorstore_instance = None
_qa_vectorstore_instance = None
EMBEDDING_DIM = 1024  # BGE-M3 固定维度
_TRACKER_FILENAME = "vector_index_tracker.json"


class SentenceTransformerEmbeddings(Embeddings):
    """使用 sentence_transformers 直接加载模型（绕过 langchain_huggingface 的兼容性问题）。"""

    def __init__(self, model_name: str, device: str = "cpu"):
        self._model = SentenceTransformer(model_name, device=device)

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


def _get_tracker_path(settings: Settings) -> Path:
    return settings.resolved_chroma_dir / _TRACKER_FILENAME


def _load_tracker(settings: Settings) -> dict[str, float]:
    path = _get_tracker_path(settings)
    if path.exists():
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_tracker(tracker: dict[str, float], settings: Settings):
    import json
    path = _get_tracker_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def _is_file_processed(pdf_path: Path, tracker: dict[str, float]) -> bool:
    abs_path = str(pdf_path.resolve())
    last_modified = pdf_path.stat().st_mtime
    tracked_mtime = tracker.get(abs_path)
    return tracked_mtime is not None and abs(tracked_mtime - last_modified) < 1.0


def _mark_file_processed(pdf_path: Path, tracker: dict[str, float]):
    abs_path = str(pdf_path.resolve())
    tracker[abs_path] = pdf_path.stat().st_mtime


def build_embeddings(settings: Settings | None = None):
    global _embeddings_instance
    if _embeddings_instance is not None:
        return _embeddings_instance
    settings = settings or get_settings()
    if settings.embedding_provider.lower() == "openai":
        _embeddings_instance = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    else:
        if settings.hf_endpoint:
            os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
        settings.resolved_embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        _embeddings_instance = SentenceTransformerEmbeddings(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
        )
    return _embeddings_instance


def get_vectorstore(settings: Settings | None = None) -> Chroma:
    global _vectorstore_instance
    if _vectorstore_instance is not None:
        return _vectorstore_instance
    settings = settings or get_settings()
    _vectorstore_instance = Chroma(
        collection_name=settings.collection_name,
        persist_directory=str(settings.resolved_chroma_dir),
        embedding_function=build_embeddings(settings),
    )
    return _vectorstore_instance


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(CJK_COMPAT_MAP)
    text = text.replace("\u00ad", "")
    # 修复单词间连字符换行: "com-\nmon" → "common"
    text = re.sub(r"(\w)-\s*\n\s*(?=\w)", r"\1", text)
    # 修复英文单词内部无故换行: "com\nmon" → "common"
    text = re.sub(r"(?<=[a-zA-Z])\n(?=[a-zA-Z])", "", text)
    # 修复中文后紧跟英文/数字时缺少空格: "医生对它们1" → "医生对它们 1"
    text = re.sub(r"(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])", " ", text)
    # 修复英文/数字后紧跟中文时缺少空格: "用随意性,主要根据"
    text = re.sub(r"(?<=[A-Za-z0-9)])(?=[\u4e00-\u9fff])", " ", text)
    # 中文间多余的换行合并为空格或直接移除
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s*\n\s*(?=[\u4e00-\u9fff])", "", text)
    # 统一空白字符
    text = re.sub(r"[ \t]+", " ", text)
    # 过滤噪声行
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(re.fullmatch(pattern, line, flags=re.I) for pattern in NOISE_PATTERNS):
            continue
        lines.append(line)
    # 减少连续换行
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # 修复逗号后缺空格 (中文/英文逗号)
    result = re.sub(r"(?<=[，,])(?=[^\s，,])", " ", result)
    # 移除行首行尾的多余管道符 (表格噪声)
    result = re.sub(r"^[\|]\s*", "", result, flags=re.MULTILINE)

    # ── 修复 PDF 提取中上标/引用标记导致的数字丢失 ──
    # 时间量词前缺 "1": "通常 周后" → "通常1周后", "不到 天" → "不到1天"
    result = re.sub(r"(?<=[通常约仅不足不到])\s+(?=[周天月年日])", " 1", result)
    # "维生素 " → "维生素C" (接中文助动词时)
    result = re.sub(r"维生素\s+(?=可)", "维生素C可", result)
    # 修复误插入的孤立的 "C": "无C效" → "无效"
    result = re.sub(r"无C效", "无效", result)

    return result


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
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
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
                except Exception as e:
                    print(f"  页 {page_number} 跳过: {e}", flush=True)
                    continue
    except Exception as e:
        print(f"  跳过文件: {pdf_path.name} ({e})", flush=True)


def get_pdf_sources(settings: Settings | None = None) -> list[Path]:
    """确定 PDF 来源目录列表。

    如果 knowledge_base_auto_discover 为 True 且 knowledge_base_dir 存在，
    优先自动发现其下的所有子目录；否则回退到 knowledge_dirs 配置。
    """
    settings = settings or get_settings()
    if settings.knowledge_base_auto_discover:
        discovered = settings.discovered_knowledge_dirs
        if not discovered:
            return settings.resolved_knowledge_dirs
        return discovered
    return settings.resolved_knowledge_dirs


def iter_pdf_documents(knowledge_dirs: list[Path]) -> Iterable[Document]:
    total_parsed = 0
    total_pdfs = sum(1 for d in knowledge_dirs if d.exists() for _ in d.glob("**/*.[pP][dD][fF]"))
    for root_dir in knowledge_dirs:
        if not root_dir.exists():
            raise FileNotFoundError(f"知识库目录不存在: {root_dir}")
        for pdf_path in sorted(root_dir.glob("**/*.[pP][dD][fF]")):
            total_parsed += 1
            if total_parsed % 50 == 0:
                print(f"已解析 {total_parsed}/{total_pdfs} 个 PDF", flush=True)
            yield from extract_pdf_documents(pdf_path, root_dir)
    print(f"PDF 解析完成，共 {total_parsed} 个文件", flush=True)


def iter_unprocessed_pdfs(knowledge_dirs: list[Path], tracker: dict[str, float]) -> Iterable[tuple[Path, Path]]:
    """遍历尚未处理的 PDF 文件，返回 (pdf_path, root_dir) 对。"""
    for root_dir in knowledge_dirs:
        if not root_dir.exists():
            continue
        for pdf_path in sorted(root_dir.glob("**/*.[pP][dD][fF]")):
            if not _is_file_processed(pdf_path, tracker):
                yield pdf_path, root_dir


# ── 速率限制器 ────────────────────────────────────────────────────


def _rate_limit(total: int, start_time: float, rate_per_minute: int):
    """漏桶限流：每批次写入后检查速度，超过 rate_per_minute 条/分钟时 sleep 等待。

    Args:
        total: 当前已处理的文档总数
        start_time: 启动时间（time.time）
        rate_per_minute: 目标速率上限（<=0 表示不限速）
    """
    if rate_per_minute <= 0:
        return
    expected_sec = total / rate_per_minute * 60.0
    elapsed = time.time() - start_time
    if elapsed < expected_sec:
        time.sleep(expected_sec - elapsed)


# ── 知识库构建 ────────────────────────────────────────────────────


def build_knowledge_base(batch_size: int = 64, rate_per_minute: int = 0) -> int:
    """全量重建医学教材知识库（清空后重新构建所有 PDF 的内容向量）。
    
    重建完成后自动构建索引追踪文件，后续增量更新可正常识别已处理文件。
    """
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ";", "，", ",", " ", ""],
    )
    vectorstore = get_vectorstore(settings)
    total = 0
    start_time = time.time()
    buffer: list[Document] = []
    for doc in splitter.split_documents(iter_pdf_documents(get_pdf_sources(settings))):
        buffer.append(doc)
        if len(buffer) >= batch_size:
            vectorstore.add_documents(buffer)
            total += len(buffer)
            _rate_limit(total, start_time, rate_per_minute)
            print(f"已写入向量片段: {total}", flush=True)
            buffer.clear()
    if buffer:
        vectorstore.add_documents(buffer)
        total += len(buffer)
        _rate_limit(total, start_time, rate_per_minute)
        print(f"已写入向量片段: {total}", flush=True)
    
    # 重建索引追踪
    tracker: dict[str, float] = {}
    for root_dir in get_pdf_sources(settings):
        if not root_dir.exists():
            continue
        for pdf_path in sorted(root_dir.glob("**/*.[pP][dD][fF]")):
            _mark_file_processed(pdf_path, tracker)
    _save_tracker(tracker, settings)
    print(f"索引追踪已更新: {len(tracker)} 个 PDF 文件", flush=True)
    
    return total


def build_knowledge_base_incremental(batch_size: int = 64, rate_per_minute: int = 0) -> int:
    """增量更新医学教材知识库（仅处理新增或修改过的 PDF 文件）。"""
    settings = get_settings()
    tracker = _load_tracker(settings)
    count_all = sum(1 for _ in get_pdf_sources(settings) if _.exists() for _ in _.glob("**/*.[pP][dD][fF]"))
    processed_count = len(tracker)
    print(f"当前索引追踪: {processed_count}/{count_all} 个 PDF 文件已处理", flush=True)

    unprocessed = list(iter_unprocessed_pdfs(get_pdf_sources(settings), tracker))
    if not unprocessed:
        print("没有检测到新增或修改的 PDF 文件，无需更新。", flush=True)
        return 0

    print(f"发现 {len(unprocessed)} 个未处理（新增/修改）的 PDF 文件，开始增量构建...", flush=True)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ";", "，", ",", " ", ""],
    )
    vectorstore = get_vectorstore(settings)
    total = 0
    start_time = time.time()
    buffer: list[Document] = []
    for pdf_path, root_dir in unprocessed:
        try:
            docs = list(extract_pdf_documents(pdf_path, root_dir))
            if not docs:
                continue
            for doc in splitter.split_documents(docs):
                buffer.append(doc)
                if len(buffer) >= batch_size:
                    vectorstore.add_documents(buffer)
                    total += len(buffer)
                    _rate_limit(total, start_time, rate_per_minute)
                    print(f"已写入向量片段: {total}", flush=True)
                    buffer.clear()
            _mark_file_processed(pdf_path, tracker)
        except Exception as e:
            print(f"处理失败 {pdf_path.name}: {e}", flush=True)
    if buffer:
        vectorstore.add_documents(buffer)
        total += len(buffer)
        _rate_limit(total, start_time, rate_per_minute)
        print(f"已写入向量片段: {total}", flush=True)
    _save_tracker(tracker, settings)
    print(f"索引追踪已更新: {len(tracker)}/{count_all} 个 PDF 文件", flush=True)
    return total


# ── Huatuo-26M 问答对知识库 ──────────────────────────────────────────


def get_qa_vectorstore(settings: Settings | None = None) -> Chroma:
    """获取 Huatuo-26M QA 对向量库（独立集合）。"""
    global _qa_vectorstore_instance
    if _qa_vectorstore_instance is not None:
        return _qa_vectorstore_instance
    settings = settings or get_settings()
    _qa_vectorstore_instance = Chroma(
        collection_name=settings.qa_collection_name,
        persist_directory=str(settings.resolved_chroma_dir),
        embedding_function=build_embeddings(settings),
    )
    return _qa_vectorstore_instance


def _l2_to_cosine(l2_dist: float) -> float:
    return max(0.0, 1.0 - l2_dist * l2_dist / 2.0)


def search_qa_suggestions(
    question: str,
    threshold: float | None = None,
    k: int | None = None,
    settings: Settings | None = None,
) -> list[tuple[Document, float]]:
    """在 QA 库中检索相似问题，返回 (文档, 余弦相似度) 列表。

    仅返回余弦相似度 >= threshold 的结果，按相似度降序排列。
    """
    settings = settings or get_settings()
    threshold = threshold if threshold is not None else settings.qa_similarity_threshold
    k = k or settings.qa_retrieval_k
    vectorstore = get_qa_vectorstore(settings)
    results = vectorstore.similarity_search_with_score(question, k=k)
    converted = [(doc, _l2_to_cosine(score)) for doc, score in results]
    return [(doc, score) for doc, score in converted if score >= threshold]


ITER_HUATUO_LOCAL_PATH = Path(r"C:\System_IT\Evibotchat\Huatuo-26M\data")


def iter_huatuo_documents(
    settings: Settings | None = None,
    max_pairs: int = 50000,
) -> Iterable[Document]:
    """从本地缓存或 Hugging Face 加载 Huatuo26M-Lite，生成 Document 对象。

    max_pairs: 最多处理多少条 QA 对（默认 50000）。
    优先从本地缓存加载（Huatuo-26M data 目录），
    本地不存在时从 Hugging Face 下载。
    """
    try:
        from datasets import load_dataset, load_from_disk
    except ImportError:
        raise ImportError("请安装 datasets: pip install datasets")

    # 优先从本地加载
    local_path = ITER_HUATUO_LOCAL_PATH
    if (local_path / "dataset_info.json").exists():
        print(f"从本地缓存加载数据集: {local_path}")
        dataset = load_from_disk(str(local_path))
    else:
        print("正在从 Hugging Face 加载 Huatuo26M-Lite 数据集...")
        old_endpoint = os.environ.pop("HF_ENDPOINT", None)
        try:
            dataset = load_dataset(
                "FreedomIntelligence/Huatuo26M-Lite",
                split="train",
                streaming=True,
            )
        finally:
            if old_endpoint:
                os.environ["HF_ENDPOINT"] = old_endpoint

    seen = set()
    count = 0
    for example in dataset:
        question = (example.get("question") or "").strip()
        answer = (example.get("answer") or "").strip()
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
                "department": example.get("label", ""),
                "disease": example.get("related_diseases", ""),
            },
        )
        count += 1
        if count % 5000 == 0:
            print(f"已读取 {count} 条 QA 对...")
        if count >= max_pairs:
            break
    print(f"共读取 {count} 条 QA 对。")


def build_qa_knowledge_base(batch_size: int = 128, max_pairs: int = 50000, rate_per_minute: int = 0) -> int:
    """下载 Huatuo26M-Lite 并构建 QA 对向量库。"""
    settings = get_settings()
    vectorstore = get_qa_vectorstore(settings)
    total = 0
    start_time = time.time()
    buffer: list[Document] = []
    for doc in iter_huatuo_documents(settings, max_pairs=max_pairs):
        buffer.append(doc)
        if len(buffer) >= batch_size:
            vectorstore.add_documents(buffer)
            total += len(buffer)
            _rate_limit(total, start_time, rate_per_minute)
            print(f"已写入问答对向量片段: {total}", flush=True)
            buffer.clear()
    if buffer:
        vectorstore.add_documents(buffer)
        total += len(buffer)
        _rate_limit(total, start_time, rate_per_minute)
        print(f"已写入问答对向量片段: {total}", flush=True)
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
            use_fp16=(self.device.lower() != "cpu"),
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
