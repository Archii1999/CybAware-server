from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers importeren
from app.routers import (
    users,
    companies,
    trainings,
    progress,
    stats,
)

app = FastAPI(title="CybAware API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Alle routers registreren
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(trainings.router)
app.include_router(progress.router)   
app.include_router(stats.router)      


@app.get("/", tags=["root"])
def read_root():
    return {"message": "CybAware API is running 🚀"}
