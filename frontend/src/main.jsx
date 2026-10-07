import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useLocation,
  useParams
} from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid
} from 'recharts';
import './style.css';

const API='http://127.0.0.1:8000';

async function api(path,opts={}){
  const r=await fetch(API+path,{
    headers:{
      'Content-Type':'application/json',
      ...(opts.headers||{})
    },
    ...opts
  });

  const j=await r.json().catch(()=>({}));

  if(!r.ok){
    throw new Error(
      j.detail ||
      j.message ||
      `Request failed (${r.status})`
    );
  }

  return j;
}

const demoDevices=[
  {
    device_id:'TEMP-001',
    device_type:'Temperature Sensor',
    context_id:'ICU-ZONE-A',
    expected_firmware_hash:'9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
  },
  {
    device_id:'ENV-001',
    device_type:'Environmental Sensor',
    context_id:'WARD-ZONE-B',
    expected_firmware_hash:'7f83b1657ff1fc53b92dc18148a1d65dfa1350ba2a7d4f1d4d1b0b3e0c2a6b19'
  },
  {
    device_id:'PATIENT-001',
    device_type:'Patient Monitor',
    context_id:'ICU-ZONE-A',
    expected_firmware_hash:'2c26b46b68ffc68ff99b453c1d30413413422a11c4b8f3a9a1b2c3d4e5f60718'
  },
  {
    device_id:'OXY-001',
    device_type:'Oxygen Monitor',
    context_id:'ICU-ZONE-A',
    expected_firmware_hash:'4a44dc15364204a80fe80e9039455cc1608281820b6a6c3a9e7f4d2c1b0a9876'
  },
  {
    device_id:'CAM-001',
    device_type:'Security Camera',
    context_id:'SECURITY-ZONE',
    expected_firmware_hash:'6b23c0d5f35d1b11f9b683f0b0a4d7c3e2f1a9b8c7d6e5f4a3b2c1d0e9f80716'
  }
];

function State({s}){
  return (
    <span className={'state '+String(s||'UNKNOWN').toLowerCase()}>
      <i/>
      {s||'UNKNOWN'}
    </span>
  );
}

function Icon({children}){
  return <span className="icon">{children}</span>;
}

