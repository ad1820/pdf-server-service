from fastapi import FastAPI
from controllers.auth_controller import router as auth_router
from controllers.user_controller import router as user_router
from controllers.pdf_controller import router as pdf_router
from database.db import users_collection

app = FastAPI(title="AI PDF Reader API")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(pdf_router)

# print("Mongo user count:", users_collection.count_documents({}))
