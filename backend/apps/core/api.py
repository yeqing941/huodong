from django.db import connection
from django.http import JsonResponse


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            database = "ok" if cursor.fetchone()[0] == 1 else "error"
    except Exception:
        database = "error"

    status = "ok" if database == "ok" else "degraded"
    return JsonResponse({"data": {"status": status, "database": database}, "meta": {}})
