from fastapi import FastAPI
from app.routes.caption import router as caption_router
from app.routes.songs import router as songs_router
from app.routes import palette
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Insta Caption Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(caption_router)
app.include_router(songs_router)
app.include_router(palette.router)
@app.get("/")
def read_root():
    return {"message": "Backend is alive!"}