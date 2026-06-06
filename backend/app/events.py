"""커스텀 스트림 이벤트 emit 헬퍼.

``get_stream_writer``로 카드/추천/메시지를 즉시 흘려보내 '실시간으로 채워지는' UX를 만든다.
스트리밍 컨텍스트가 아니면(예: graph.invoke 테스트) 조용히 무시한다.
"""

from __future__ import annotations


def emit(payload: dict) -> None:
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
    except Exception:
        return
    if writer is not None:
        writer(payload)
