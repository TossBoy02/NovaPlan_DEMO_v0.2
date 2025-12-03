from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from generator import generate_roadmaps_for_user
from data_ingest import DATA_DIR
from pathlib import Path
import os

app = FastAPI()

# serve static frontend
# serve static frontend from novaPlan-master/dist
# We assume the build output is in ../novaPlan-master/dist relative to this file
FRONTEND_DIST = Path('../novaPlan-master/dist')

app.mount('/assets', StaticFiles(directory=FRONTEND_DIST / 'assets'), name='assets')
# We also keep the old static for generated images
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/')
async def read_root():
    return FileResponse(FRONTEND_DIST / 'index.html')

# allow local dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health')
async def health():
    return {'status':'ok'}

@app.post('/generate')
async def generate(request: Request):
    payload = await request.json()
    out = generate_roadmaps_for_user(payload)
    return JSONResponse(content=out)

@app.get('/download')
async def download():
    path = 'generated_roadmaps_output.json'
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Output not found')
    return FileResponse(path, media_type='application/json', filename='generated_roadmaps_output.json')

@app.post('/upload_onet')
async def upload_onet(file: UploadFile = File('onet_upload.zip')):
    # Accept manual O*NET zip upload and extract
    data_path = DATA_DIR / 'onet_upload.zip'
    with open(data_path, 'wb') as f:
        f.write(await file.read())
    return {'status':'uploaded', 'path': str(data_path)}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
