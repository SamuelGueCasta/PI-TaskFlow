import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth, usuarios, proyectos, tareas, subtareas

app = FastAPI(
    title="TaskFlow API",
    description="API REST para la gestión de tareas empresariales",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (fotos de perfil de usuario)
os.makedirs("static/fotos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(proyectos.router)
app.include_router(tareas.router)
app.include_router(subtareas.router)

@app.get("/")
def root():
    return {"mensaje": "TaskFlow API funcionando correctamente"}