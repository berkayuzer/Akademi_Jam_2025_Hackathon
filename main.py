from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from database import SessionLocal, User, UserProgress, Base, engine
from ai.roadmap import generate_roadmap, generate_topic_summary_and_challenges, check_code_with_testcases, generate_step_examples_and_challenges

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse("/home", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(email: str = Form(...), username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return RedirectResponse("/login", status_code=302)
    new_user = User(email=email, username=username, password=password)
    db.add(new_user)
    db.commit()
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db), request: Request = None):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if user:
        request.session["user"] = username
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Kullanıcı adı veya şifre hatalı!"})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)

    progress = db.query(UserProgress).filter(UserProgress.username == user).first()
    if progress:
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.post("/select_topic")
def select_topic(language: str = Form(...), topic: str = Form(...), db: Session = Depends(get_db), request: Request = None):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)
    existing = db.query(UserProgress).filter(UserProgress.username == user, UserProgress.language == language, UserProgress.topic == topic).first()
    if not existing:
        progress = UserProgress(username=user, language=language, topic=topic)
        db.add(progress)
        db.commit()
    # Kullanıcı eksik olduğu konuları UserProgress tablosundan çek
    progress = db.query(UserProgress).filter(UserProgress.username == user).all()
    topics = [p.topic for p in progress if not p.completed]
    if not topics:
        return RedirectResponse("/home", status_code=302)
    roadmap_data = generate_roadmap(topics)
    return templates.TemplateResponse("roadmap.html", {"request": request, "roadmap": roadmap_data, "user": user})

@app.get("/topic", response_class=HTMLResponse)
def topic_page(request: Request, lang: str, topic: str, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)
    # Gemini'dan konu özeti ve challenge başlıklarını al
    topic_data = generate_topic_summary_and_challenges(lang, topic)
    return templates.TemplateResponse("topic_page.html", {
        "request": request,
        "lang": lang,
        "topic": topic,
        "user": user,
        "summary": topic_data.get("summary", ""),
        "challenges": topic_data.get("challenges", [])
    })

@app.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse("general_home.html", {"request": request})
    progress = db.query(UserProgress).filter(UserProgress.username == user).all()
    completed = sum(1 for p in progress if p.completed)
    total = len(progress)
    percent = int((completed / total) * 100) if total > 0 else 0
    badge = "Yeni Başlayan" if percent < 40 else "Orta Seviye" if percent < 80 else "Usta!"
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "progress": progress,
        "progress_percent": percent,
        "badge": badge
    })

@app.post("/complete_topic")
def complete_topic(request: Request, language: str = Form(...), topic: str = Form(...), db: Session = Depends(get_db)):
    user = request.session.get("user")
    progress = db.query(UserProgress).filter_by(username=user, language=language, topic=topic).first()
    if progress:
        progress.completed = True
        db.commit()
    return RedirectResponse("/home", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/home", status_code=302)

@app.post("/roadmap", response_class=HTMLResponse)
def roadmap(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)
    # Kullanıcının eksik olduğu konuları UserProgress tablosundan çek
    progress = db.query(UserProgress).filter(UserProgress.username == user).all()
    topics = [p.topic for p in progress if not p.completed]
    if not topics:
        return RedirectResponse("/home", status_code=302)
    roadmap_data = generate_roadmap(topics)
    return templates.TemplateResponse("roadmap.html", {"request": request, "roadmap": roadmap_data, "user": user})

@app.get("/roadmap", response_class=HTMLResponse)
def roadmap_get(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)
    progress = db.query(UserProgress).filter(UserProgress.username == user).all()
    topics = [p.topic for p in progress if not p.completed]
    if not topics:
        return RedirectResponse("/home", status_code=302)
    roadmap_data = generate_roadmap(topics)
    return templates.TemplateResponse("roadmap.html", {"request": request, "roadmap": roadmap_data, "user": user})

@app.get("/challenge", response_class=HTMLResponse)
def challenge_page(request: Request, lang: str, topic: str, level: str, step: str = None, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)
    if step:
        # step_challenge'dan geldiyse, ilgili step için challenge'ı bul
        data = generate_step_examples_and_challenges(lang, topic, step)
        challenge = next((c for c in data.get("challenges", []) if c["level"] == level), None)
        if not challenge:
            return RedirectResponse(f"/step_challenge?lang={lang}&topic={topic}&step={step}", status_code=302)
        return templates.TemplateResponse("challenge.html", {
            "request": request,
            "lang": lang,
            "topic": topic,
            "level": level,
            "challenge": challenge,
            "user": user
        })
    # Gemini'dan challenge detaylarını al
    topic_data = generate_topic_summary_and_challenges(lang, topic)
    challenge = next((c for c in topic_data.get("challenges", []) if c["level"] == level), None)
    if not challenge:
        return RedirectResponse(f"/topic?lang={lang}&topic={topic}", status_code=302)
    return templates.TemplateResponse("challenge.html", {
        "request": request,
        "lang": lang,
        "topic": topic,
        "level": level,
        "challenge": challenge,
        "user": user
    })

@app.get("/step_challenge", response_class=HTMLResponse)
def step_challenge_page(request: Request, lang: str, topic: str, step: str):
    data = generate_step_examples_and_challenges(lang, topic, step)
    return templates.TemplateResponse("step_challenge.html", {
        "request": request,
        "lang": lang,
        "topic": topic,
        "step": step,
        "explanation": data.get("explanation", ""),
        "examples": data.get("examples", []),
        "challenges": data.get("challenges", []),
        "raw": str(data)
    })

@app.post("/run_code")
def run_code(lang: str = Form(...), code: str = Form(...), example_input: str = Form(...), example_output: str = Form(...)):
    # Sadece örnek input/output ile test
    testcases = [{"input": example_input, "output": example_output}]
    results = check_code_with_testcases(code, lang, testcases)
    return JSONResponse({"success": all(results)})

@app.post("/submit_code")
def submit_code(lang: str = Form(...), code: str = Form(...), topic: str = Form(...), level: str = Form(...)):
    # Challenge'ın gizli testlerini Gemini'dan al
    topic_data = generate_topic_summary_and_challenges(lang, topic)
    challenge = next((c for c in topic_data.get("challenges", []) if c["level"] == level), None)
    if not challenge:
        return JSONResponse({"success": False, "error": "Challenge bulunamadı."})
    testcases = challenge.get("hidden_tests", [])
    results = check_code_with_testcases(code, lang, testcases)
    if all(results):
        return JSONResponse({"success": True})
    else:
        return JSONResponse({"success": False, "error": "Bazı testler başarısız."})


