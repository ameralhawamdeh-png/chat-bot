from fastapi import FastAPI, Depends, HTTPException, Header,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from login_script import decode_jwt_token
from pydantic import BaseModel
from main import *
import asyncio
import httpx
import jwt



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    query: str

class LoginRequest(BaseModel):
    email: str
    password: str


templates = Jinja2Templates(directory="../front-end")
@app.get("/")
def redirect_to_home():
    return "Welcome"
 

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
    

@app.post("/login")
async def login_user(req: LoginRequest):
    url = "https://api-test.penny.co/api/auth/login"
    payload = {"email": req.email, "password": req.password, "platform": "web"}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.post(url, json=payload)

        data = response.json()
        if "accessToken" not in data:
            raise HTTPException(status_code=401, detail="Login failed")

        return {"access_token": data["accessToken"]}

    except asyncio.CancelledError:
       
        raise HTTPException(status_code=499, detail="Request cancelled")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")


@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = get_file_path(filename)
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)



@app.post('/ask')
async def ask_agent(question: Question, authorization: str = Header(...)):

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt_token(token)
    return {
        "answer": sql_maker(question.query, user_data, token),
        "user": user_data
    }