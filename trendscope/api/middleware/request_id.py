"""Request ID middleware — injects unique request_id into all JSON responses"""
import uuid
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求生成唯一 request_id，注入 JSON 响应体 + 响应头。

    位置：应注册在 CORSMiddleware 之后（最外层），确保覆盖所有响应。
    注意：StreamingResponse 无法读取 body，仅注入头。
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        # Always add X-Request-ID header
        response.headers["X-Request-ID"] = request_id

        # Inject request_id into JSON response body (skip StreamingResponse)
        if isinstance(response, StreamingResponse):
            return response

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                body = getattr(response, "body", None)
                if body:
                    data = json.loads(body)
                    data["request_id"] = request_id
                    new_body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                    # Preserve existing headers and cookies
                    new_headers = dict(response.headers)
                    return Response(
                        content=new_body,
                        status_code=response.status_code,
                        headers=new_headers,
                        media_type="application/json",
                    )
            except (ValueError, AttributeError, TypeError):
                pass

        return response
