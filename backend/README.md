# Evibot Medical RAG Backend

## Python 版本要求

请使用 Python 3.11 或 3.12。不要使用 Python 3.14。

`pydantic-core`、`tokenizers` 等依赖在 Python 3.14 上可能没有预编译 wheel，会触发本地 Rust 编译并安装失败。

## 1. 创建虚拟环境并安装依赖

```powershell
cd c:\System_IT\Evibotchat\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

`python --version` 应显示 `Python 3.12.x` 或 `Python 3.11.x`。

## 2. 配置环境变量

复制 `.env.example` 为 `.env`，填写 `OPENAI_API_KEY`。

```powershell
copy .env.example .env
```

如需使用 DeepSeek/OpenAI 兼容接口，可配置：

```env
OPENAI_BASE_URL=https://api.deepseek.com/v1
CHAT_MODEL=deepseek-chat
```

## 3. 当前知识库目录

`.env` 使用 `KNOWLEDGE_DIRS` 配置多个 PDF 来源目录，用分号分隔：

```env
KNOWLEDGE_DIRS=../激素和代谢性障碍_表格PDFs;../激素和代谢性障碍_PDFs;../精神健康障碍_PDFs;../精神健康障碍_表格PDFs
```

当前 PDF 解析流程：

- `pdfplumber` 提取普通文本
- `pdfplumber` 提取简单表格并转 Markdown
- 正则清洗噪声、合并英文断词、合并中文异常换行
- `RecursiveCharacterTextSplitter` 分块：`CHUNK_SIZE=600`，`CHUNK_OVERLAP=100`
- 元数据包含：`source`、`file_name`、`path`、`relative_path`、`page`、`category`
- 向量模型：默认本地 `bge-m3`，路径由 `EMBEDDING_MODEL` 指定
- 存储：Chroma，目录由 `CHROMA_DIR` 指定

如果后续遇到扫描版图片 PDF，再补 PaddleOCR；当前代码优先处理简单文本和简单表格 PDF。

## 4. 构建医学向量库

```powershell
cd c:\System_IT\Evibotchat\backend
.\.venv\Scripts\Activate.ps1
python scripts\ingest.py
```

构建完成后会输出：

```text
已写入向量片段: xxxx
```

## 5. 启动后端

```powershell
cd c:\System_IT\Evibotchat\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

接口：

- `GET /health`
- `POST /chat/stream`，SSE 流式返回。
