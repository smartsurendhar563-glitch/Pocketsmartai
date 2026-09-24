import os
os.environ['DATABASE_PATH']='app/data/test_pocketsmart.db'
os.environ['SECRET_KEY']='test-secret'
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db

init_db()
client=TestClient(app)

def test_health():
    r=client.get('/health'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_register_login_and_home():
    username='tester_unique'; email='tester_unique@example.com'
    client.post('/api/register',json={'username':username,'email':email,'password':'password123'})
    r=client.post('/api/login',json={'username':username,'password':'password123'}); assert r.status_code==200
    r=client.post('/api/home-budget',json={'total_budget':50000,'rooms':['Living Room'],'num_lights':5,'num_fans':2,'num_furniture':2,'num_dining_tables':1}); assert r.status_code==200
    assert r.json()['recommendation_id']
