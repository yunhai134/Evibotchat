from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    external_model_api_key: str = ""
    external_model_base_url: str = ""
    chat_model: str = "gpt-4o-mini"
    embedding_provider: str = "local"
    embedding_model: str = "C:/System_IT/Evibotchat/backend/models/bge-m3"
    embedding_cache_dir: str = "./models"
    embedding_device: str = "cpu"
    hf_endpoint: str = "https://hf-mirror.com"
    knowledge_dirs: str = "../激素和代谢性障碍_表格PDFs;../激素和代谢性障碍_PDFs;../精神健康障碍_PDFs;../精神健康障碍_表格PDFs"
    knowledge_dir: str = ""
    knowledge_base_dir: str = "../knowleagebaseoriginaldata"
    knowledge_base_auto_discover: bool = True
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
    final_k: int = 3
    rerank_relevance_threshold: float = 0.5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _apply_external_model_aliases(self) -> "Settings":
        """兼容 External_Model_* 环境变量别名。"""
        if not self.openai_api_key and self.external_model_api_key:
            self.openai_api_key = self.external_model_api_key
        if self.external_model_base_url and self.openai_base_url == "https://api.openai.com/v1":
            self.openai_base_url = self.external_model_base_url
        return self

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
    def resolved_knowledge_base_dir(self) -> Path:
        return self._resolve_path(self.knowledge_base_dir)

    @property
    def discovered_knowledge_dirs(self) -> list[Path]:
        """自动发现 knowledge_base_dir 下的所有子目录（排除隐藏目录和文件）。"""
        base = self.resolved_knowledge_base_dir
        if not base.exists():
            return self.resolved_knowledge_dirs
        return sorted([d for d in base.iterdir() if d.is_dir() and not d.name.startswith(".")])

    @property
    def resolved_chroma_dir(self) -> Path:
        return self._resolve_path(self.chroma_dir)


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """获取全局配置单例。每次 uvicorn reload 会重置模块级变量，自动加载最新 .env。"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """强制重新读取 .env 配置（供 /config/reload 端点调用）。"""
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance
