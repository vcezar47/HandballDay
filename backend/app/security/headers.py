"""Security headers (barem 10.04). Two documents, two policies.

The API answers JSON and images, so its policy forbids everything. The single-page app is served by
the web server (Vite preview locally, Apache in production: copy SPA_CSP into .htaccess in M6), and
its policy lists exactly what the app loads:
  - scripts: our own bundle and the Turnstile widget (challenges.cloudflare.com)
  - styles: our own files; inline style="" attributes are allowed (React sets colours and positions
    that way) but inline <style> and style-src 'unsafe-inline' are not
  - images: ours, data: and blob: (the logo preview)
  - connections: our own API only. The Stripe redirect is a navigation, which CSP does not restrict.
Keep SPA_CSP in sync with frontend/vite.config.js.
"""

from starlette.datastructures import MutableHeaders

from ..config import get_config

API_CSP = "default-src 'none'; frame-ancestors 'none'"
SPA_CSP = (
    "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; "
    "style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data: blob:; "
    "connect-src 'self'; frame-src https://challenges.cloudflare.com; "
    "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)
# camera=() because there is no camera scanning yet: allow (self) on the scan page if it is added.
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
DOCS_PATHS = {"/docs", "/redoc"}  # Swagger loads scripts from a CDN, so it cannot run under API_CSP


class SecurityHeadersMiddleware:
    """Pure ASGI, outermost layer: even error and CSRF-rejection responses carry the headers."""

    def __init__(self, app) -> None:
        self.app = app
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": PERMISSIONS_POLICY,
        }
        if get_config().secure_cookies:  # HTTPS only: browsers ignore HSTS over plain HTTP, and it would be wrong to promise it
            self.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(self.headers)
        if scope["path"] not in DOCS_PATHS:
            headers["Content-Security-Policy"] = API_CSP

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                out = MutableHeaders(scope=message)
                for name, value in headers.items():
                    out.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)
