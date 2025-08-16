# schedifyApp/core/middleware/api_logging.py
import json
import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

api_logger = logging.getLogger("api_hits")


class ApiHitLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/api/"):
            request._log_id = str(uuid.uuid4())[:8]
            request._start_time = time.time()

            # Parse request body safely
            try:
                raw_body = request.body.decode("utf-8")
                body_data = json.loads(raw_body) if raw_body else {}
            except Exception:
                body_data = request.body.decode("utf-8", errors="ignore")

            request._body_data = body_data

        return None

    def process_response(self, request, response):
        if request.path.startswith("/api/"):
            elapsed = round((time.time() - getattr(request, "_start_time", time.time())) * 1000, 2)
            log_id = getattr(request, "_log_id", "--------")

            # Parse response safely
            try:
                data = (
                    response.data
                    if hasattr(response, "data")
                    else response.content.decode("utf-8")
                )
            except Exception:
                data = "⚠️ Non-serializable response"

            # Minimal JSON log (file/db/UI)
            entry = {
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "id": log_id,
                "method": request.method,
                "path": request.path,
                "headers": dict(request.headers),
                "body": getattr(request, "_body_data", {}),
                "status": response.status_code,
                "time_ms": elapsed,
                "response": data,
                "ip": request.META.get("REMOTE_ADDR"),
                "ua": request.META.get("HTTP_USER_AGENT", "")[:200],
            }
            api_logger.info(json.dumps(entry))

        return response
