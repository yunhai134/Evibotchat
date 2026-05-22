import logging
import os
from pathlib import Path

# 禁用 ChromaDB 遥测（避免 posthog 版本不兼容导致的 capture() 报错）
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 静音无害的第三方库日志噪音
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("posthog").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import get_settings, reload_settings
from .rag import stream_rag_answer

app = FastAPI(title="Evibot Medical RAG API", version="0.1.0")


@app.on_event("startup")
def _print_startup_info():
    s = get_settings()
    print("=" * 50)
    print("  Evibot Backend Started")
    print(f"  CHAT_MODEL   = {s.chat_model}")
    print(f"  BASE_URL     = {s.openai_base_url}")
    print(f"  API_KEY      = {s.openai_api_key[:8]}..." if s.openai_api_key else "  API_KEY      = (empty)")
    print(f"  LLM Mode     = {'llm' if s.openai_api_key else 'programmatic'}")
    print(f"  EMBED_DEVICE = {s.embedding_device}")
    print(f"  RERANK       = {'on' if s.rerank_enabled else 'off'} ({s.rerank_device})")
    print("=" * 50)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/health")
def health():
    settings = get_settings()
    llm_connected = bool(settings.openai_api_key)
    return {
        "status": "ok",
        "collection": settings.collection_name,
        "knowledge_dir": str(settings.resolved_knowledge_dir),
        "chroma_dir": str(settings.resolved_chroma_dir),
        "llm_connected": llm_connected,
        "chat_model": settings.chat_model if llm_connected else None,
        "mode": "llm" if llm_connected else "programmatic",
    }


