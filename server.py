# -*- coding: utf-8 -*-
"""
===================================
Daily Stock Analysis - FastAPI 后端服务入口
===================================

职责：
1. 提供 RESTful API 服务
2. 配置 CORS 跨域支持
3. 健康检查接口
4. 托管前端静态文件（生产模式）

启动方式：
    uvicorn server:app --reload --host 0.0.0.0 --port 8000
    
    或使用 main.py:
    python main.py --serve-only      # 仅启动 API 服务
    python main.py --serve           # API 服务 + 执行分析
"""

import logging
import os

# ── Python 3.14 + sniffio 1.3.x 兼容性修补 ──────────────────────
# sniffio 的 asyncio 偵測在 Python 3.14 下失敗（asyncio.current_task()
# 回傳 None），導致 anyio / starlette StreamingResponse 全面崩潰。
# 在此強制設定 sniffio thread-local，讓它直接回傳 "asyncio"。
import sniffio._impl as _sniffio_impl
_sniffio_impl.thread_local.name = "asyncio"
# ─────────────────────────────────────────────────────────────────

from src.config import setup_env, get_config
from src.logging_config import setup_logging

# 初始化环境变量与日志
setup_env()

config = get_config()
level_name = (config.log_level or "INFO").upper()
level = getattr(logging, level_name, logging.INFO)

setup_logging(
    log_prefix="api_server",
    console_level=level,
    extra_quiet_loggers=['uvicorn', 'fastapi'],
)

# 从 api.app 导入应用实例
from api.app import app  # noqa: E402

# 导出 app 供 uvicorn 使用
__all__ = ['app']


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv("WEBUI_PORT", "8000")),
        reload=True,
    )
