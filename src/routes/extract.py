"""Router module defining endpoints for calling Meteor from Rest API"""


# pylint: disable=broad-exception-caught

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.templating import _TemplateResponse, Jinja2Templates

from src.settings import get_settings, Settings
from src.util import Utils

router = APIRouter(tags=['Extract metadata from file'])
templates = Jinja2Templates(directory="templates")
utils = Utils()


@router.post("/", response_class=HTMLResponse)
async def post_pdf_html(
        request: Request
) -> _TemplateResponse:
    """
    Extract metadata from a PDF from either
    an uploaded file or a URL and display
    it in an HTML template
    """
    form = await request.form()
    file_input = form.get('fileInput')
    file_url = form.get('fileUrl')
    backend = str(form.get('backend'))

    if file_url != "" and isinstance(file_url, str):
        utils.verify_url(file_url)
        filename: Optional[str] = file_url
        filepath = utils.download_file(file_url)
        results = utils.process_and_remove(filename, filepath, backend=backend)
    elif file_input is not None and isinstance(file_input, UploadFile):
        utils.verify_file(file_input)
        filename = file_input.filename
        filepath = utils.save_file(file_input)
        results = utils.process_and_remove(filename, filepath, backend=backend)
    else:
        raise HTTPException(400)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "file": file_input,
            "url": file_url,
            "filepath": filepath,
            "filename": filename,
            "results": results,
            "root_path": utils.get_environment_prefix(),
            "backends": utils.get_available_backends()
        }
    )


@router.post("/json", response_class=JSONResponse)
async def post_pdf_json(
        request: Request
) -> Response:
    """
    Extract metadata from a PDF file and return it as JSON
    """
    form = await request.form()
    file_input = form.get('fileInput')
    file_url = form.get('fileUrl')
    backend = str(form.get('backend'))

    if file_url != "" and isinstance(file_url, str):
        utils.verify_url(file_url)
        filepath = utils.download_file(file_url)
        results = utils.process_and_remove(
            file_url, filepath, backend=backend, delete_immediately=True)
    elif file_input is not None and isinstance(file_input, UploadFile):
        utils.verify_file(file_input)
        filepath = utils.save_file(file_input)
        results = utils.process_and_remove(
            file_input.filename, filepath, backend=backend, delete_immediately=True)
    else:
        raise HTTPException(400)
    return JSONResponse(results)


@router.get("/file/{file_name}", response_class=JSONResponse, status_code=200)
async def get_metadata_from_file_on_disk(
        file_name: str,
        conf: Annotated[Settings, Depends(get_settings)],
        backend: Optional[str] = Query(None)  # Define the optional query parameter
) -> JSONResponse:
    """
    Extract metadata from a file on disk and return it as JSON
    """
    try:
        results = utils.meteor.run(conf.MOUNT_FOLDER + '/' + file_name, backend=backend)
    except Exception:
        return JSONResponse({"error": f"Error while processing {file_name}"})
    return JSONResponse(results)
