import hashlib
from .db import init_db,get_db
from .config import NETWORK_ID

def fw(v): return hashlib.sha256(v.encode()).hexdigest()
def seed():
 init_db()
 contexts=[('ICU-ZONE-A','ICU Zone A'),('WARD-ZONE-B','Ward Zone B'),('SECURITY-ZONE','Security Zone')]
 devices=[('TEMP-001','temperature','ICU-ZONE-A','temp-firmware-v1','temp-secret-001'),('ENV-001','environment','WARD-ZONE-B','env-firmware-v1','env-secret-001'),('PATIENT-001','patient-monitor','ICU-ZONE-A','patient-firmware-v1','patient-secret-001'),('OXY-001','oxygen-monitor','ICU-ZONE-A','oxy-firmware-v1','oxy-secret-001'),('CAM-001','camera','SECURITY-ZONE','cam-firmware-v1','cam-secret-001')]
 with get_db() as db:
  for cid,name in contexts: db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?,?)',(cid,name,NETWORK_ID))
  for did,typ,cid,fv,secret in devices:
   if not db.execute('SELECT 1 FROM devices WHERE device_id=?',(did,)).fetchone():
    db.execute('INSERT INTO devices VALUES(?,?,?,?,?,?,?,?)',(did,typ,cid,fw(fv),hashlib.sha256(secret.encode()).hexdigest(),'UNKNOWN',__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),None)); db.execute('INSERT INTO credentials VALUES(?,?,?)',(did,hashlib.sha256(secret.encode()).hexdigest(),__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
if __name__=='__main__': seed()
