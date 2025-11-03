from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.auth_controller import router as auth_router
from controllers.user_controller import router as user_router
from controllers.pdf_controller import router as pdf_router
from database.db import users_collection

app = FastAPI(title="AI PDF Reader API")

origins = [ 
    "https://pdf-client-service.vercel.app",
    "https://pdf-rag-service.onrender.com",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(pdf_router)
