import json
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"

def short_headers(headers):
    """Keep only useful headers."""
    keep_keys = ["Content-Type", "User-Agent", "Authorization", "Content-Length"]
    return {k: v for k, v in headers.items() if k in keep_keys}

class APILoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/api/"):
            request._log_id = str(uuid.uuid4())[:8]
            request._start_time = time.time()

            # Prepare request body
            try:
                body = request.body.decode("utf-8")
                body_data = json.loads(body) if body else {}
            except Exception:
                body_data = request.body.decode("utf-8", errors="ignore")

            # Compact start log
            print(f"\n{MAGENTA}┌─── [START] {request.method} {request.get_full_path()} ───┐{RESET}")
            print(f"{CYAN}ID:{RESET} {request._log_id}")
            print(f"{CYAN}Headers:{RESET} {short_headers(dict(request.headers))}")
            print(f"{CYAN}Body:{RESET} {body_data}")

        return None

    def process_response(self, request, response):
        if request.path.startswith("/api/"):
            elapsed = round((time.time() - getattr(request, "_start_time", time.time())) * 1000, 2)
            log_id = getattr(request, "_log_id", "--------")

            # Prepare response body
            try:
                data = (
                    response.data
                    if hasattr(response, "data")
                    else response.content.decode("utf-8")
                )
            except Exception:
                data = "Non-serializable response"

            # Compact end log
            status_color = GREEN if 200 <= response.status_code < 300 else RED
            print(f"{CYAN}Status:{RESET} {status_color}{response.status_code}{RESET} | {CYAN}Time:{RESET} {elapsed} ms")
            print(f"{CYAN}Response:{RESET} {data}")
            print(f"{MAGENTA}└─── [END] {request.method} {request.get_full_path()} ───┘{RESET}\n")

        return response
