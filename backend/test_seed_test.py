from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from datetime import datetime, date, timedelta
from app.database import SessionLocal, engine, Base
from app.models.machine import Machine
from app.models.job import Job, Operation
from app.models.disruption import Disruption
from app.models.schedule import Schedule, ScheduleOperation
from app.seed import seed_all
from app.services.scheduling_engine import run_scheduling_engine

seed_all(reset=True)
db = SessionLocal()
print('Machines in DB:', db.query(Machine).count())
print('Jobs in DB:', db.query(Job).count())
print('Ready to test extended jobs.')