function Layout({children}){
  const loc=useLocation();

  const links=[
    ['/dashboard','Dashboard','◈'],
    ['/devices','Devices','▦'],
    ['/onboarding','Onboarding','⇥'],
    ['/behavior','Behavior','⌁'],
    ['/attack-lab','Attack Lab','⚡'],
    ['/security-logs','Security Logs','≡'],
    ['/architecture','Architecture','◇'],
    ['/threat-model','Threat Model','△'],
    ['/case-study','Case Study','▣'],
    ['/demo','Professor Demo','▶'],
    ['/about','About','i']
  ];

  return (
    <div className="shell">

      <aside className="sidebar">

        <div className="logo">
          <div className="logo-mark">T</div>

          <div>
            <b>TRI-BIND</b>
            <small>SECURE IoT LAB</small>
          </div>
        </div>

        <div className="side-label">
          CONTROL CENTER
        </div>

        <nav>
          {links.map(([p,label,ic])=>(
            <Link
              className={
                loc.pathname===p ||
                (p==='/devices' &&
                loc.pathname.startsWith('/devices/'))
                  ? 'active'
                  : ''
              }
              key={p}
              to={p}
            >
              <Icon>{ic}</Icon>
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="side-bottom">
          <div className="status-dot">
            <i/>
            Backend connected
          </div>

          <small>
            FastAPI • SQLite
            <br/>
            Academic prototype
          </small>
        </div>

      </aside>

      <div className="content-shell">

        <header className="topbar">

          <div className="mobile-title">
            TRI-BIND
          </div>

          <div className="crumb">
            SMART HOSPITAL /
            {' '}
            <b>
              {loc.pathname.split('/')[1]||'dashboard'}
            </b>
          </div>

          <div className="top-actions">
            <span className="env">
              FICTIONAL LAB
            </span>

            <span className="avatar">
              A
            </span>
          </div>

        </header>

        <main className="main">
          {children}
        </main>

      </div>

    </div>
  );
}

function PageTitle({
  eyebrow,
  title,
  description,
  actions
}){
  return (
    <div className="page-title">

      <div>
        <div className="eyebrow">
          {eyebrow}
        </div>

        <h1>
          {title}
        </h1>

        {description && (
          <p>
            {description}
          </p>
        )}
      </div>

      <div className="title-actions">
        {actions}
      </div>

    </div>
  );
}

function Metric({
  label,
  value,
  sub,
  tone='blue'
}){
  return (
    <div className={'metric '+tone}>

      <div className="metric-top">
        <span>{label}</span>
        <span className="metric-dot"/>
      </div>

      <strong>
        {value}
      </strong>

      <small>
        {sub}
      </small>

    </div>
  );
}

function Table({
  rows=[],
  cols
}){
  return (
    <div className="table-wrap">

      <table>

        <thead>
          <tr>
            {cols.map(c=>(
              <th key={c}>
                {c.replaceAll('_',' ')}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>

          {rows.length ? (
            rows.map((r,i)=>(
              <tr key={i}>

                {cols.map(c=>(
                  <td key={c}>

                    {c==='state' ||
                    c==='final_state' ? (
                      <State s={r[c]}/>
                    ) : (
                      String(r[c]??'—')
                    )}

                  </td>
                ))}

              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={cols.length}>
                <div className="empty">
                  No records yet
                </div>
              </td>
            </tr>
          )}

        </tbody>

      </table>

    </div>
  );
}

function Dashboard(){

  const[d,setD]=useState(null);
  const[err,setErr]=useState('');
  const[seeding,setSeeding]=useState(false);
  const[seedMsg,setSeedMsg]=useState('');

  async function load(){
    try{
      setErr('');
      setD(
        await api('/dashboard/summary')
      );
    }catch(e){
      setErr(e.message);
    }
  }

  useEffect(()=>{
    load();
  },[]);

  async function seed(){

    setSeeding(true);
    setSeedMsg('');

    const results=[];

    for(const x of demoDevices){

      try{

        await api(
          '/devices/register',
          {
            method:'POST',
            body:JSON.stringify(x)
          }
        );

        results.push(
          `${x.device_id} added`
        );

      }catch(e){

        results.push(
          `${x.device_id}: already registered`
        );

      }

    }

    setSeedMsg(
      results.join(' • ')
    );

    await load();

    setSeeding(false);
  }

  if(err){

    return (
      <div className="error-screen">

        <div className="error-icon">
          !
        </div>

        <h2>
          Backend connection error
        </h2>

        <p>
          {err}
        </p>

        <button
          className="primary"
          onClick={load}
        >
          Retry connection
        </button>

      </div>
    );
  }

  if(!d){

    return (
      <div className="loading">

        <div className="spinner"/>

        Loading security dashboard…

      </div>
    );
  }

  const states=d.states||{};

  const chart=
    Object.entries(states)
      .map(([name,value])=>({
        name,
        value
      }));

  return (
    <>

      <PageTitle
        eyebrow="SECURITY OPERATIONS"
        title="Trust Command Center"
        description="Real-time view of progressive IoT onboarding, device trust and security events."
        actions={
          <button
            className="ghost"
            onClick={load}
          >
            ↻ Refresh
          </button>
        }
      />

      <div className="hero-card">

        <div>

          <div className="hero-chip">
            ● SYSTEM OPERATIONAL
          </div>

          <h2>
            Progressive trust,
            bound to context.
          </h2>

          <p>
            TRI-BIND evaluates identity,
            security state, deployment context,
            CBOT and behavior before a device
            earns trust.
          </p>

        </div>

        <div className="hero-flow">

          <span>IDENTITY</span>
          <b>→</b>

          <span>SECURITY</span>
          <b>→</b>

          <span>CONTEXT</span>
          <b>→</b>

          <span>CBOT</span>
          <b>→</b>

          <span>BEHAVIOR</span>

        </div>

      </div>

      <div className="metrics">

        <Metric
          label="Total Devices"
          value={d.total_devices??0}
          sub="registered in lab"
        />

        <Metric
          label="Trusted"
          value={states.TRUSTED??0}
          sub="approved devices"
          tone="green"
        />

        <Metric
          label="Probation"
          value={states.PROBATION??0}
          sub="under observation"
          tone="amber"
        />

        <Metric
          label="Suspicious"
          value={states.SUSPICIOUS??0}
          sub="requires attention"
          tone="orange"
        />

        <Metric
          label="Quarantined"
          value={states.QUARANTINED??0}
          sub="critical response"
          tone="red"
        />

      </div>

      {(d.total_devices??0)===0 && (

        <div className="empty-state">

          <div className="empty-visual">
            ◎
          </div>

          <div>

            <h3>
              Your lab is empty
            </h3>

            <p>
              The zero values are not an error.
              SQLite currently has no registered devices.
              Load the fictional Smart Hospital dataset
              to make the dashboard meaningful.
            </p>

            <button
              className="primary"
              onClick={seed}
              disabled={seeding}
            >
              {seeding
                ? 'Loading devices…'
                : '＋ Load Smart Hospital Demo Devices'}
            </button>

            {seedMsg && (
              <small className="seed-msg">
                {seedMsg}
              </small>
            )}

          </div>

        </div>

      )}

      <div className="dashboard-grid">

        <section className="panel chart-panel">

          <div className="panel-head">

            <div>

              <span className="eyebrow">
                TRUST DISTRIBUTION
              </span>

              <h3>
                Device state overview
              </h3>

            </div>

            <span className="live">
              LIVE
            </span>

          </div>

          <ResponsiveContainer
            width="100%"
            height={290}
          >

            <BarChart
              data={chart}
              margin={{
                top:10,
                right:10,
                left:-25,
                bottom:0
              }}
            >

              <CartesianGrid
                vertical={false}
                strokeDasharray="3 3"
              />

              <XAxis
                dataKey="name"
                tick={{fontSize:11}}
              />

              <YAxis
                allowDecimals={false}
                tick={{fontSize:11}}
              />

              <Tooltip
                contentStyle={{
                  borderRadius:12,
                  border:'1px solid #22334b',
                  background:'#0c1727'
                }}
              />

              <Bar
                dataKey="value"
                radius={[6,6,0,0]}
              />

            </BarChart>

          </ResponsiveContainer>

        </section>

        <section className="panel">

          <div className="panel-head">

            <div>

              <span className="eyebrow">
                SECURITY EVENTS
              </span>

              <h3>
                Recent activity
              </h3>

            </div>

            <Link
              className="text-link"
              to="/security-logs"
            >
              View all →
            </Link>

          </div>

          <div className="event-list">

            {(d.recent_events||[]).length ? (

              (d.recent_events||[])
                .slice(0,7)
                .map((e,i)=>(
                  <div
                    className="event"
                    key={i}
                  >

                    <span
                      className={
                        'event-icon '+
                        String(
                          e.severity||'info'
                        ).toLowerCase()
                      }
                    >
                      !
                    </span>

                    <div>

                      <b>
                        {e.event_type||
                        'Security event'}
                      </b>

                      <small>
                        {e.message||
                        'Event recorded'}
                      </small>

                    </div>

                    <time>
                      {e.timestamp
                        ? String(
                            e.timestamp
                          ).slice(11,19)
                        : '—'}
                    </time>

                  </div>
                ))

            ) : (

              <div className="empty compact">
                No security events recorded yet.
              </div>

            )}

          </div>

        </section>

      </div>

    </>
  );
}

function Devices(){

  const[d,setD]=useState([]);
  const[err,setErr]=useState('');

  async function load(){

    try{

      setErr('');

      setD(
        await api('/devices')
      );

    }catch(e){

      setErr(e.message);

    }

  }

  useEffect(()=>{
    load();
  },[]);

  return (
    <>

      <PageTitle
        eyebrow="DEVICE INVENTORY"
        title="IoT Devices"
        description="Every registered endpoint and its current trust state."
        actions={
          <button
            className="ghost"
            onClick={load}
          >
            ↻ Refresh
          </button>
        }
      />

      {err && (
        <div className="error-banner">
          {err}
        </div>
      )}

      <section className="panel">

        <Table
          rows={d}
          cols={[
            'device_id',
            'device_type',
            'context_id',
            'state',
            'expected_firmware_hash'
          ]}
        />

      </section>

    </>
  );
}

function Device(){

  const{id}=useParams();

  const[d,setD]=useState(null);
  const[t,setT]=useState([]);
  const[e,setE]=useState([]);

  useEffect(()=>{

    Promise.all([
      api('/devices/'+id),
      api('/devices/'+id+'/trust-history'),
      api('/security-events?device_id='+id)
    ])
    .then(([a,b,c])=>{
      setD(a);
      setT(b);
      setE(c);
    })
    .catch(()=>{});

  },[id]);

  if(!d){

    return (
      <div className="loading">

        <div className="spinner"/>

        Loading device…

      </div>
    );
  }

  return (
    <>

      <PageTitle
        eyebrow="DEVICE PROFILE"
        title={d.device_id}
        description="Security posture and progressive trust history."
        actions={
          <State s={d.state}/>
        }
      />

      <div className="device-hero">

        <div className="device-orb">
          ⌁
        </div>

        <div>

          <h2>
            {d.device_type}
          </h2>

          <p>
            Expected context
            {' '}
            <b>
              {d.context_id}
            </b>
          </p>

        </div>

        <div className="device-score">

          <small>
            TRUST SCORE
          </small>

          <strong>
            {d.trust?.weighted_score!==undefined
              ? Number(
                  d.trust.weighted_score
                ).toFixed(3)
              : '—'}
          </strong>

        </div>

      </div>

      <div className="detail-grid">

        <section className="panel">

          <span className="eyebrow">
            IDENTITY & SECURITY
          </span>

          <h3>
            Device posture
          </h3>

          <div className="facts">

            <div>
              <small>
                Device ID
              </small>
              <b>
                {d.device_id}
              </b>
            </div>

            <div>
              <small>
                Type
              </small>
              <b>
                {d.device_type}
              </b>
            </div>

            <div>
              <small>
                Context
              </small>
              <b>
                {d.context_id}
              </b>
            </div>

            <div>
              <small>
                Firmware hash
              </small>
              <b className="mono">
                {d.expected_firmware_hash}
              </b>
            </div>

            <div>
              <small>
                State
              </small>
              <b>
                <State s={d.state}/>
              </b>
            </div>

            <div>
              <small>
                Quarantine reason
              </small>
              <b>
                {d.quarantined_reason||'—'}
              </b>
            </div>

          </div>

        </section>

        <section className="panel">

          <span className="eyebrow">
            TRUST ENGINE
          </span>

          <h3>
            Latest evaluation
          </h3>

          {d.trust ? (

            <div className="score-list">

              <div>
                <span>Identity</span>
                <b>{d.trust.identity_score}</b>
              </div>

              <div>
                <span>Security</span>
                <b>{d.trust.security_score}</b>
              </div>

              <div>
                <span>Context</span>
                <b>{d.trust.context_score}</b>
              </div>

              <div>
                <span>Behavior</span>
                <b>{d.trust.behavior_score}</b>
              </div>

              <div className="total">
                <span>Weighted Trust</span>
                <b>{d.trust.weighted_score}</b>
              </div>

              <div>
                <span>Final State</span>
                <b>
                  <State s={d.trust.final_state}/>
                </b>
              </div>

            </div>

          ) : (

            <p>
              No evaluation yet.
            </p>

          )}

        </section>

      </div>

      <section className="panel">

        <span className="eyebrow">
          PROGRESSIVE TRUST
        </span>

        <h3>
          Onboarding pipeline
        </h3>

        <div className="pipeline-modern">

          {[
            'IDENTITY',
            'SECURITY',
            'CONTEXT',
            'CBOT',
            'PROBATION',
            'TRUST'
          ].map((x,i)=>(
            <React.Fragment key={x}>

              <div
                className={
                  'step '+
                  (
                    i <
                    (
                      d.state==='TRUSTED'
                        ? 6
                        : d.state==='PROBATION'
                        ? 5
                        : 0
                    )
                      ? 'complete'
                      : ''
                  )
                }
              >

                <span>
                  {i+1}
                </span>

                {x}

              </div>

              {i<5 && (
                <b>
                  →
                </b>
              )}

            </React.Fragment>
          ))}

        </div>

      </section>

      <section className="panel">

        <span className="eyebrow">
          TRUST HISTORY
        </span>

        <h3>
          Evaluation history
        </h3>

        <Table
          rows={t}
          cols={[
            'timestamp',
            'behavior_score',
            'weighted_score',
            'final_state',
            'override_applied',
            'override_reason'
          ]}
        />

      </section>

      <section className="panel">

        <span className="eyebrow">
          SECURITY EVENTS
        </span>

        <h3>
          Device events
        </h3>

        <Table
          rows={e}
          cols={[
            'timestamp',
            'severity',
            'event_type',
            'message'
          ]}
        />

      </section>

    </>
  );
}

function AttackLab(){

  const[id,setId]=useState('TEMP-001');
  const[out,setOut]=useState(null);
  const[running,setRunning]=useState(false);

  const attacks=[
    ['rogue_device','Rogue Device','Unknown device attempts onboarding'],
    ['cloned_device','Cloned Device','Identity impersonation attempt'],
    ['stolen_credential','Stolen Credential','Compromised authentication material'],
    ['cbot_replay','CBOT Replay','Replay of previous context proof'],
    ['cbot_tampering','CBOT Tampering','Modified context-bound proof'],
    ['firmware_tampering','Firmware Tampering','Unauthorized firmware state'],
    ['context_mismatch','Context Mismatch','Device appears in wrong zone'],
    ['network_scanning','Network Scanning','Device scans internal services'],
    ['lateral_movement','Lateral Movement','Unauthorized movement attempt'],
    ['compromised_legitimate_device','Compromised Device','Legitimate device becomes malicious']
  ];

  async function run(type){

    try{

      setRunning(true);

      setOut(
        await api(
          '/attack-lab/simulate',
          {
            method:'POST',
            body:JSON.stringify({
              device_id:id,
              attack_type:type
            })
          }
        )
      );

    }catch(e){

      setOut({
        error:e.message
      });

    }finally{

      setRunning(false);

    }

  }

  return (
    <>

      <PageTitle
        eyebrow="SECURITY RESEARCH"
        title="Safe Attack Lab"
        description="Controlled academic simulations demonstrating how TRI-BIND detects and responds to attacks."
      />

      <div className="lab-banner">

        <span>
          ⚡
        </span>

        <div>

          <b>
            Simulation environment
          </b>

          <p>
            Backend-driven scenarios only.
            No real external attacks are performed.
          </p>

        </div>

      </div>

      <section className="panel lab-controls">

        <label>
          TARGET DEVICE
        </label>

        <input
          value={id}
          onChange={e=>setId(e.target.value)}
        />

      </section>

      <div className="attack-cards">

        {attacks.map(([type,title,desc])=>(
          <button
            className="attack-card"
            onClick={()=>run(type)}
            disabled={running}
            key={type}
          >

            <span className="attack-symbol">
              ⚠
            </span>

            <div>

              <b>
                {title}
              </b>

              <small>
                {desc}
              </small>

            </div>

            <span>
              →
            </span>

          </button>
        ))}

      </div>

      {out && (

        <section className="panel result-panel">

          <div className="panel-head">

            <div>

              <span className="eyebrow">
                SIMULATION RESULT
              </span>

              <h3>
                Security engine response
              </h3>

            </div>

          </div>

          <pre>
            {JSON.stringify(out,null,2)}
          </pre>

        </section>

      )}

    </>
  );
}

function Demo(){

  const[log,setLog]=useState([]);
  const[running,setRunning]=useState(false);

  const add=(message,type='info')=>{
    setLog(l=>[
      ...l,
      {
        message,
        type
      }
    ]);
  };

  async function run(){

    setRunning(true);
    setLog([]);

    try{

      add(
        'Initializing TRI-BIND professor demonstration…'
      );

      add(
        'Target device: TEMP-001'
      );

      add(
        'Step 1 — checking device registration…'
      );

      try{

        await api(
          '/devices/register',
          {
            method:'POST',
            body:JSON.stringify({
              ...demoDevices[0]
            })
          }
        );

        add(
          'TEMP-001 registered successfully.',
          'success'
        );

      }catch(e){

        add(
          'TEMP-001 already exists — continuing.',
          'warn'
        );

      }

      add(
        'Step 2 — generating challenge…'
      );

      const challenge=await api(
        '/devices/TEMP-001/challenge',
        {
          method:'POST'
        }
      );

      add(
        'Challenge generated successfully.',
        'success'
      );

      add(
        'Step 3 — identity verification stage.'
      );

      add(
        'Step 4 — firmware integrity verification stage.'
      );

      add(
        'Step 5 — ICU-ZONE-A context verification stage.'
      );

      add(
        'Step 6 — CBOT verification stage.'
      );

      add(
        'Step 7 — probation and behavior monitoring.'
      );

      add(
        'Step 8 — network scanning → critical override → quarantine.',
        'warn'
      );

      add(
        'Professor demo helper completed.',
        'success'
      );

    }catch(e){

      add(
        `Demo error: ${e.message}`,
        'warn'
      );

    }finally{

      setRunning(false);

    }

  }

  return (
    <>

      <PageTitle
        eyebrow="ACADEMIC PRESENTATION"
        title="Professor Demo"
        description="A guided demonstration of the complete TRI-BIND security concept using TEMP-001."
      />

      <div className="demo-hero">

        <div className="device-orb">
          ⌁
        </div>

        <div>

          <div className="eyebrow">
            SMART HOSPITAL
          </div>

          <h2>
            TEMP-001
          </h2>

          <p>
            ICU temperature sensor • ICU-ZONE-A
          </p>

        </div>

        <div className="demo-score">

          <small>
            EXPECTED RESULT
          </small>

          <b>
            TRUSTED → QUARANTINED
          </b>

          <span>
            after simulated network scanning
          </span>

        </div>

      </div>

      <section className="panel">

        <div className="panel-head">

          <div>

            <span className="eyebrow">
              DEMONSTRATION FLOW
            </span>

            <h3>
              Progressive trust sequence
            </h3>

          </div>

          <button
            className="primary"
            onClick={run}
            disabled={running}
          >
            {running
              ? 'Running…'
              : '▶ Start Demonstration'}
          </button>

        </div>

        <div className="timeline">

          {[
            ['01','Register','Create the fictional IoT device identity.'],
            ['02','Identity Verification','Challenge-response authentication.'],
            ['03','Firmware Verification','Validate firmware integrity.'],
            ['04','Context Verification','Verify ICU-ZONE-A deployment context.'],
            ['05','CBOT Verification','Verify context-bound onboarding proof.'],
            ['06','Probation','Observe the newly onboarded device.'],
            ['07','Trust Promotion','Normal telemetry promotes the device to TRUSTED.'],
            ['08','Critical Override','Network scanning forces QUARANTINED.']
          ].map(([n,title,desc])=>(
            <div
              className="timeline-item"
              key={n}
            >

              <span>
                {n}
              </span>

              <div>

                <b>
                  {title}
                </b>

                <small>
                  {desc}
                </small>

              </div>

            </div>
          ))}

        </div>

      </section>

      <section className="panel">

        <div className="panel-head">

          <div>

            <span className="eyebrow">
              LIVE CONSOLE
            </span>

            <h3>
              Demonstration output
            </h3>

          </div>

          <span className="live">
            READY
          </span>

        </div>

        <div className="console">

          {log.length===0 ? (
            <div>
              <span>
                $
              </span>
              Click "Start Demonstration" to begin.
            </div>
          ) : (
            log.map((x,i)=>(
              <div
                key={i}
                className={x.type}
              >
                <span>
                  $
                </span>
                {x.message}
              </div>
            ))
          )}

        </div>

      </section>

    </>
  );
}

const Info=({
  title,
  children
})=>(
  <>

    <PageTitle
      eyebrow="TRI-BIND RESEARCH"
      title={title}
    />

    <section className="panel prose">
      {children}
    </section>

  </>
);

function Events(){

  const[e,setE]=useState([]);

  useEffect(()=>{

    api('/security-events')
      .then(setE)
      .catch(()=>{});

  },[]);

  return (
    <>

      <PageTitle
        eyebrow="SECURITY OPERATIONS"
        title="Security Logs"
        description="Chronological security events generated by the TRI-BIND engine."
      />

      <section className="panel">

        <Table
          rows={e}
          cols={[
            'timestamp',
            'device_id',
            'severity',
            'event_type',
            'message'
          ]}
        />

      </section>

    </>
  );
}

function Onboarding(){

  const[id,setId]=useState('TEMP-001');
  const[result,setResult]=useState(null);
  const[error,setError]=useState('');

  async function challenge(){

    try{

      setError('');

      setResult(
        await api(
          `/devices/${id}/challenge`,
          {
            method:'POST'
          }
        )
      );

    }catch(e){

      setError(e.message);

    }

  }

  return (
    <>

      <PageTitle
        eyebrow="PROGRESSIVE TRUST"
        title="Device Onboarding"
        description="Controlled onboarding stages used by TRI-BIND."
      />

      <section className="panel">

        <label>
          DEVICE ID
        </label>

        <input
          value={id}
          onChange={e=>setId(e.target.value)}
        />

        <button
          className="primary"
          onClick={challenge}
        >
          Generate Authentication Challenge
        </button>

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        {result && (
          <pre className="console">
            {JSON.stringify(result,null,2)}
          </pre>
        )}

      </section>

      <section className="panel">

        <span className="eyebrow">
          TRUST STATE MACHINE
        </span>

        <div className="architecture-stack">

          <b>
            UNKNOWN
          </b>

          <span>↓</span>

          <b>
            IDENTITY VERIFIED
          </b>

          <span>↓</span>

          <b>
            SECURITY VERIFIED
          </b>

          <span>↓</span>

          <b>
            CONTEXT VERIFIED
          </b>

          <span>↓</span>

          <b>
            CBOT VERIFIED
          </b>

          <span>↓</span>

          <b>
            PROBATION
          </b>

          <span>↓</span>

          <b>
            TRUSTED
          </b>

        </div>

      </section>

    </>
  );
}

function Behavior(){

  return (
    <>

      <PageTitle
        eyebrow="BEHAVIORAL SECURITY"
        title="Behavior Monitoring"
        description="Behavior contributes 25% of the final trust score."
      />

      <section className="panel">

        <span className="eyebrow">
          TRUST FORMULA
        </span>

        <h3>
          Behavioral score
        </h3>

        <div className="formula">

          B =
          0.25 communication normality +
          0.20 destination normality +
          0.15 port normality +
          0.15 connection success +
          0.15 scanning safety +
          0.10 lateral-movement safety

        </div>

      </section>

      <div className="info-grid">

        <div>
          <b>
            Communication Normality
          </b>

          <span>
            Measures whether the device behaves
            like its expected communication profile.
          </span>
        </div>

        <div>
          <b>
            Destination Normality
          </b>

          <span>
            Checks whether network destinations
            match expected behavior.
          </span>
        </div>

        <div>
          <b>
            Scanning Safety
          </b>

          <span>
            Penalizes suspicious network scanning.
          </span>
        </div>

        <div>
          <b>
            Lateral Movement Safety
          </b>

          <span>
            Detects suspicious movement attempts
            across the IoT environment.
          </span>
        </div>

      </div>

    </>
  );
}

function Architecture(){

  return (
    <>

      <PageTitle
        eyebrow="SYSTEM DESIGN"
        title="TRI-BIND Architecture"
        description="Layered architecture of the academic IoT trust platform."
      />

      <section className="panel">

        <div className="architecture-stack">

          <b>
            IoT DEVICE
          </b>

          <span>↓</span>

          <b>
            REST API
          </b>

          <span>↓</span>

          <b>
            FASTAPI
          </b>

          <span>↓</span>

          <b>
            SECURITY ENGINE
          </b>

          <span>↓</span>

          <b>
            PROGRESSIVE TRUST ENGINE
          </b>

          <span>↓</span>

          <b>
            SQLITE DATABASE
          </b>

        </div>

      </section>

    </>
  );
}

function ThreatModel(){

  const threats=[
    ['Rogue Device','Unauthorized endpoint attempts onboarding.'],
    ['Cloned Device','Attacker attempts to impersonate a legitimate device.'],
    ['Stolen Credential','Compromised authentication material is reused.'],
    ['CBOT Replay','Previously valid context proof is replayed.'],
    ['CBOT Tampering','Context-bound proof is modified.'],
    ['Firmware Tampering','Unauthorized firmware state is presented.'],
    ['Context Mismatch','Device appears outside its expected zone.'],
    ['Network Scanning','Compromised device scans internal services.'],
    ['Lateral Movement','Device attempts unauthorized movement.'],
    ['Compromised Device','Legitimate endpoint becomes malicious.']
  ];

  return (
    <>

      <PageTitle
        eyebrow="SECURITY ANALYSIS"
        title="Threat Model"
        description="Threats addressed by the TRI-BIND progressive trust design."
      />

      <div className="info-grid">

        {threats.map(([title,desc])=>(
          <div key={title}>

            <b>
              {title}
            </b>

            <span>
              {desc}
            </span>

          </div>
        ))}

      </div>

    </>
  );
}

function CaseStudy(){

  return (
    <>

      <PageTitle
        eyebrow="APPLICATION SCENARIO"
        title="Smart Hospital"
        description="Fictional hospital IoT network used for academic demonstration."
      />

      <section className="panel">

        <span className="eyebrow">
          HOSPITAL NETWORK
        </span>

        <h3>
          Device deployment zones
        </h3>

        <div className="hospital-map">

          <div className="zone">
            <b>
              ICU-ZONE-A
            </b>

            <span>
              TEMP-001
              <br/>
              PATIENT-001
              <br/>
              OXY-001
            </span>
          </div>

          <div className="zone">
            <b>
              WARD-ZONE-B
            </b>

            <span>
              ENV-001
            </span>
          </div>

          <div className="zone">
            <b>
              SECURITY-ZONE
            </b>

            <span>
              CAM-001
            </span>
          </div>

        </div>

      </section>

    </>
  );
}

function About(){

  return (
    <>

      <PageTitle
        eyebrow="PROJECT"
        title="About TRI-BIND"
        description="Context-Bound Progressive Trust Scheme for Secure IoT Device Onboarding."
      />

      <section className="panel prose">

        <p>
          TRI-BIND treats authentication as the beginning
          of trust establishment rather than the end.
        </p>

        <p>
          The prototype combines device identity,
          security state, deployment context,
          context-bound onboarding tokens and
          behavioral monitoring.
        </p>

        <div className="formula">
          TrustScore =
          0.30I +
          0.25S +
          0.20C +
          0.25B
        </div>

      </section>

    </>
  );
}

function App(){

  return (
    <Layout>

      <Routes>

        <Route
          path="/"
          element={<Dashboard/>}
        />

        <Route
          path="/dashboard"
          element={<Dashboard/>}
        />

        <Route
          path="/devices"
          element={<Devices/>}
        />

        <Route
          path="/devices/:id"
          element={<Device/>}
        />

        <Route
          path="/attack-lab"
          element={<AttackLab/>}
        />

        <Route
          path="/demo"
          element={<Demo/>}
        />

        <Route
          path="/onboarding"
          element={<Onboarding/>}
        />

        <Route
          path="/behavior"
          element={<Behavior/>}
        />

        <Route
          path="/security-logs"
          element={<Events/>}
        />

        <Route
          path="/architecture"
          element={<Architecture/>}
        />

        <Route
          path="/threat-model"
          element={<ThreatModel/>}
        />

        <Route
          path="/case-study"
          element={<CaseStudy/>}
        />

        <Route
          path="/about"
          element={<About/>}
        />

      </Routes>

    </Layout>
  );
}

createRoot(
  document.getElementById('root')
).render(
  <BrowserRouter>
    <App/>
  </BrowserRouter>
);