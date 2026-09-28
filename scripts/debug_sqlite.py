import os, sys
api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, api_dir)

from sqlalchemy import create_engine
from app.database.base import Base
import app.models.user
import app.models.environment
import app.models.resource
import app.models.incidents
import app.models.remediation
import app.models.rbac

from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)

from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    print("Tables:", [r[0] for r in res.fetchall()])
