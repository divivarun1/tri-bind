import os, tempfile, hashlib, pytest
os.environ['TRIBIND_DB']=os.path.join(tempfile.gettempdir(),'tribind_test.db')
try: os.remove(os.environ['TRIBIND_DB'])
except FileNotFoundError: pass
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
from app.config import NETWORK_ID

client=TestClient(app)

def setup_module():
 init_db()
 from app.db import get_db
 with get_db() as db:
  db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?,?)",('ICU-ZONE-A','ICU Zone A',NETWORK_ID))
 client.post('/devices',json={'device_id':'TEMP-001','device_type':'temperature','context_id':'ICU-ZONE-A','firmware_hash':hashlib.sha256(b'fw').hexdigest(),'credential':'temp-secret-001'})

def test_health(): assert client.get('/health').status_code==200

def onboard(did='TEMP-001',secret='temp-secret-001'):
 c=client.post(f'/devices/{did}/challenge').json()['challenge']
 secret_hash=hashlib.sha256(secret.encode()).hexdigest(); import hmac
 response=hmac.new(secret_hash.encode(),c.encode(),hashlib.sha256).hexdigest()
 assert client.post(f'/devices/{did}/verify-identity',json={'challenge':c,'response':response}).status_code==200
 fw=hashlib.sha256(b'fw').hexdigest(); assert client.post(f'/devices/{did}/firmware',json={'current_firmware_hash':fw}).status_code==200
 assert client.post(f'/devices/{did}/verify-context',json={'context_id':'ICU-ZONE-A'}).status_code==200
 token=client.post(f'/devices/{did}/cbot/generate',json={'firmware_hash':fw}).json()['token']; assert client.post(f'/devices/{did}/cbot/verify',json={'token':token}).status_code==200
 assert client.post(f'/devices/{did}/onboard').json()['state']=='PROBATION'
 return token

def test_complete_onboarding_and_replay():
 with __import__('app.db',fromlist=['get_db']).get_db() as db: db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?,?)",('ICU-ZONE-A','ICU Zone A',NETWORK_ID))
 client.post('/devices',json={'device_id':'REPLAY-CORE','device_type':'temperature','context_id':'ICU-ZONE-A','firmware_hash':hashlib.sha256(b'fw').hexdigest(),'credential':'temp-secret-001'})
 token=onboard('REPLAY-CORE'); assert client.post('/devices/REPLAY-CORE/cbot/verify',json={'token':token}).status_code==409

def test_normal_behavior_trusted():
 onboard('TEMP-001')
 client.post('/devices/TEMP-001/telemetry',json={'packet_rate':2,'communication_frequency':1/30,'destination':'GATEWAY','port':1883,'protocol':'MQTT','connection_success':1})
 r=client.post('/devices/TEMP-001/evaluate-behavior'); assert r.status_code==200; assert r.json()['final_state']=='TRUSTED'

def test_scanning_quarantines():
 r=client.post('/attack-lab/simulate',json={'device_id':'TEMP-001','attack_type':'network_scanning'}); assert r.status_code==200; assert r.json()['final_state']=='QUARANTINED'
 assert client.get('/devices/TEMP-001').json()['state']=='QUARANTINED'
