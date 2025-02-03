from fastapi import FastAPI,Request, Depends, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String,create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Annotated


Base = declarative_base()
app = FastAPI()

app.mount('/static', StaticFiles(directory="static"), name = "static")

templates = Jinja2Templates(directory="templates")



class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index = True)
    title = Column(String(50), unique=True)
    detail = Column(String(100))


class TaskBase(BaseModel):
    title: str
    detail: str

SQL_DATABASE = "mysql+pymysql://root:Dimple#3110@localhost:3306/TodoApplication"

engine = create_engine(SQL_DATABASE)

SessionLocal = sessionmaker(autocommit = False, bind = engine)

Base.metadata.create_all(bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/", response_class=HTMLResponse)
async def load(request: Request):
    return templates.TemplateResponse(name = "index.html", context = {"request": request})


@app.post("/create_task", response_model=TaskBase)
def create_task(db: db_dependency, task: TaskBase):
    db_task = Task(title = task.title, detail = task.detail)
    db.add(db_task)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/show_tasks", response_class=HTMLResponse)
def read_tasks(db: db_dependency, request: Request):
    db_tasks = db.query(Task)
    return templates.TemplateResponse("tasks.html", context = {"request":request,"tasks": db_tasks})


@app.get("/delete_task/{task_id}")
def delete_task(task_id: int, db: db_dependency, request: Request):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail = "task not found")
    db.delete(db_task)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/update_task/{task_id}")
def update_task(request: Request, task_id: int):
    return templates.TemplateResponse(name = "update_task.html", context={"request": request, "task_id":task_id})

    
@app.post("/update_task/{task_id}")
def update(db: db_dependency, task_id: int, title: str = Form() , detail: str = Form()):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail = "task not found")
    if title != "":
        db_task.title = title
    if detail != "":
        db_task.detail = detail
    db.add(db_task)
    db.commit()
    return RedirectResponse("/", status_code=303)