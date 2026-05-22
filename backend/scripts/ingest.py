"""医学教材知识库向量构建脚本。

用法（必须使用 Python 3.12）：
  & "C:\Users\vo909\AppData\Local\Programs\Python\Python312\python.exe" scripts/ingest.py              # 增量更新
  & "C:\Users\vo909\AppData\Local\Programs\Python\Python312\python.exe" scripts/ingest.py --full       # 全量重建
  & "C:\Users\vo909\AppData\Local\Programs\Python\Python312\python.exe" scripts/ingest.py --info       # 显示信息
  或使用启动脚本：.\start.ps1 ingest [--full] [--info]
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.vectorstore import (
    build_knowledge_base,
    build_knowledge_base_incremental,
    get_pdf_sources,
    _load_tracker,
)
from app.config import get_settings


def show_info():
    settings = get_settings()
    sources = get_pdf_sources(settings)
    print(f"知识库来源目录：")
    total_pdfs = 0
    for d in sources:
        if d.exists():
            pdfs = list(d.glob("**/*.[pP][dD][fF]"))
            total_pdfs += len(pdfs)
            print(f"  {d} ({len(pdfs)} 个 PDF)")
        else:
            print(f"  {d} (不存在)")
    tracker = _load_tracker(settings)
    print(f"\n当前索引追踪: {len(tracker)}/{total_pdfs} 个 PDF 文件")
    print(f"Chroma 数据目录: {settings.resolved_chroma_dir}")
    print(f"向量集合名: {settings.collection_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="医学教材知识库向量构建")
    parser.add_argument("--full", action="store_true", help="全量重建（清空现有数据后重新构建）")
    parser.add_argument("--yes", action="store_true", help="跳过确认提示")
    parser.add_argument("--info", action="store_true", help="显示知识库来源信息")
    args = parser.parse_args()

    if args.info:
        show_info()
        sys.exit(0)

    if args.full:
        if not args.yes:
            print("全量重建模式：将清空现有向量数据后重新构建所有 PDF...")
            answer = input("确认全量重建？这将删除现有向量数据 (y/N): ").strip().lower()
            if answer != "y":
                print("已取消。")
                sys.exit(0)
        else:
            print("全量重建模式：清空现有向量数据后重新构建所有 PDF...")
        settings = get_settings()
        chroma_dir = settings.resolved_chroma_dir
        if chroma_dir.exists():
            import shutil
            for item in chroma_dir.iterdir():
                if item.name != _load_tracker.__globals__.get("_TRACKER_FILENAME", ""):
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        import os
        tracker_path = chroma_dir / "vector_index_tracker.json"
        if tracker_path.exists():
            tracker_path.unlink()
        count = build_knowledge_base(batch_size=8, rate_per_minute=4000)
        print(f"全量重建完成，共写入 {count} 个向量片段。")
    else:
        print("增量更新模式：仅处理新增或修改的 PDF 文件...")
        count = build_knowledge_base_incremental(batch_size=8, rate_per_minute=4000)
        if count > 0:
            print(f"增量更新完成，共写入 {count} 个向量片段。")