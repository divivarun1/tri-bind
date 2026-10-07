import os, tempfile, hashlib, hmac
os.environ['TRIBIND_DB']=os.path.join(tempfile.gettempdir(),'tribind_cases.db')
try: os.remove(os.environ['TRIBIND_DB'])
except FileNotFoundError: pass
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, get_db
from app.config import NETWORK_ID
from app.security import behavior_score
client=TestClient(app)

def reg(did,secret='secret-12345',fw=b'fw'):
    with get_db() as db: db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?,?)',('ICU-ZONE-A','ICU',NETWORK_ID))
    return client.post('/devices',json={'device_id':did,'device_type':'temperature','context_id':'ICU-ZONE-A','firmware_hash':hashlib.sha256(fw).hexdigest(),'credential':secret})

def full(did):
    secret='secret-12345'; fw=hashlib.sha256(b'fw').hexdigest(); ch=client.post(f'/devices/{did}/challenge').json()['challenge']; sh=hashlib.sha256(secret.encode()).hexdigest(); resp=hmac.new(sh.encode(),ch.encode(),hashlib.sha256).hexdigest()
    assert client.post(f'/devices/{did}/verify-identity',json={'challenge':ch,'response':resp}).status_code==200
    assert client.post(f'/devices/{did}/firmware',json={'current_firmware_hash':fw}).status_code==200
    assert client.post(f'/devices/{did}/verify-context',json={'context_id':'ICU-ZONE-A'}).status_code==200
    tok=client.post(f'/devices/{did}/cbot/generate',json={'firmware_hash':fw}).json()['token']; assert client.post(f'/devices/{did}/cbot/verify',json={'token':tok}).status_code==200
    assert client.post(f'/devices/{did}/onboard').status_code==200
    return tok

def test_duplicate_registration():
    assert reg('DUP-001').status_code==200; assert reg('DUP-001').status_code==409

def test_challenge_replay():
    reg('REPLAY-001'); r=client.post('/devices/REPLAY-001/challenge').json(); sh=hashlib.sha256(b'secret-12345').hexdigest(); resp=hmac.new(sh.encode(),r['challenge'].encode(),hashlib.sha256).hexdigest(); assert client.post('/devices/REPLAY-001/verify-identity',json={'challenge':r['challenge'],'response':resp}).status_code==200; assert client.post('/devices/REPLAY-001/verify-identity',json={'challenge':r['challenge'],'response':resp}).status_code==409

def test_firmware_mismatch_quarantines():
    reg('FW-001'); full_identity=client.post('/devices/FW-001/challenge').json(); sh=hashlib.sha256(b'secret-12345').hexdigest(); resp=hmac.new(sh.encode(),full_identity['challenge'].encode(),hashlib.sha256).hexdigest(); client.post('/devices/FW-001/verify-identity',json={'challenge':full_identity['challenge'],'response':resp}); r=client.post('/devices/FW-001/firmware',json={'current_firmware_hash':hashlib.sha256(b'bad').hexdigest()}); assert r.status_code==403; assert client.get('/devices/FW-001').json()['state']=='QUARANTINED'

def test_context_mismatch_rejected():
    reg('CTX-001'); full_identity=client.post('/devices/CTX-001/challenge').json(); sh=hashlib.sha256(b'secret-12345').hexdigest(); resp=hmac.new(sh.encode(),full_identity['challenge'].encode(),hashlib.sha256).hexdigest(); client.post('/devices/CTX-001/verify-identity',json={'challenge':full_identity['challenge'],'response':resp}); client.post('/devices/CTX-001/firmware',json={'current_firmware_hash':hashlib.sha256(b'fw').hexdigest()}); r=client.post('/devices/CTX-001/verify-context',json={'context_id':'WARD-ZONE-B'}); assert r.status_code==403

def test_invalid_transition_rejected():
    reg('STATE-001'); assert client.post('/devices/STATE-001/onboard').status_code==409

def test_cbot_tampering_quarantines():
    reg('TAMPER-001'); tok=full('TAMPER-001'); bad=tok[:-1]+('0' if tok[-1]!='0' else '1'); r=client.post('/devices/TAMPER-001/cbot/verify',json={'token':bad}); assert r.status_code==403; assert client.get('/devices/TAMPER-001').json()['state']=='QUARANTINED'

def test_behavior_formula_and_thresholds():
    normal={'packet_rate':2,'destination':'GATEWAY','port':1883,'protocol':'MQTT','connection_success':1,'scanning':0,'lateral_movement':0}; bad={'packet_rate':100,'destination':'UNKNOWN','port':445,'protocol':'TCP','connection_success':0.2,'scanning':1,'lateral_movement':1}; assert behavior_score(normal)==1.0; assert behavior_score(bad)<.5
