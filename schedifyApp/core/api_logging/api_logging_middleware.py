import json
import time
import uuid
from django.utils.deprecation import MiddlewareMixin


def short_headers(headers):
    """Keep only useful headers for logging."""
    keep_keys = ["Content-Type", "User-Agent", "Authorization", "Content-Length"]
    return {k: v for k, v in headers.items() if k in keep_keys}


class APILoggingMiddleware(MiddlewareMixin):
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

            # Request log
            print(f"===================== [START] {request.method} {request.get_full_path()} ===================== ")
            print(f"  ID       : {request._log_id}")
            print(f"  Headers  : {short_headers(dict(request.headers))}")
            print(f"  Body     : {body_data}")
            print("-" * 80)

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
                data = "Non-serializable response"

            # Response log
            print(f"  Status   : {response.status_code}")
            print(f"  Time     : {elapsed} ms")
            print(f"  Response : {data}")
            print(f"===================== [END]   {request.method} {request.get_full_path()} | ID: {log_id} ===================== \n")

        return response
