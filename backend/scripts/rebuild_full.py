"""全量重建入口 - 清除缓存实例后重新构建所有 PDF（GPU 加速版）。"""
import os
import sys
import time
import shutil
from pathlib import Path

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.vectorstore import (
    _vectorstore_instance,
    _embeddings_instance,
    _qa_vectorstore_instance,
    build_knowledge_base,
    iter_pdf_documents,
    get_pdf_sources,
    extract_pdf_documents,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

settings = get_settings()

# 1. 清除所有缓存实例
import app.vectorstore as vsmod
vsmod._vectorstore_instance = None
vsmod._embeddings_instance = None
vsmod._qa_vectorstore_instance = None
vsmod._reranker_instance = None

# 2. 删除 chroma_db 目录下的所有数据
chroma_dir = settings.resolved_chroma_dir
if chroma_dir.exists():
    for item in chroma_dir.iterdir():
        if item.name == "vector_index_tracker.json":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    print(f"已清空 Chroma 数据目录: {chroma_dir}")

tracker_path = chroma_dir / "vector_index_tracker.json"
if tracker_path.exists():
    tracker_path.unlink()
    print("已删除旧的索引追踪文件")

# 3. 显示知识库来源
sources = get_pdf_sources(settings)
total_pdfs = 0
csv_files = []
for d in sources:
    if d.exists():
        pdfs = sorted(d.glob("**/*.[pP][dD][fF]"))
        total_pdfs += len(pdfs)
        csv_files.extend((pdf, d) for pdf in pdfs)
        print(f"  {d.name}: {len(pdfs)} PDFs")
print(f"共 {len(sources)} 个目录，{total_pdfs} 个 PDF 文件")

# 4. 全量重建（带进度输出）
print("\n开始全量重建（GPU: CUDA 加速嵌入）...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", "。", "；", ";", "，", ",", " ", ""],
)

from app.vectorstore import get_vectorstore
vectorstore = get_vectorstore(settings)
total = 0
buffer = []
batch_size = 64
start_time = time.time()
pdf_index = 0

for pdf_path, root_dir in csv_files:
    pdf_index += 1
    try:
        docs = list(extract_pdf_documents(pdf_path, root_dir))
    except Exception as e:
        print(f"  [{pdf_index}/{total_pdfs}] 解析失败 {pdf_path.name}: {e}")
        continue
    if not docs:
        continue
    for doc in splitter.split_documents(docs):
        buffer.append(doc)
        if len(buffer) >= batch_size:
            vectorstore.add_documents(buffer)
            total += len(buffer)
            elapsed = time.time() - start_time
            rate = total / elapsed if elapsed > 0 else 0
            print(f"  已写入向量片段: {total} ({rate:.1f} chunks/s) | PDF进度: {pdf_index}/{total_pdfs}")
            buffer.clear()
    if pdf_index % 100 == 0:
        print(f"  PDF进度: {pdf_index}/{total_pdfs} (缓存 {len(buffer)} 个片段)")

if buffer:
    vectorstore.add_documents(buffer)
    total += len(buffer)
    print(f"  已写入向量片段: {total}")

elapsed = time.time() - start_time
print(f"\n全量重建完成！")
print(f"  向量片段总数: {total}")
print(f"  用时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
print(f"  平均速度: {total/elapsed:.1f} chunks/s")
print(f"  GPU 嵌入模型: bge-m3 (CUDA)")