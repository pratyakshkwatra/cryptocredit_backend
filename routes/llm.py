from fastapi import APIRouter, Depends
from auth_deps import get_current_user

router = APIRouter(prefix="/llm", tags=["LLM"])

@router.post("/")
def llm_chat(prompt: str, current_user=Depends(get_current_user)):

    return {"user_id": current_user.id, "prompt": prompt, "response": f"Echo: {prompt}"}