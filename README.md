# Evibot — 循证医学问答助手

基于 RAG（检索增强生成）的医学知识问答系统，整合默沙东诊疗手册教材与 Huatuo-26M 问答数据集，通过本地嵌入模型和重排序模型实现高精度检索，支持 LLM 综合生成与程序化输出双模式。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS v4 |
| 后端 | FastAPI + Python 3.12 |
| RAG 框架 | LangChain 0.3 |
| 向量数据库 | ChromaDB |
| 嵌入模型 | BAAI/bge-m3（1024 维，多语言） |
| 重排序模型 | BAAI/bge-reranker-v2-m3 |
| 问答数据集 | Huatuo-26M-Lite |

---

## 项目结构

```
.
├── backend/
│   ├── app/              # FastAPI 核心应用
│   │   ├── main.py       # API 路由与 SSE 流式响应
│   │   ├── rag.py        # RAG 编排流程
│   │   ├── vectorstore.py # 向量库、PDF 提取、知识库构建
│   │   └── config.py     # 配置管理
│   ├── scripts/          # 数据导入脚本
│   │   ├── ingest.py     # 增量/全量重建教材向量库
│   │   ├── ingest_huatuo.py # 导入 Huatuo 问答对
│   │   └── download_huatuo.py # 下载 Huatuo 数据集
│   ├── .env.example      # 环境变量模板
│   └── requirements.txt
├── web-app/
│   ├── src/              # React 前端源码
│   └── package.json
├── Huatuo-26M/           # Huatuo 数据集（需自行下载）
├── knowleagebaseoriginaldata/  # 医学教材 PDF（需自行获取）
├── pyproject.toml
└── uv.lock
```

---

## 快速开始

### 1. 环境准备

- Python 3.12
- Node.js 20+
- CUDA（可选，用于 GPU 加速嵌入和重排序）

### 2. 安装依赖

**后端：**

```bash
cd backend
pip install -r requirements.txt
```

**前端：**

```bash
cd web-app
npm install
```

### 3. 配置环境变量

复制模板并填写：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填写你的 LLM API Key（可选，不填则使用程序化输出模式）：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o-mini
```

### 4. 下载模型

从 Hugging Face 下载 BGE-M3 和 BGE-Reranker-v2-M3：

```bash
# 设置镜像（国内）
export HF_ENDPOINT=https://hf-mirror.com

# 下载嵌入模型
huggingface-cli download BAAI/bge-m3 --local-dir backend/models/bge-m3

# 下载重排序模型
huggingface-cli download BAAI/bge-reranker-v2-m3 --local-dir backend/models/bge-reranker-v2-m3
```

### 5. 准备知识库

**医学教材 PDF**（默沙东诊疗手册中文版）：

将 PDF 文件放入 `knowleagebaseoriginaldata/` 下的分类目录中，例如：

```
knowleagebaseoriginaldata/
├── 医学主题/
│   ├── 感染_PDFs/
│   ├── 皮肤病_PDFs/
│   └── ...
└── 表格/
    ├── 基本知识 (23)/
    └── ...
```

**Huatuo-26M 问答数据集**（可选）：

```bash
cd backend
python scripts/download_huatuo.py
```

### 6. 构建向量索引

```bash
cd backend

# 全量重建教材向量库
python scripts/ingest.py --full --yes

# 导入 Huatuo 问答对
python scripts/ingest_huatuo.py
```

### 7. 启动服务

**后端（终端 1）：**

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端（终端 2）：**

```bash
cd web-app
npm run dev
```

访问 http://localhost:5173 即可使用。

---

## 核心功能

### 双知识库检索

系统同时检索两个知识库并合并结果：

1. **教材库** — 基于 BGE-M3 嵌入的向量相似度检索，经 BGE-Reranker 重排序
2. **问答库** — Huatuo-26M-Lite 的 5 万条医学问答对

### 智能去重

- 教材文档间去重：4-gram Jaccard 相似度 ≥ 0.45 视为重复
- QA 答案与教材内容去重：逐句比对，移除与教材重叠的句子

### 双模式输出

| 模式 | 触发条件 | 特点 |
|------|---------|------|
| LLM 综合 | 配置了 API Key | LLM 基于检索资料综合生成，结构化回答 |
| 程序化 | 未配置 API Key | 直接展示检索到的教材片段，附来源标注 |

LLM 调用失败时自动降级到程序化输出。

### SSE 流式响应

后端通过 Server-Sent Events 逐字推送回答，前端实时渲染，支持：
- 分阶段状态提示（解析中 → 思考中 → 输出中）
- 来源标注（教材名称 + 页码）
- 相似问题推荐（QA 库匹配结果）

---

## 配置说明

关键环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥 | 空（程序化模式） |
| `OPENAI_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `CHAT_MODEL` | 对话模型 | `gpt-4o-mini` |
| `EMBEDDING_DEVICE` | 嵌入设备 | `cpu` |
| `RERANK_DEVICE` | 重排序设备 | `cpu` |
| `RETRIEVAL_K` | 初始检索数量 | `20` |
| `FINAL_K` | 重排序后返回数量 | `5` |
| `CHUNK_SIZE` | 文本分块大小 | `600` |
| `CHUNK_OVERLAP` | 分块重叠大小 | `100` |

---

## 数据来源与许可

**医学教材**
- 内容来源：默沙东诊疗手册（MSD Manuals）
- 版权归属：Merck & Co., Inc. 及其附属公司
- 使用须遵守 [MSD 权限政策](https://www.msdmanuals.cn/home/content/permissions)

**问答数据集**
- Huatuo-26M-Lite（[Hugging Face](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite)）
- 许可：Apache 2.0
- 论文：[arXiv:2305.01526](https://arxiv.org/abs/2305.01526)

**模型**
- BAAI/bge-m3（[Hugging Face](https://huggingface.co/BAAI/bge-m3)）— MIT License
- BAAI/bge-reranker-v2-m3（[Hugging Face](https://huggingface.co/BAAI/bge-reranker-v2-m3)）— MIT License

---

## 免责声明

本项目提供的医学信息仅供参考，不能替代专业医生的诊断和治疗建议。如有身体不适或紧急症状，请及时就医。
