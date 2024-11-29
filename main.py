"""Main module for FastAPI service"""


import markdown
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from secure import secure
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.routes import extract
from src.util import Utils

SWAGGER_URL = f"{Utils.get_environment_prefix()}/swagger-ui"
allowed_origins = ["https://*.nb.no*", "http://*.nb.no*"]

app = FastAPI(
    title="METEOR",
    description="API documentation for METEOR",
    docs_url=SWAGGER_URL,
    openapi_url=f"{Utils.get_environment_prefix()}/openapi.json"
)
app.mount(
    f"{Utils.get_environment_prefix()}/static",
    StaticFiles(directory="static"),
    name="static"
)
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST"])
secure_headers = secure.Secure()

router = APIRouter(prefix=Utils.get_environment_prefix())
router.include_router(extract.router)
app.include_router(router=router)

templates = Jinja2Templates(directory="templates")


@app.get(f"{Utils.get_environment_prefix()}/doc", tags=["Documentation"])
def get_documentation(request: Request) -> Response:
    doc_text = "\n"
    with open("DOC.md", encoding="UTF-8") as infile:
        for line in infile:
            doc_text += line
    return templates.TemplateResponse(
        "doc.html",
        {
            "request": request,
            "doc": markdown.markdown(doc_text),
            "root_path": Utils.get_environment_prefix()
        }
    )


@app.get(
    f"{Utils.get_environment_prefix()}/",
    tags=["Templates"],
    response_class=HTMLResponse, status_code=200
)
async def get_front_page_html(request: Request) -> Response:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "root_path": Utils.get_environment_prefix(),
            "backends": Utils.get_available_backends()
        }
    )


@app.exception_handler(StarletteHTTPException)
def display_error_message_in_template(request: Request, exc: StarletteHTTPException) -> Response:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "results": {
                'error': str(exc.detail)
            },
            "root_path": Utils.get_environment_prefix(),
            "backends": Utils.get_available_backends()
        },
        status_code=exc.status_code
    )
