# api.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from user_store import load_users, save_users
from auth import get_password_hash, verify_password, create_access_token

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class User(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: User):
    users = load_users()
    if user.username in users:
        raise HTTPException(status_code=400, detail="Username already exists.")
    users[user.username] = {
        "username": user.username,
        "password": get_password_hash(user.password)
    }
    save_users(users)
    return {"msg": "Registration successful."}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    user = users.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# api.py'ye ekleyin
from challenges import load_challenges, get_challenge_by_id

class Challenge(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str  # easy, medium, hard
    category: str  # algorithms, data-structures, etc.
    test_cases: List[Dict]
    starter_code: str

@app.get("/challenges", response_model=List[Challenge])
def get_challenges():
    return load_challenges()

@app.get("/challenges/{challenge_id}", response_model=Challenge)
def get_challenge(challenge_id: str):
    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge
