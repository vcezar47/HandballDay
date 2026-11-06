from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from ..config import get_config
from ..db import get_db
from ..services import CatalogService

# Outside /api on purpose: crawlers look for these two at the site root.
router = APIRouter(tags=["seo"], include_in_schema=False)


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return f"User-agent: *\nDisallow: /api/\nSitemap: {get_config().public_url}/sitemap.xml\n"


@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    base = get_config().public_url
    catalog = CatalogService(db)
    paths = ["/", "/clubs", "/fixtures"]
    paths += [f"/clubs/{c.slug}" for c in catalog.list_clubs()]
    paths += [f"/fixtures/{f.id}" for f in catalog.list_fixtures(limit=200)]
    urls = "".join(f"<url><loc>{escape(base + p)}</loc></url>" for p in paths)
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(body, media_type="application/xml")
