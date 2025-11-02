from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
import tempfile
import httpx
import os
from utils.cloudinary_utils import upload_pdf_to_cloudinary
from middleware.verification_middleware import verify_token
from database.db import files_collection  # Changed from users_collection
from bson import ObjectId
from datetime import datetime
import json

router = APIRouter(prefix="/pdf", tags=["PDF"])

# Agent service configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

if not AGENT_API_KEY:
    raise ValueError("AGENT_API_KEY not set in environment variables")


@router.post("/upload")
async def upload_pdf(user=Depends(verify_token), file: UploadFile = File(...)):
    try:
        file_content = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        pdf_url = upload_pdf_to_cloudinary(tmp_path)

        file_doc = {
            "user_id": user["uid"],
            "filename": file.filename,
            "cloudinary_url": pdf_url,
            "uploaded_at": datetime.utcnow().isoformat(),
            "indexed": False,
            "conversations": []
        }
        
        result = files_collection.insert_one(file_doc)
        file_id = str(result.inserted_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{AGENT_SERVICE_URL}/index_pdf",
                    headers={"X-API-Key": AGENT_API_KEY}, 
                    data={"file_id": file_id},
                    files={"file": (file.filename, file_content, "application/pdf")}
                )
                
                if response.status_code == 200:
                    agent_response = response.json()

                    files_collection.update_one(
                        {"_id": ObjectId(file_id)},
                        {"$set": {
                            "indexed": True,
                            "text_length": agent_response.get("text_length", 0)
                        }}
                    )
                    
                    return {
                        "message": "File uploaded and indexed successfully",
                        "file_id": file_id,
                        "url": pdf_url,
                        "indexed": True
                    }
                else:
                    return {
                        "message": "File uploaded but indexing failed",
                        "file_id": file_id,
                        "url": pdf_url,
                        "indexed": False,
                        "error": response.text
                    }
        
        except httpx.RequestError as e:
            return {
                "message": "File uploaded but agent service unreachable",
                "file_id": file_id,
                "url": pdf_url,
                "indexed": False,
                "error": str(e)
            }
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_pdf(
    user=Depends(verify_token),
    file_id: str = Form(...),
    query: str = Form(...)
):
    try:
        file_doc = files_collection.find_one({
            "_id": ObjectId(file_id),
            "user_id": user["uid"]
        })
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        if not file_doc.get("indexed", False):
            raise HTTPException(status_code=400, detail="File not indexed yet. Please wait.")

        conversations = file_doc.get("conversations", [])
        chat_history = []
        
        if conversations:
            latest_conversation = conversations[-1]
            messages = latest_conversation.get("messages", [])

            for msg in messages[-10:]:
                chat_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/query",
                headers={"X-API-Key": AGENT_API_KEY},
                data={
                    "file_id": file_id,
                    "query": query,
                    "chat_history": json.dumps(chat_history)
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent service error: {response.text}"
                )
            
            agent_response = response.json()
            answer = agent_response["response"]

        timestamp = datetime.utcnow().isoformat()

        if not conversations:
            files_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$push": {
                    "conversations": {
                        "started_at": timestamp,
                        "messages": [
                            {"role": "user", "content": query, "timestamp": timestamp},
                            {"role": "assistant", "content": answer, "timestamp": timestamp}
                        ]
                    }
                }}
            )
        else:
            files_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$push": {
                    f"conversations.{len(conversations)-1}.messages": {
                        "$each": [
                            {"role": "user", "content": query, "timestamp": timestamp},
                            {"role": "assistant", "content": answer, "timestamp": timestamp}
                        ]
                    }
                }}
            )
        
        return {
            "response": answer,
            "file_id": file_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{file_id}")
async def get_conversation_history(file_id: str, user=Depends(verify_token)):
    """Get conversation history for a PDF."""
    try:
        file_doc = files_collection.find_one({
            "_id": ObjectId(file_id),
            "user_id": user["uid"]
        })
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        return {
            "file_id": file_id,
            "filename": file_doc.get("filename"),
            "conversations": file_doc.get("conversations", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new-conversation/{file_id}")
async def start_new_conversation(file_id: str, user=Depends(verify_token)):
    """Start a new conversation for a PDF (clears context)."""
    try:
        file_doc = files_collection.find_one({
            "_id": ObjectId(file_id),
            "user_id": user["uid"]
        })
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        return {"message": "Ready for new conversation"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_pdf(file_id: str, user=Depends(verify_token)):
    try:
        file_doc = files_collection.find_one({
            "_id": ObjectId(file_id),
            "user_id": user["uid"]
        })
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(
                    f"{AGENT_SERVICE_URL}/cache/{file_id}",
                    headers={"X-API-Key": AGENT_API_KEY} 
                )
        except:
            pass 
        
        #delete from MongoDB
        files_collection.delete_one({"_id": ObjectId(file_id)})
        
        return {"message": "PDF deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_user_pdfs(user=Depends(verify_token)):
    """List all PDFs uploaded by the user."""
    try:
        files = list(files_collection.find(
            {"user_id": user["uid"]},
            {
                "_id": 1,
                "filename": 1,
                "cloudinary_url": 1,
                "uploaded_at": 1,
                "indexed": 1,
                "conversations": 1
            }
        ))

        for file in files:
            file["file_id"] = str(file.pop("_id"))
            file["message_count"] = sum(
                len(conv.get("messages", [])) 
                for conv in file.get("conversations", [])
            )
        
        return {"files": files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))