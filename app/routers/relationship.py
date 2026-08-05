from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/relationship", tags=["relationship"])


@router.get("", response_class=HTMLResponse)
def relationship_placeholder() -> HTMLResponse:
    return HTMLResponse(
        "<html><body><h1>Munosabat testi</h1>"
        "<p>Mavjud funksionallik bu yerda saqlanadi. Personality test alohida mahsulot sifatida ishlaydi.</p>"
        "<p><a href='/personality'>Xarakter testiga o‘tish</a></p></body></html>"
    )
