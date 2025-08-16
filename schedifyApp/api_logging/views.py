import os
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

LOG_FILE = settings.APP_LOG_FILE


def _tail_lines(path, max_lines=200):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        lines = f.readlines()
    return lines[-max_lines:]


@staff_member_required
def api_logs_json(request):
    n = int(request.GET.get("n", 200))
    return JsonResponse({"lines": _tail_lines(LOG_FILE, max_lines=min(n, 1000))})


@staff_member_required
def api_logs_page(request):
    return render(request, "api_logs.html", {
        "is_staff": request.user.is_staff
    })


@staff_member_required
def clear_logs(request):
    """
    Clears logs older than the given date (YYYY-MM-DD).
    """
    cutoff = request.GET.get("date")
    if not cutoff:
        return JsonResponse({"success": False, "error": "No date provided."}, status=400)

    if not os.path.exists(LOG_FILE):
        return JsonResponse({"success": True, "message": "Log file not found, nothing to clear."})

    from datetime import datetime

    try:
        cutoff_date = datetime.strptime(cutoff, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    kept_lines = []
    cleared_count = 0
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                import json
                log = json.loads(line)
                ts = datetime.fromisoformat(log.get("ts", "").split(" ")[0]).date()

                if ts > cutoff_date:
                    kept_lines.append(line)
                else:
                    cleared_count += 1
            except Exception:
                # keep malformed lines
                kept_lines.append(line)

    with open(LOG_FILE, "w") as f:
        f.writelines(kept_lines)

    return JsonResponse({"success": True, "cleared": cleared_count})
