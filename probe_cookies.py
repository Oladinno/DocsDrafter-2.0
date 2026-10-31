from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine

Base.metadata.create_all(bind=engine)
c = TestClient(app)
print("csrf json:", c.get("/api/auth/csrf").json())
r = c.post("/api/auth/register", json={"email": "probe2@t.dev", "password": "password123", "name": "P"})
print("register:", r.status_code)
r2 = c.post("/api/auth/login", json={"email": "probe2@t.dev", "password": "password123"})
print("login:", r2.status_code)
print("cookies.items():", dict(c.cookies.items()))
