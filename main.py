from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum as PyEnum
import datetime


from fastapi.middleware.cors import CORSMiddleware




# Database setup
DATABASE_URL = "mysql+pymysql://root:root@localhost/EventManagement"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    attendees = relationship("Attendee", back_populates="event", cascade="all, delete")
    tasks = relationship("Task", back_populates="event", cascade="all, delete")

class Attendee(Base):
    __tablename__ = "attendees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    event = relationship("Event", back_populates="attendees")

class TaskStatus(PyEnum):
    Pending = "Pending"
    Completed = "Completed"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.Pending)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    assignee_id = Column(Integer, ForeignKey("attendees.id", ondelete="SET NULL"))
    event = relationship("Event", back_populates="tasks")

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class EventCreate(BaseModel):
    name: str
    description: str = None
    location: str
    date: datetime.date

class EventUpdate(BaseModel):
    name: str = None
    description: str = None
    location: str = None
    date: datetime.date = None

class AttendeeCreate(BaseModel):
    name: str
    email: str
    event_id: int

class TaskCreate(BaseModel):
    name: str
    deadline: datetime.date
    event_id: int
    assignee_id: int = None

class TaskUpdateStatus(BaseModel):
    status: TaskStatus

# Event Management API
@app.post("/events/")
def create_event(event: EventCreate, db: SessionLocal = Depends(get_db)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.get("/events/")
def get_all_events(db: SessionLocal = Depends(get_db)):
    return db.query(Event).all()

@app.put("/events/{event_id}")
def update_event(event_id: int, event: EventUpdate, db: SessionLocal = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.dict(exclude_unset=True).items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.delete("/events/{event_id}")
def delete_event(event_id: int, db: SessionLocal = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(db_event)
    db.commit()
    return {"detail": "Event deleted"}

# Attendee Management API
@app.post("/attendees/")
def add_attendee(attendee: AttendeeCreate, db: SessionLocal = Depends(get_db)):
    db_attendee = Attendee(**attendee.dict())
    db.add(db_attendee)
    db.commit()
    db.refresh(db_attendee)
    return db_attendee

@app.get("/attendees/")
def get_all_attendees(db: SessionLocal = Depends(get_db)):
    return db.query(Attendee).all()

@app.delete("/attendees/{attendee_id}")
def delete_attendee(attendee_id: int, db: SessionLocal = Depends(get_db)):
    db_attendee = db.query(Attendee).filter(Attendee.id == attendee_id).first()
    if not db_attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    db.delete(db_attendee)
    db.commit()
    return {"detail": "Attendee deleted"}

# Task Management API
@app.post("/tasks/")
def create_task(task: TaskCreate, db: SessionLocal = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task  

@app.get("/tasks/{event_id}")
def get_tasks_for_event(event_id: int, db: SessionLocal = Depends(get_db)):
    return db.query(Task).filter(Task.event_id == event_id).all()

@app.put("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: TaskUpdateStatus, db: SessionLocal = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.status = status.status
    db.commit()
    db.refresh(db_task)
    return db_task
