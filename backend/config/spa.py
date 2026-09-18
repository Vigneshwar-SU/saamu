"""SPA fallback view for serving the compiled React production build."""

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt

# Prefixes that belong to the backend and must never be served the SPA shell.
# Requests under these prefixes that reach this view are unmatched backend
# routes, so they raise Http404 and fall through to the configured JSON 404
# handler (apps.common.views.custom_404), preserving the API error contract.
BACKEND_PREFIXES = ("api", "admin", "static", "media")


@csrf_exempt
def spa_fallback(request, path):
    """Serve the frontend index.html for any route the backend does not own.

    Only GET/HEAD navigation requests are served the SPA shell; every other
    method on an unmatched path keeps the previous 404 behaviour.
    """
    prefix = path.split("/", 1)[0]
    if prefix in BACKEND_PREFIXES:
        raise Http404

    if request.method not in ("GET", "HEAD"):
        raise Http404

    if not settings.FRONTEND_DIST:
        raise Http404

    index_file = settings.FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise Http404

    return FileResponse(index_file.open("rb"), content_type="text/html")