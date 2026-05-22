from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    embedding_provider: str = "local"
    embedding_model: str = "C:/System_IT/Evibotchat/backend/models/bge-m3"
    embedding_cache_dir: str = "./models"
    hf_endpoint: str = "https://hf-mirror.com"
    knowledge_dirs: str = "../激素和代谢性障碍_表格PDFs;../激素和代谢性障碍_PDFs;../精神健康障碍_PDFs;../精神健康障碍_表格PDFs"
    knowledge_dir: str = ""
    chroma_dir: str = "./chroma_db"
    collection_name: str = "medical_books"
    retrieval_k: int = 20
    chunk_size: int = 600
    chunk_overlap: int = 100

    # Huatuo-26M QA 知识库
    qa_collection_name: str = "huatuo_qa"
    qa_retrieval_k: int = 3
    qa_similarity_threshold: float = 0.55

    # Rerank 重排序
    rerank_enabled: bool = True
    rerank_model: str = "C:/System_IT/Evibotchat/backend/models/bge-reranker-v2-m3"
    rerank_device: str = "cpu"
    final_k: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _resolve_path(self, value: str) -> Path:
        path = Path(value.strip())
        return path if path.is_absolute() else (self.backend_dir / path).resolve()

    @property
    def resolved_embedding_cache_dir(self) -> Path:
        return self._resolve_path(self.embedding_cache_dir)

    @property
    def resolved_knowledge_dirs(self) -> list[Path]:
        raw = self.knowledge_dirs or self.knowledge_dir
        values = [part.strip() for part in raw.replace("\n", ";").split(";") if part.strip()]
        return [self._resolve_path(value) for value in values]

    @property
    def resolved_knowledge_dir(self) -> Path:
        dirs = self.resolved_knowledge_dirs
        return dirs[0] if dirs else self.backend_dir

    @property
    def resolved_chroma_dir(self) -> Path:
        return self._resolve_path(self.chroma_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
