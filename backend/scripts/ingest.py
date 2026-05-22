import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.vectorstore import build_knowledge_base


if __name__ == "__main__":
    count = build_knowledge_base()
    print(f"已写入向量片段: {count}")