@app.post("/config/reload")
def config_reload():
    """重新读取 .env 配置，无需重启后端即可切换模型等参数。"""
    old = get_settings()
    new = reload_settings()
    return {
        "message": "Config reloaded",
        "chat_model": {"old": old.chat_model, "new": new.chat_model},
        "base_url": {"old": old.openai_base_url, "new": new.openai_base_url},
        "llm_connected": bool(new.openai_api_key),
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")

    return StreamingResponse(
        stream_rag_answer(question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/chat/stream")
async def chat_stream_get(question: str):
    question = question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")

    return StreamingResponse(
        stream_rag_answer(question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


_CHAT_PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evibot 医学问答测试</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;height:100vh;display:flex;flex-direction:column}
.header{background:#1a73e8;color:#fff;padding:16px 24px;font-size:18px;font-weight:600}
#chat{flex:1;overflow-y:auto;padding:20px 24px}
.msg{margin-bottom:16px;display:flex}
.msg.user{justify-content:flex-end}
.msg .bubble{max-width:70%;padding:12px 16px;border-radius:12px;line-height:1.6;white-space:pre-wrap;word-break:break-word;font-size:14px}
.msg.user .bubble{background:#1a73e8;color:#fff;border-bottom-right-radius:4px}
.msg.bot .bubble{background:#fff;color:#333;border-bottom-left-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.msg.bot .bubble code{background:#e8e8e8;padding:2px 4px;border-radius:3px;font-size:13px}
.msg.bot .bubble pre{background:#f0f0f0;padding:8px;border-radius:6px;overflow-x:auto;margin:8px 0}
.msg.bot .bubble pre code{background:none;padding:0}
.sources{margin-top:8px;font-size:12px;color:#888}
.sources span{background:#e3f2fd;color:#1565c0;padding:2px 8px;border-radius:10px;margin-right:4px}
.suggestion{margin-top:8px;padding:8px 12px;background:#fff8e1;border-left:3px solid #f9a825;border-radius:4px;font-size:13px;color:#555}
.suggestion b{color:#e65100}
.input-bar{padding:16px 24px;background:#fff;border-top:1px solid #e0e0e0;display:flex;gap:12px}
#q{flex:1;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:14px;outline:none}
#q:focus{border-color:#1a73e8}
#btn{padding:10px 24px;background:#1a73e8;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer}
#btn:disabled{background:#aaa;cursor:not-allowed}
.typing::after{content:"▌";animation:blink 1s infinite}
@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
</style>
</head>
<body>
<div class="header">Evibot 医学问答测试</div>
<div id="chat"></div>
<div class="input-bar">
<input id="q" placeholder="输入医学问题，如：甲状腺功能减退的症状有哪些？" autofocus />
<button id="btn" onclick="send()">发送</button>
</div>
<script>
const chat=document.getElementById('chat'),inp=document.getElementById('q'),btn=document.getElementById('btn');
inp.addEventListener('keydown',e=>{if(e.key==='Enter')send()});
async function send(){
  const q=inp.value.trim();if(!q)return;
  btn.disabled=true;inp.value='';
  addMsg('user',q);
  const botDiv=addMsg('bot','');const bubble=botDiv.querySelector('.bubble');
  bubble.classList.add('typing');
  try{
    const r=await fetch('/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    if(!r.ok){bubble.textContent='错误: '+r.status;return}
    const reader=r.body.getReader(),dec=new TextDecoder();
    let buf='',text='',sources=null,suggestion=null,eventType=null;
    while(true){
      const{done,value}=await reader.read();if(done)break;
      buf+=dec.decode(value,{stream:true});
      const lines=buf.split('\\n');buf=lines.pop();
      for(const line of lines){
        const l=line.trim();
        if(l.startsWith('event:')){eventType=l.substring(6).trim();continue}
        if(l.startsWith('data:')){
          const d=l.substring(5).trim();
          if(eventType==='done'){eventType=null;continue}
          if(eventType==='sources'){try{sources=JSON.parse(d)}catch(e){}eventType=null;continue}
          if(eventType==='suggestion'){try{suggestion=JSON.parse(d)}catch(e){}eventType=null;continue}
          text+=d;eventType=null;
        }
      }
      bubble.textContent=text;
      chat.scrollTop=chat.scrollHeight;
    }
    bubble.classList.remove('typing');
    let extra='';
    if(sources){
      extra+='<div class="sources">来源：'+sources.map(s=>'<span>'+s.source+' 第'+s.page+'页</span>').join('')+'</div>';
    }
    if(suggestion){
      extra+='<div class="suggestion">您是不是想问：<b>'+suggestion.question+'</b>'+(suggestion.disease?' ('+suggestion.disease+')':'')+'</div>';
    }
    bubble.innerHTML=md(text)+extra;
  }catch(e){bubble.classList.remove('typing');bubble.textContent='请求失败: '+e.message}
  finally{btn.disabled=false;inp.focus();chat.scrollTop=chat.scrollHeight}
}
function addMsg(role,content){
  const d=document.createElement('div');d.className='msg '+role;
  d.innerHTML='<div class="bubble">'+(role==='user'?esc(content):esc(content))+'</div>';
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d;
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function md(s){
  s=esc(s);
  s=s.replace(/```([\\s\\S]*?)```/g,'<pre><code>$1</code></pre>');
  s=s.replace(/`([^`]+)`/g,'<code>$1</code>');
  s=s.replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>');
  s=s.replace(/^### (.+)$/gm,'<b>$1</b><br>');
  s=s.replace(/^## (.+)$/gm,'<b style="font-size:16px">$1</b><br>');
  s=s.replace(/^\\| (.+) \\|$/gm,m=>'<tr>'+m.split('|').filter(c=>c.trim()).map(c=>'<td style="border:1px solid #ddd;padding:4px 8px">'+c.trim()+'</td>').join('')+'</tr>');
  return s;
}
</script>
</body>
</html>"""


# 静态文件目录：backend/../web-app/dist
_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "web-app" / "dist"

# API 路由在前，静态文件兜底
app.mount("/", StaticFiles(directory=str(_DIST_DIR), html=True), name="static")
