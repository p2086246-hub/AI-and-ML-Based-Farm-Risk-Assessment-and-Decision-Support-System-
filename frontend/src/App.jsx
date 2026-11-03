import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import {
  Sprout, LayoutDashboard, MapPinned, ScanLine, History as HistoryIcon, Info,
  Languages, LogOut, CloudSun, Droplets, Leaf, ShieldCheck, Volume2,
  RefreshCw, BrainCircuit, Eye, EyeOff, Smartphone, KeyRound, Camera,
  Images, Navigation, Search, CalendarDays, ExternalLink, Trash2, CheckCircle2,
  AlertTriangle, X, RotateCcw, CircleGauge, FlaskConical, MapPin, Droplet,
  ChevronRight, ThermometerSun, Wind, Gauge, CloudRain, Sunrise, Sunset, Cloud,
  Umbrella, Beaker, ShieldAlert, Sparkles, TrendingDown, TrendingUp, SlidersHorizontal, LocateFixed,
  ListChecks, CalendarCheck2, Activity
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { T, ACTIONS } from './i18n.js';
import {
  IRRIGATION_TYPES, IRRIGATION_SOURCES, SOILS, PLANT_PARTS,
  stagesForCrop, stageLabel, irrigationLabel, sourceLabel, soilLabel
} from './farmOptions.js';

const API = 'http://127.0.0.1:8000/api/v1';
const client = axios.create({ baseURL: API, timeout: 30000 });
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('agritech_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function localizeError(detail, t) {
  const text = String(detail || '').toLowerCase();
  if (text.includes('invalid mobile') || (text.includes('invalid') && text.includes('password'))) return t.invalidLogin;
  if (text.includes('already registered')) return t.mobileExists;
  if (text.includes('no account') || text.includes('account not found')) return t.accountNotFound;
  if (text.includes('incorrect otp')) return t.incorrectOtp;
  if (text.includes('otp has expired') || text.includes('otp expired')) return t.otpExpired;
  if (text.includes('wait') && text.includes('otp')) return t.waitOtp;
  return t.requestFailed;
}

function statusLabel(status, t) {
  return status === 'HIGH' ? t.high : status === 'MODERATE' ? t.moderate : status === 'LOW' ? t.low : t.noAssessment;
}

function priorityLabel(priority, t) {
  if (priority === 'IMMEDIATE') return t.immediate;
  if (priority === 'TODAY') return t.today;
  if (priority === 'NEXT_2_3_DAYS') return t.nextDays;
  return t.routine;
}

function visualLabel(label, t) {
  return t[`visual_${label}`] || label?.replaceAll('_', ' ') || '';
}

function warningLabel(code, t) {
  return t[`warning_${code}`] || code?.replaceAll('_', ' ') || '';
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('agritech_token'));
  const [lang, setLang] = useState(localStorage.getItem('agritech_lang') || 'en');
  const [page, setPage] = useState('dashboard');
  const [farms, setFarms] = useState([]);
  const [farmId, setFarmIdState] = useState(() => Number(localStorage.getItem('agritech_farm_id')) || null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [latestScan, setLatestScan] = useState(null);
  const [msg, setMsg] = useState('');
  const t = T[lang];

  const setFarmId = (id) => {
    const value = id ? Number(id) : null;
    setFarmIdState(value);
    if (value) localStorage.setItem('agritech_farm_id', String(value));
    else localStorage.removeItem('agritech_farm_id');
    setResult(null);
  };

  useEffect(() => localStorage.setItem('agritech_lang', lang), [lang]);
  useEffect(() => { if (token) loadFarms(); }, [token]);
  useEffect(() => { if (token && farmId) loadLatestScan(farmId); else setLatestScan(null); }, [token, farmId]);

  async function loadFarms(preferredId = null) {
    try {
      const { data } = await client.get('/farms');
      setFarms(data);
      const stored = Number(localStorage.getItem('agritech_farm_id')) || null;
      const candidates = [preferredId, farmId, stored, data[0]?.id].filter(Boolean).map(Number);
      const next = candidates.find((id) => data.some((farm) => farm.id === id)) ?? null;
      setFarmIdState(next);
      if (next) localStorage.setItem('agritech_farm_id', String(next));
      else localStorage.removeItem('agritech_farm_id');
      return data;
    } catch (error) {
      if (error.response?.status === 401) logout();
      return [];
    }
  }

  async function loadLatestScan(id = farmId) {
    if (!id) return setLatestScan(null);
    try {
      const { data } = await client.get(`/disease/latest/${id}`);
      setLatestScan(data || null);
    } catch {
      setLatestScan(null);
    }
  }

  function logout() {
    localStorage.removeItem('agritech_token');
    localStorage.removeItem('agritech_farm_id');
    setToken(null); setFarms([]); setFarmIdState(null); setResult(null); setLatestScan(null);
  }

  function authenticated(data) {
    localStorage.setItem('agritech_token', data.token);
    setToken(data.token);
  }

  async function onFarmSaved(newFarm) {
    await loadFarms(newFarm.id);
    setFarmId(newFarm.id);
    setMsg(t.farmSaved);
  }

  async function onFarmDeleted(id) {
    try {
      await client.delete(`/farms/${id}`);
      if (Number(farmId) === Number(id)) setFarmId(null);
      await loadFarms();
    } catch {
      setMsg(t.requestFailed);
    }
  }

  async function loadHistory(id = farmId) {
    if (!id) { setHistory([]); return; }
    try {
      const { data } = await client.get(`/assessments/history/${id}`);
      setHistory(data);
    } catch { setHistory([]); }
  }

  if (!token) return <Auth t={t} lang={lang} setLang={setLang} onAuth={authenticated} />;

  const current = farms.find((farm) => farm.id === Number(farmId)) || null;
  const pageTitle = page === 'dashboard' ? t.dashboard : page === 'farm' ? t.farm : page === 'plant' ? t.plantAI : page === 'actionplan' ? t.actionPlan : page === 'history' ? t.history : t.about;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <img className="brandLogoFull" src="/agritech-logo.png" alt="AgriTech" />
        </div>
        <nav>
          {[
            ['dashboard', LayoutDashboard, t.dashboard],
            ['farm', MapPinned, t.farm],
            ['plant', ScanLine, t.plantAI],
            ['actionplan', ListChecks, t.actionPlan],
            ['history', HistoryIcon, t.history],
            ['about', Info, t.about],
          ].map(([id, Icon, label]) => (
            <button key={id} onClick={() => { setPage(id); if (id === 'history') loadHistory(); }} className={page === id ? 'active' : ''}>
              <Icon size={18} />{label}
            </button>
          ))}
        </nav>
        <div className="sidebottom">
          <label><Languages size={16} /><LanguageSelect lang={lang} setLang={setLang} /></label>
          <button onClick={logout}><LogOut size={17} />{t.logout}</button>
        </div>
      </aside>

      <main className="main">
        <header className="appHeader">
          <div className="headerTitleWrap"><img className="headerLogo" src="/agritech-icon.png" alt="AgriTech"/><div><span className="eyebrow">{t.eyebrow}</span><h1>{pageTitle}</h1></div></div>
          <div className="headercontrols">
            <div className="mobilelang"><Languages size={16} /><LanguageSelect lang={lang} setLang={setLang} /></div>
            {farms.length > 0 && (
              <select className="farmselect" value={farmId ?? ''} onChange={(e) => setFarmId(e.target.value)}>
                {farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name} • {farm.crop}</option>)}
              </select>
            )}
          </div>
        </header>

        {msg && <div className="toast" onClick={() => setMsg('')}>{msg}<X size={14} /></div>}

        {page === 'dashboard' && (
          <Dashboard
            t={t} lang={lang} farm={current} result={result} onResult={setResult}
            latestScan={latestScan} refreshScan={loadLatestScan} setMsg={setMsg}
            goToFarm={() => setPage('farm')} goToPlant={() => setPage('plant')}
          />
        )}
        {page === 'farm' && (
          <FarmPage t={t} lang={lang} farms={farms} activeFarmId={farmId} setActiveFarm={setFarmId}
            onSaved={onFarmSaved} onDelete={onFarmDeleted} setMsg={setMsg} />
        )}
        {page === 'plant' && (
          <PlantAIPage t={t} lang={lang} farm={current} setMsg={setMsg} onScan={(scan) => { setLatestScan(scan); setMsg(t.scanCompleted); }} />
        )}
        {page === 'actionplan' && <ActionPlanPage t={t} lang={lang} farm={current} setMsg={setMsg} />}
        {page === 'history' && <HistoryPage t={t} lang={lang} data={history} />}
        {page === 'about' && <AboutPage t={t} />}
      </main>
    </div>
  );
}

function LanguageSelect({ lang, setLang }) {
  return (
    <select value={lang} onChange={(e) => setLang(e.target.value)} aria-label="Language">
      <option value="en">English</option><option value="hi">हिंदी</option><option value="mr">मराठी</option><option value="gu">ગુજરાતી</option>
    </select>
  );
}

function Auth({ t, lang, setLang, onAuth }) {
  const [mode, setMode] = useState('login');
  const [login, setLogin] = useState({ mobile_no: '', password: '' });
  const [form, setForm] = useState({ name: '', mobile_no: '', password: '', confirmPassword: '', otp: '' });
  const [otpSent, setOtpSent] = useState(false);
  const [verifiedToken, setVerifiedToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [err, setErr] = useState('');

  function changeMode(next) {
    setMode(next); setOtpSent(false); setVerifiedToken(''); setErr(''); setNotice('');
    setForm({ name: '', mobile_no: '', password: '', confirmPassword: '', otp: '' });
  }

  async function doLogin(e) {
    e.preventDefault(); setBusy(true); setErr('');
    try { const { data } = await axios.post(`${API}/auth/login`, login); onAuth(data); }
    catch (error) { setErr(localizeError(error.response?.data?.detail, t)); }
    finally { setBusy(false); }
  }

  async function doRegister(e) {
    e.preventDefault(); setBusy(true); setErr('');
    try {
      const { data } = await axios.post(`${API}/auth/register`, { name: form.name, mobile_no: form.mobile_no, password: form.password, preferred_language: lang });
      onAuth(data);
    } catch (error) { setErr(localizeError(error.response?.data?.detail, t)); }
    finally { setBusy(false); }
  }

  async function requestForgotOtp() {
    if (!form.mobile_no) return;
    setBusy(true); setErr(''); setNotice('');
    try {
      const { data } = await axios.post(`${API}/auth/request-otp`, { mobile_no: form.mobile_no, purpose: 'forgot_password' });
      setOtpSent(true); setNotice(data.delivery === 'console' ? `${t.otpSent} ${t.consoleOtp}` : t.otpSent);
    } catch (error) { setErr(localizeError(error.response?.data?.detail, t)); }
    finally { setBusy(false); }
  }

  async function verifyForgotOtp() {
    setBusy(true); setErr('');
    try {
      const { data } = await axios.post(`${API}/auth/verify-otp`, { mobile_no: form.mobile_no, purpose: 'forgot_password', otp: form.otp });
      setVerifiedToken(data.verification_token); setNotice(t.otpVerified);
    } catch (error) { setErr(localizeError(error.response?.data?.detail, t)); }
    finally { setBusy(false); }
  }

  async function resetPassword(e) {
    e.preventDefault();
    if (!verifiedToken) return;
    if (form.password !== form.confirmPassword) { setErr(t.passwordMismatch); return; }
    setBusy(true); setErr('');
    try {
      await axios.post(`${API}/auth/reset-password`, { mobile_no: form.mobile_no, new_password: form.password, verification_token: verifiedToken });
      setNotice(t.passwordReset); setTimeout(() => changeMode('login'), 900);
    } catch (error) { setErr(localizeError(error.response?.data?.detail, t)); }
    finally { setBusy(false); }
  }

  return (
    <div className="authPage">
      <div className="authGlow one" /><div className="authGlow two" />
      <div className="authCard">
        <div className="authBrand"><img className="authLogo" src="/agritech-logo.png" alt="AgriTech"/><p>{t.tag}</p></div>
        <div className="langPills">{[['en','EN'],['hi','हिं'],['mr','म'],['gu','ગુ']].map(([id,label]) => <button key={id} className={lang===id?'on':''} onClick={() => setLang(id)}>{label}</button>)}</div>

        {mode === 'login' && <form onSubmit={doLogin}>
          <Field label={t.mobile} value={login.mobile_no} onChange={(v)=>setLogin({...login,mobile_no:v})} placeholder="9876543210" inputMode="tel" />
          <PasswordField label={t.password} value={login.password} onChange={(v)=>setLogin({...login,password:v})} t={t} />
          <button className="primary wide" disabled={busy}>{busy?<RefreshCw className="spin" size={17}/>:<Smartphone size={17}/>} {t.login}</button>
          <button type="button" className="textButton" onClick={()=>changeMode('forgot')}>{t.forgotPassword}</button>
          <div className="authDivider" />
          <button type="button" className="secondary wide" onClick={()=>changeMode('register')}>{t.register}</button>
        </form>}

        {mode === 'register' && <form onSubmit={doRegister}>
          <Field label={t.name} value={form.name} onChange={(v)=>setForm({...form,name:v})} />
          <Field label={t.mobile} value={form.mobile_no} onChange={(v)=>setForm({...form,mobile_no:v})} placeholder="9876543210" inputMode="tel" />
          <PasswordField label={t.password} value={form.password} onChange={(v)=>setForm({...form,password:v})} t={t} />
          <button className="primary wide" disabled={busy}>{busy?<RefreshCw className="spin" size={17}/>:<Sprout size={17}/>} {t.register}</button>
          <button type="button" className="textButton" onClick={()=>changeMode('login')}>{t.backToLogin}</button>
        </form>}

        {mode === 'forgot' && <form onSubmit={resetPassword}>
          <Field label={t.mobile} value={form.mobile_no} onChange={(v)=>{setForm({...form,mobile_no:v});setOtpSent(false);setVerifiedToken('');}} placeholder="9876543210" inputMode="tel" />
          <button type="button" className="secondary wide" onClick={requestForgotOtp} disabled={busy||!form.mobile_no}><Smartphone size={16}/>{otpSent?t.resendOtp:t.sendOtp}</button>
          {otpSent && !verifiedToken && <div className="otpRow"><Field label={t.otp} value={form.otp} onChange={(v)=>setForm({...form,otp:v.replace(/\D/g,'').slice(0,6)})} inputMode="numeric" maxLength={6}/><button type="button" className="secondary verify" onClick={verifyForgotOtp} disabled={busy||form.otp.length!==6}><KeyRound size={16}/>{t.verifyOtp}</button></div>}
          {verifiedToken && <><PasswordField label={t.newPassword} value={form.password} onChange={(v)=>setForm({...form,password:v})} t={t}/><PasswordField label={t.confirmPassword} value={form.confirmPassword} onChange={(v)=>setForm({...form,confirmPassword:v})} t={t}/><button className="primary wide" disabled={busy}>{t.resetPassword}</button></>}
          <button type="button" className="textButton" onClick={()=>changeMode('login')}>{t.backToLogin}</button>
        </form>}
        {notice && <div className="notice">{notice}</div>}{err && <div className="error">{err}</div>}
      </div>
    </div>
  );
}

function PasswordField({ label, value, onChange, t }) {
  const [show, setShow] = useState(false);
  return <label className="field"><span>{label}</span><div className="passwordWrap"><input type={show?'text':'password'} value={value} onChange={(e)=>onChange(e.target.value)} required/><button type="button" onClick={()=>setShow(!show)} title={show?t.hidePassword:t.showPassword}>{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></label>;
}

function Dashboard({ t, lang, farm, result, onResult, latestScan, refreshScan, setMsg, goToFarm, goToPlant }) {
  const [live, setLive] = useState(true);
  const [busy, setBusy] = useState(false);
  const [weather, setWeather] = useState(null);
  const [weatherBusy, setWeatherBusy] = useState(false);
  const [x, setX] = useState({ temperature_c:34, humidity_pct:52, rainfall_next_24h_mm:2, soil_moisture_pct:20, et0_mm:5 });

  useEffect(() => {
    if (farm?.id) {
      refreshScan(farm.id);
      loadWeather();
    } else {
      setWeather(null);
    }
  }, [farm?.id]);

  async function loadWeather() {
    if (!farm?.id) return;
    setWeatherBusy(true);
    try {
      const { data } = await client.get(`/weather/farm/${farm.id}`);
      setWeather(data);
      setX({
        temperature_c: data.temperature_c ?? 34,
        humidity_pct: data.humidity_pct ?? 52,
        rainfall_next_24h_mm: data.rainfall_next_24h_mm ?? 0,
        soil_moisture_pct: data.soil_moisture_pct ?? 20,
        et0_mm: data.et0_mm ?? 4,
      });
    } catch (error) {
      setWeather(null);
      setMsg(error.response?.data?.detail || t.weatherUnavailable);
    } finally { setWeatherBusy(false); }
  }

  async function run() {
    if (!farm) { setMsg(t.createFarmToBegin); goToFarm(); return; }
    setBusy(true);
    try {
      const payload = { farm_id:farm.id, use_live_weather:live };
      if (!live) Object.assign(payload, Object.fromEntries(Object.entries(x).map(([k,v])=>[k,Number(v)])));
      const { data } = await client.post('/assessments/run', payload);
      onResult(data); setMsg(t.assessmentCompleted);
      if (data.weather_snapshot) setWeather(data.weather_snapshot);
    } catch (error) {
      if (live && [422,502].includes(error.response?.status)) { setLive(false); setMsg(t.liveFailed); }
      else setMsg(error.response?.data?.detail || t.assessmentFailed);
    } finally { setBusy(false); }
  }

  if (!farm) return <EmptyState t={t} icon={<MapPinned/>} title={t.createFarmToBegin} button={t.farmSetup} onClick={goToFarm}/>;

  return <>
    <section className="hero">
      <div><span>🌾 {farm.name}</span><h2>{farm.crop} • {stageLabel(farm.crop_stage,t)} • {farm.location}</h2></div>
      <div className="decision"><ShieldCheck/><div><b>{t.decisionSupport}</b><small>{t.whatWhyWhen}</small></div></div>
    </section>

    <WeatherCenter t={t} lang={lang} weather={weather} busy={weatherBusy} onRefresh={loadWeather}/>

    <SmartFarmTools t={t} lang={lang} weather={weather}/>

    <section className="panel photoEvidence">
      <div className="evidenceIcon"><ScanLine/></div>
      <div className="evidenceText"><span className="kicker">{t.photoEvidence}</span>{latestScan?<><b>{displayScanLabel(latestScan.label,t)}</b><small>{latestScan.usable_for_risk?t.photoUsed:t.notUsableInRisk} • {Math.round(latestScan.disease_risk_pct)}% {t.risk}</small></>:<><b>{t.noPhotoEvidence}</b><small>{t.plantModelNote}</small></>}</div>
      <button className="secondary" onClick={goToPlant}><Camera size={16}/>{t.plantAI}<ChevronRight size={16}/></button>
    </section>

    <section className="panel inputs">
      <div className="panelhead"><div><span className="kicker">{t.assessmentInput}</span><h3>{live?t.live:t.manual}</h3></div><label className="switch"><input type="checkbox" checked={live} onChange={(e)=>setLive(e.target.checked)}/><span/></label></div>
      {!live && <div className="formgrid five"><Field label={t.temp} type="number" value={x.temperature_c} onChange={(v)=>setX({...x,temperature_c:v})}/><Field label={t.humidity} type="number" value={x.humidity_pct} onChange={(v)=>setX({...x,humidity_pct:v})}/><Field label={t.rain} type="number" value={x.rainfall_next_24h_mm} onChange={(v)=>setX({...x,rainfall_next_24h_mm:v})}/><Field label={t.soilMoisture} type="number" value={x.soil_moisture_pct} onChange={(v)=>setX({...x,soil_moisture_pct:v})}/><Field label={t.et0} type="number" value={x.et0_mm} onChange={(v)=>setX({...x,et0_mm:v})}/></div>}
      <button className="primary runButton" onClick={run} disabled={busy}>{busy?<RefreshCw className="spin"/>:<BrainCircuit/>}{busy?t.running:t.run}</button>
    </section>
    <RiskSummary t={t} lang={lang} result={result}/>
    <WhatIfSimulator t={t} farm={farm} weather={weather} latestScan={latestScan} currentResult={result} setMsg={setMsg}/>
  </>;
}

function weatherCodeLabel(code, t) {
  const n = Number(code);
  if (n === 0) return t.weatherClear;
  if ([1,2].includes(n)) return t.weatherPartlyCloudy;
  if (n === 3) return t.weatherOvercast;
  if ([45,48].includes(n)) return t.weatherFog;
  if ([51,53,55,56,57].includes(n)) return t.weatherDrizzle;
  if ([61,63,65,66,67,80,81,82].includes(n)) return t.weatherRain;
  if ([71,73,75,77,85,86].includes(n)) return t.weatherSnow;
  if ([95,96,99].includes(n)) return t.weatherThunderstorm;
  return t.weatherMixed;
}

function localeFor(lang) { return ({en:'en-IN',hi:'hi-IN',mr:'mr-IN',gu:'gu-IN'})[lang] || 'en-IN'; }
function shortDate(value, lang) { try { return new Intl.DateTimeFormat(localeFor(lang), {weekday:'short', day:'numeric', month:'short'}).format(new Date(`${value}T12:00:00`)); } catch { return value; } }
function shortTime(value, lang) { if(!value)return '--'; try { return new Intl.DateTimeFormat(localeFor(lang), {hour:'numeric',minute:'2-digit'}).format(new Date(value)); } catch { return value.slice(11,16); } }
function formatDateTime(value, lang) { if(!value)return '--'; try { const normalized=String(value).includes('T')?String(value):String(value).replace(' ','T')+'Z'; return new Intl.DateTimeFormat(localeFor(lang), {day:'2-digit',month:'short',year:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(normalized)); } catch { return String(value); } }

function WeatherCenter({ t, lang, weather, busy, onRefresh, compact=false }) {
  if (busy && !weather) return <section className="panel weatherCenter loadingCard"><RefreshCw className="spin"/><span>{t.loadingWeather}</span></section>;
  if (!weather) return <section className="panel weatherCenter emptyWeather"><CloudSun/><div><b>{t.weatherCenter}</b><span>{t.weatherUnavailable}</span></div><button className="secondary" onClick={onRefresh}><RefreshCw size={16}/>{t.retry}</button></section>;
  const c = weather.current || {};
  const days = weather.daily || [];
  return <section className={`panel weatherCenter ${compact?'compactWeather':''}`}>
    <div className="weatherHead">
      <div><span className="kicker">{t.weatherCenter}</span><h3>{weatherCodeLabel(c.weather_code,t)}</h3><p>{t.weatherAutoNote}</p></div>
      <button className="ghost refreshWeather" onClick={onRefresh} disabled={busy}><RefreshCw className={busy?'spin':''} size={16}/>{t.refresh}</button>
    </div>
    <div className="currentWeather">
      <div className="tempHero"><CloudSun/><div><b>{c.temperature_c==null?'--':Math.round(c.temperature_c)}°</b><span>{t.feelsLike} {c.feels_like_c==null?'--':Math.round(c.feels_like_c)}°C</span></div></div>
      <WeatherMetric icon={<Droplets/>} label={t.humidity} value={c.humidity_pct==null?'--':`${Math.round(c.humidity_pct)}%`}/>
      <WeatherMetric icon={<CloudRain/>} label={t.rainNow} value={c.precipitation_mm==null?'--':`${Number(c.precipitation_mm).toFixed(1)} mm`}/>
      <WeatherMetric icon={<Wind/>} label={t.wind} value={c.wind_kmh==null?'--':`${Math.round(c.wind_kmh)} km/h`}/>
      <WeatherMetric icon={<Gauge/>} label={t.pressure} value={c.pressure_hpa==null?'--':`${Math.round(c.pressure_hpa)} hPa`}/>
      <WeatherMetric icon={<Cloud/>} label={t.cloudCover} value={c.cloud_cover_pct==null?'--':`${Math.round(c.cloud_cover_pct)}%`}/>
      <WeatherMetric icon={<ThermometerSun/>} label={t.uvIndex} value={c.uv_index==null?'--':Number(c.uv_index).toFixed(1)}/>
      <WeatherMetric icon={<LocateFixed/>} label={t.visibility} value={c.visibility_km==null?'--':`${c.visibility_km} km`}/>
      <WeatherMetric icon={<Droplet/>} label={t.soilMoisture} value={c.soil_moisture_pct==null?'--':`${Math.round(c.soil_moisture_pct)}%`}/>
    </div>
    {!compact && <>
      <div className="sunRow"><span><Sunrise size={17}/>{t.sunrise}: <b>{shortTime(days[0]?.sunrise,lang)}</b></span><span><Sunset size={17}/>{t.sunset}: <b>{shortTime(days[0]?.sunset,lang)}</b></span><span><Umbrella size={17}/>{t.todayRain}: <b>{days[0]?.rain_probability_pct ?? '--'}%</b></span></div>
      <div className="forecastTitle"><b>{t.sevenDayForecast}</b><span>{t.weatherForecastHint}</span></div>
      <div className="forecastStrip">{days.map((d)=><div className="forecastDay" key={d.date}><b>{shortDate(d.date,lang)}</b><span>{weatherCodeLabel(d.weather_code,t)}</span><strong>{Math.round(d.max_c ?? 0)}° / {Math.round(d.min_c ?? 0)}°</strong><small><CloudRain size={13}/>{d.rain_probability_pct ?? 0}% • {Number(d.rain_mm ?? 0).toFixed(1)} mm</small></div>)}</div>
    </>}
    <small className="weatherNote">{t.weatherModelNote}</small>
  </section>;
}

function WeatherMetric({icon,label,value}) { return <div className="weatherMetric"><span>{icon}{label}</span><b>{value}</b></div>; }

function SmartFarmTools({t,lang,weather}) {
  if(!weather) return null;
  const spray=weather.spray_window || {};
  const irrigation=weather.irrigation_advice || {};
  const alerts=weather.alerts || [];
  return <section className="smartToolGrid">
    <div className="panel smartTool sprayTool"><div className="toolIcon"><Beaker/></div><div className="toolBody"><span className="kicker">{t.smartSprayWindow}</span><h3>{t[`spray_${spray.status}`]||t.sprayUnavailable}</h3>{spray.start_time&&<p><b>{shortTime(spray.start_time,lang)} – {shortTime(spray.end_time,lang)}</b> • {Math.round(spray.score||0)}/100</p>}<small>{t.sprayWindowNote}</small></div></div>
    <div className="panel smartTool irrigationTool"><div className="toolIcon"><Droplets/></div><div className="toolBody"><span className="kicker">{t.smartIrrigation}</span><h3>{t[`irrigationAdvice_${irrigation.code}`]||t.monitorIrrigation}</h3><p>{t[`irrigationReason_${irrigation.code}`]||t.irrigationGenericReason}</p><small>{t.sensorWeatherCaution}</small></div></div>
    <div className="panel smartTool alertTool"><div className="toolIcon"><ShieldAlert/></div><div className="toolBody"><span className="kicker">{t.farmAlerts}</span>{alerts.length===0?<><h3>{t.noMajorWeatherAlert}</h3><p>{t.keepMonitoringWeather}</p></>:<div className="alertList">{alerts.map((a,i)=><div className={`farmAlert ${a.severity}`} key={`${a.code}-${i}`}><AlertTriangle size={15}/><span>{t[`alert_${a.code}`]||a.code.replaceAll('_',' ')}{a.value!=null?` • ${a.value}${a.unit||''}`:''}</span></div>)}</div>}</div></div>
  </section>;
}

function WhatIfSimulator({t,farm,weather,latestScan,currentResult,setMsg}) {
  const defaults=()=>({
    temperature_c:weather?.temperature_c ?? 34,
    humidity_pct:weather?.humidity_pct ?? 55,
    rainfall_next_24h_mm:weather?.rainfall_next_24h_mm ?? 0,
    soil_moisture_pct:weather?.soil_moisture_pct ?? 25,
    et0_mm:weather?.et0_mm ?? 4,
    disease_probability_pct:latestScan?.usable_for_risk ? latestScan.disease_risk_pct : (currentResult?.risks?.disease ?? 25),
  });
  const [v,setV]=useState(defaults());
  const [out,setOut]=useState(null);
  const [busy,setBusy]=useState(false);
  useEffect(()=>{setV(defaults());setOut(null);},[farm?.id,weather?.current?.time,latestScan?.scan_id]);

  function preset(type){
    if(type==='irrigation')setV((x)=>({...x,soil_moisture_pct:Math.max(40,Number(x.soil_moisture_pct)||0)}));
    if(type==='heat')setV((x)=>({...x,temperature_c:(Number(x.temperature_c)||0)+5,humidity_pct:Math.max(20,(Number(x.humidity_pct)||0)-8)}));
    if(type==='disease')setV((x)=>({...x,disease_probability_pct:Math.min(95,(Number(x.disease_probability_pct)||0)+20)}));
    setOut(null);
  }
  async function simulate(){setBusy(true);try{const payload={farm_id:farm.id,use_live_weather:false,...Object.fromEntries(Object.entries(v).map(([k,val])=>[k,Number(val)]))};const {data}=await client.post('/assessments/simulate',payload);setOut(data);}catch(error){setMsg(error.response?.data?.detail||t.simulationFailed);}finally{setBusy(false);}}
  const base=currentResult?.overall_risk;
  const delta=out&&base!=null?Math.round((out.overall_risk-base)*10)/10:null;
  return <section className="panel simulator">
    <div className="panelhead"><div><span className="kicker">{t.whatIfTitle}</span><h3>{t.whatIfSubtitle}</h3></div><SlidersHorizontal/></div>
    <div className="presetRow"><button className="secondary" onClick={()=>preset('irrigation')}><Droplets size={15}/>{t.presetAfterIrrigation}</button><button className="secondary" onClick={()=>preset('heat')}><ThermometerSun size={15}/>{t.presetHeatwave}</button><button className="secondary" onClick={()=>preset('disease')}><ScanLine size={15}/>{t.presetDiseaseWorse}</button></div>
    <div className="formgrid simulatorGrid"><Field label={t.temp} type="number" value={v.temperature_c} onChange={(x)=>setV({...v,temperature_c:x})}/><Field label={t.humidity} type="number" value={v.humidity_pct} onChange={(x)=>setV({...v,humidity_pct:x})}/><Field label={t.rain} type="number" value={v.rainfall_next_24h_mm} onChange={(x)=>setV({...v,rainfall_next_24h_mm:x})}/><Field label={t.soilMoisture} type="number" value={v.soil_moisture_pct} onChange={(x)=>setV({...v,soil_moisture_pct:x})}/><Field label={t.plantHealthRiskInput} type="number" value={v.disease_probability_pct} onChange={(x)=>setV({...v,disease_probability_pct:x})}/></div>
    <div className="simulationFooter"><button className="primary" onClick={simulate} disabled={busy}>{busy?<RefreshCw className="spin"/>:<Sparkles/>}{t.simulate}</button>{out&&<div className="projectedRisk"><span>{t.projectedRisk}</span><b>{Math.round(out.overall_risk)}/100</b>{delta!=null&&<small className={delta<0?'better':delta>0?'worse':''}>{delta<0?<TrendingDown size={14}/>:null}{delta>0?'+':''}{delta} {t.pointsVsCurrent}</small>}</div>}<small className="simNote">{t.simulationNotSaved}</small></div>
  </section>;
}

function RiskSummary({ t, lang, result }) {
  const tone = (score) => score>=70?'high':score>=40?'moderate':'low';
  const factors = { water_stress:[t.contributorWater,t.reasonWater], weather:[t.contributorWeather,t.reasonWeather], disease:[t.contributorDisease,t.reasonDisease], crop_health:[t.contributorCrop,t.reasonCrop] };
  return <>
    <section className="panel summary">
      <div><span className="kicker">{t.overall}</span><div className={`bigscore ${tone(result?.overall_risk||0)}`}>{result?Math.round(result.overall_risk):'--'}<small>/100</small></div><span className={`status ${tone(result?.overall_risk||0)}`}>{result?statusLabel(result.status,t):t.noAssessment}</span></div>
      <div className="confidence"><span>{t.confidence}</span><b>{result?`${Math.round(result.confidence)}%`:'--'}</b><div><i style={{width:`${result?.confidence||0}%`}}/></div>{result&&<small>{t.rule}: {result.rule_risk} • {t.ml}: {result.ml_risk}</small>}</div>
    </section>
    <section className="riskgrid"><RiskCard icon={<CloudSun/>} name={t.weather} score={result?.risks.weather||0}/><RiskCard icon={<Droplets/>} name={t.water} score={result?.risks.water_stress||0}/><RiskCard icon={<ScanLine/>} name={t.diseaseRisk} score={result?.risks.disease||0}/><RiskCard icon={<Leaf/>} name={t.cropHealth} score={result?.risks.crop_health||0}/></section>
    <section className="twocol">
      <div className="panel"><h3>{t.why}</h3>{!result?<Empty t={t}/>:result.contributors.map((c)=>{const tr=factors[c.factor]||[c.factor,c.reason];return <div className="contrib" key={c.factor}><div><b>{tr[0]}</b><span>{c.contribution}%</span></div><div className="thin"><i style={{width:`${c.contribution}%`}}/></div><p>{tr[1]}</p></div>;})}</div>
      <div className="panel"><h3>{t.actions}</h3>{!result?<Empty t={t}/>:result.actions.map((a,i)=><Action key={i} a={a} lang={lang} t={t}/>)}</div>
    </section>
  </>;
}

function RiskCard({icon,name,score}) { const level=score>=70?'high':score>=40?'moderate':'low'; return <div className="riskcard"><div className="riskicon">{icon}</div><span>{name}</span><b>{Math.round(score)}<small>/100</small></b><div className="bar"><i className={level} style={{width:`${score}%`}}/></div></div>; }

function Action({a,lang,t}) {
  const text=ACTIONS[lang]?.[a.code]||ACTIONS.en[a.code]||[a.title,a.why,a.when];
  const speak=()=>{const u=new SpeechSynthesisUtterance(`${text[0]}. ${text[1]}. ${text[2]}`);u.lang={en:'en-IN',hi:'hi-IN',mr:'mr-IN',gu:'gu-IN'}[lang]||'en-IN';speechSynthesis.cancel();speechSynthesis.speak(u);};
  return <div className="action"><span className={`priority ${a.priority.toLowerCase()}`}>{priorityLabel(a.priority,t)}</span><h4>{text[0]}</h4><p>{text[1]}</p><div><b>⏱ {text[2]}</b><button onClick={speak}><Volume2 size={15}/>{t.listen}</button></div></div>;
}

function FarmPage({ t, lang, farms, activeFarmId, setActiveFarm, onSaved, onDelete, setMsg }) {
  const [f,setF]=useState({ name:'', location:'', latitude:null, longitude:null, crop:'Soybean', crop_stage:'germination_emergence', area_acres:2, soil_type:'Black soil', irrigation_type:'Rainfed', irrigation_source:'Rainfall', sowing_date:'' });
  const [customIrrigation,setCustomIrrigation]=useState('');
  const [customSource,setCustomSource]=useState('');
  const [locating,setLocating]=useState(false);
  const [saving,setSaving]=useState(false);
  const [suggestions,setSuggestions]=useState([]);
  const [searching,setSearching]=useState(false);
  const [previewWeather,setPreviewWeather]=useState(null);
  const [previewBusy,setPreviewBusy]=useState(false);
  const stages=useMemo(()=>stagesForCrop(f.crop),[f.crop]);

  useEffect(()=>{ if(!stages.includes(f.crop_stage)) setF((cur)=>({...cur,crop_stage:stages[0]})); },[f.crop,stages.join('|')]);

  useEffect(()=>{
    const q=f.location.trim();
    if(q.length<2 || f.latitude!=null){setSuggestions([]);return;}
    const timer=setTimeout(async()=>{
      setSearching(true);
      try{const {data}=await client.get('/weather/search',{params:{q,count:6,language:lang}});setSuggestions(data||[]);}catch{setSuggestions([]);}finally{setSearching(false);}
    },350);
    return()=>clearTimeout(timer);
  },[f.location,f.latitude,lang]);

  async function loadPreview(latitude,longitude){
    if(latitude==null||longitude==null)return;
    setPreviewBusy(true);
    try{const {data}=await client.get('/weather/preview',{params:{latitude,longitude}});setPreviewWeather(data);}catch{setPreviewWeather(null);setMsg(t.weatherUnavailable);}finally{setPreviewBusy(false);}
  }

  async function chooseLocation(item){
    const latitude=Number(item.latitude), longitude=Number(item.longitude);
    setF((cur)=>({...cur,location:item.display_name||item.name,latitude,longitude}));
    setSuggestions([]);
    setMsg(t.locationSelectedWeatherLoading);
    await loadPreview(latitude,longitude);
  }

  async function useCurrentLocation() {
    if(!navigator.geolocation){setMsg(t.locationPermission);return;}
    setLocating(true); setSuggestions([]);
    navigator.geolocation.getCurrentPosition(async(pos)=>{
      const latitude=pos.coords.latitude, longitude=pos.coords.longitude;
      try {
        const {data}=await client.get('/weather/reverse-geocode',{params:{latitude,longitude}});
        setF((cur)=>({...cur,latitude,longitude,location:data.compact_name||data.display_name||`${latitude}, ${longitude}`}));
      } catch { setF((cur)=>({...cur,latitude,longitude,location:`${latitude.toFixed(5)}, ${longitude.toFixed(5)}`})); }
      await loadPreview(latitude,longitude);
      setMsg(t.locationFound); setLocating(false);
    },()=>{setLocating(false);setMsg(t.locationPermission);},{enableHighAccuracy:true,timeout:15000,maximumAge:30000});
  }

  async function findLocation(){
    if(!f.location.trim())return;
    if(suggestions.length){await chooseLocation(suggestions[0]);return;}
    setLocating(true);
    try{const {data}=await client.get('/weather/geocode',{params:{location:f.location}});await chooseLocation(data);setMsg(t.locationFound);}catch{setMsg(t.locationNotFound);}finally{setLocating(false);}
  }

  async function save(e){
    e.preventDefault(); if(!f.crop.trim())return; setSaving(true);
    try{
      const payload={...f,area_acres:Number(f.area_acres),irrigation_type:f.irrigation_type==='Other'?(customIrrigation.trim()||'Other'):f.irrigation_type,irrigation_source:f.irrigation_source==='Other'?(customSource.trim()||'Other'):f.irrigation_source};
      const {data}=await client.post('/farms',payload);await onSaved(data);setF((cur)=>({...cur,name:''}));
    }catch(error){setMsg(error.response?.data?.detail||t.couldNotSave);}finally{setSaving(false);}
  }

  return <section className="farmLayout">
    <form className="panel farmform" onSubmit={save}>
      <div className="panelhead"><div><span className="kicker">{t.exactLocation}</span><h3>{t.farmSetup}</h3><p className="panelIntro">{t.locationEasyHelp}</p></div><Sprout/></div>
      <div className="formgrid">
        <Field label={t.farmName} value={f.name} onChange={(v)=>setF({...f,name:v})} required/>
        <div className="field locationField"><span>{t.location}</span><div className="locationInput"><Search size={16}/><input value={f.location} placeholder={t.locationPlaceholder} autoComplete="off" onChange={(e)=>{setF({...f,location:e.target.value,latitude:null,longitude:null});setPreviewWeather(null);}} required/><button type="button" onClick={findLocation} title={t.findOnMap}>{searching||locating?<RefreshCw className="spin" size={17}/>:<ChevronRight size={17}/>}</button></div>{suggestions.length>0&&<div className="locationSuggestions">{suggestions.map((item,i)=><button type="button" key={`${item.id||item.name}-${i}`} onClick={()=>chooseLocation(item)}><MapPin size={16}/><span><b>{item.name}</b><small>{[item.admin2,item.admin1,item.country].filter(Boolean).join(', ')}</small></span></button>)}</div>}<small>{f.latitude!=null?t.locationSelectedHint:t.locationTypeHint}</small></div>
        <Field label={t.cropName} value={f.crop} placeholder={t.cropPlaceholder} onChange={(v)=>setF({...f,crop:v})} required help={t.cropFreeHelp}/>
        <SelectField label={t.stage} value={f.crop_stage} onChange={(v)=>setF({...f,crop_stage:v})} options={stages.map((v)=>[v,stageLabel(v,t)])} help={t.stageHelp}/>
        <Field label={t.sowingDate} type="date" value={f.sowing_date} onChange={(v)=>setF({...f,sowing_date:v})} icon={<CalendarDays size={15}/>}/>
        <Field label={t.area} type="number" value={f.area_acres} onChange={(v)=>setF({...f,area_acres:v})} required/>
        <SelectField label={t.soil} value={f.soil_type} onChange={(v)=>setF({...f,soil_type:v})} options={SOILS.map((v)=>[v,soilLabel(v,t)])}/>
        <SelectField label={t.irrigation} value={f.irrigation_type} onChange={(v)=>setF({...f,irrigation_type:v})} options={IRRIGATION_TYPES.map((v)=>[v,irrigationLabel(v,t)])}/>
        {f.irrigation_type==='Other'&&<Field label={t.otherIrrigation} value={customIrrigation} onChange={setCustomIrrigation} required/>}
        <SelectField label={t.waterSource} value={f.irrigation_source} onChange={(v)=>setF({...f,irrigation_source:v})} options={IRRIGATION_SOURCES.map((v)=>[v,sourceLabel(v,t)])}/>
        {f.irrigation_source==='Other'&&<Field label={t.otherWaterSource} value={customSource} onChange={setCustomSource} required/>}
      </div>
      <div className="locationActions"><button type="button" className="secondary" onClick={useCurrentLocation} disabled={locating}>{locating?<RefreshCw className="spin" size={16}/>:<Navigation size={16}/>} {locating?t.locating:t.useCurrentLocation}</button>{f.latitude!=null&&f.longitude!=null&&<><span className="coordinates"><MapPin size={14}/>{f.latitude.toFixed(5)}, {f.longitude.toFixed(5)}</span><a className="mapLink" href={`https://www.google.com/maps?q=${f.latitude},${f.longitude}`} target="_blank" rel="noreferrer">{t.openGoogleMaps}<ExternalLink size={13}/></a></>}</div>

      {(previewWeather||previewBusy)&&<WeatherCenter t={t} lang={lang} weather={previewWeather} busy={previewBusy} onRefresh={()=>loadPreview(f.latitude,f.longitude)} compact/>}

      <MapPreview t={t} latitude={f.latitude} longitude={f.longitude} location={f.location} />
      <button className="primary wide" disabled={saving||!f.name.trim()||!f.location.trim()||!f.crop.trim()||f.latitude==null||f.longitude==null}>{saving?<RefreshCw className="spin"/>:<Sprout/>}{saving?t.saving:t.save}</button>
    </form>

    <div className="panel savedPanel"><h3>{t.savedFarms}</h3>{farms.length===0?<Empty t={t}/>:farms.map((farm)=><div className={`farmitem ${Number(activeFarmId)===farm.id?'selected':''}`} key={farm.id} onClick={()=>setActiveFarm(farm.id)}><div className="farmdot"><Sprout size={18}/></div><div className="farmitemText"><div><b>{farm.name}</b>{Number(activeFarmId)===farm.id&&<span className="activePill">{t.active}</span>}</div><p>{farm.crop} • {stageLabel(farm.crop_stage,t)} • {irrigationLabel(farm.irrigation_type,t)}</p><small>{farm.location}{farm.sowing_date?` • ${t.sowingDate}: ${farm.sowing_date}`:''}</small></div><button className="iconDanger" onClick={(e)=>{e.stopPropagation();onDelete(farm.id);}} title={t.deleteFarm}><Trash2 size={16}/></button></div>)}</div>
  </section>;
}

function MapPreview({t,latitude,longitude,location}) {
  const [provider,setProvider]=useState('google');
  if(latitude==null||longitude==null) return <div className="mapCard"><div className="mapTitle"><MapPinned size={17}/><b>{t.mapPreview}</b></div><div className="mapEmpty"><MapPinned/><span>{t.selectLocationFromSuggestions}</span></div></div>;
  const delta=0.018;
  const osm=`https://www.openstreetmap.org/export/embed.html?bbox=${longitude-delta}%2C${latitude-delta}%2C${longitude+delta}%2C${latitude+delta}&layer=mapnik&marker=${latitude}%2C${longitude}`;
  const google=`https://maps.google.com/maps?q=${latitude},${longitude}&z=16&output=embed`;
  return <div className="mapCard mapCardV7">
    <div className="mapTitle"><div><MapPinned size={17}/><span><b>{t.mapPreview}</b><small>{location}</small></span></div><div className="mapTabs"><button type="button" className={provider==='google'?'on':''} onClick={()=>setProvider('google')}>{t.googleMap}</button><button type="button" className={provider==='osm'?'on':''} onClick={()=>setProvider('osm')}>{t.backupMap}</button></div></div>
    <iframe key={`${provider}-${latitude}-${longitude}`} title={t.mapPreview} src={provider==='google'?google:osm} loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen onError={()=>setProvider('osm')}/>
    <div className="mapFooter"><span><MapPin size={14}/>{Number(latitude).toFixed(5)}, {Number(longitude).toFixed(5)}</span><a href={`https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`} target="_blank" rel="noreferrer">{t.openGoogleMaps}<ExternalLink size={13}/></a></div>
  </div>;
}

function PlantAIPage({ t, lang, farm, setMsg, onScan }) {
  const [cropName,setCropName]=useState(farm?.crop||'');
  const [plantPart,setPlantPart]=useState('leaf');
  const [symptoms,setSymptoms]=useState('');
  const [file,setFile]=useState(null);
  const [preview,setPreview]=useState('');
  const [out,setOut]=useState(null);
  const [busy,setBusy]=useState(false);
  const [cameraOpen,setCameraOpen]=useState(false);
  const [farmWeather,setFarmWeather]=useState(null);
  const [progress,setProgress]=useState(null);
  const [scanHistory,setScanHistory]=useState([]);
  const galleryRef=useRef(null);

  useEffect(()=>{ if(farm?.crop) setCropName(farm.crop); setOut(null); setFarmWeather(null); loadProgress(); },[farm?.id]);
  useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview);},[preview]);

  function chooseFile(selected){ if(!selected)return; if(preview)URL.revokeObjectURL(preview); setFile(selected);setPreview(URL.createObjectURL(selected));setOut(null); }

  async function loadProgress(){
    if(!farm?.id){setProgress(null);setScanHistory([]);return;}
    try{
      const [p,h]=await Promise.all([client.get(`/disease/progress/${farm.id}`),client.get(`/disease/history/${farm.id}`,{params:{limit:8}})]);
      setProgress(p.data);setScanHistory(h.data||[]);
    }catch{setProgress(null);setScanHistory([]);}
  }

  async function scan(){
    if(!farm){setMsg(t.createFarmToBegin);return;}
    if(!file||!cropName.trim())return;
    setBusy(true);
    try{
      const fd=new FormData();
      fd.append('farm_id',String(farm.id));fd.append('crop_name',cropName.trim());fd.append('plant_part',plantPart);fd.append('symptoms',symptoms);fd.append('file',file);
      const {data}=await client.post('/disease/analyze',fd,{headers:{'Content-Type':'multipart/form-data'},timeout:60000});
      setOut(data); onScan(data); await loadProgress();
      try{const wx=await client.get(`/weather/farm/${farm.id}`);setFarmWeather(wx.data);}catch{setFarmWeather(null);}
    }catch(error){setMsg(error.response?.data?.detail||t.plantAIUnavailable);}finally{setBusy(false);}
  }

  if(!farm)return <EmptyState t={t} icon={<MapPinned/>} title={t.createFarmToBegin}/>;

  return <>
    <section className="panel scanIntro"><div><span className="kicker">{t.plantAI}</span><h2>{t.scanTitle}</h2><p>{t.scanSubtitle}</p></div><div className="modelBadge"><FlaskConical/><span>{t.plantModelNote}</span></div></section>
    <section className="plantGrid">
      <div className="panel scanForm">
        <div className="formgrid"><Field label={t.scanCrop} value={cropName} onChange={setCropName} required/><SelectField label={t.plantPart} value={plantPart} onChange={setPlantPart} options={PLANT_PARTS.map((v)=>[v,t[`plantPart_${v}`]])}/></div>
        <label className="field"><span>{t.symptomsOptional}</span><textarea value={symptoms} onChange={(e)=>setSymptoms(e.target.value)} placeholder={t.symptomsPlaceholder} rows={3}/></label>
        <div className="uploadbox">
          {preview?<img className="plantPreview" src={preview} alt={t.selectedPhoto}/>:<div className="uploadPlaceholder"><ScanLine size={42}/><h3>{t.addPlantPhoto}</h3><p>{t.maxImage}</p></div>}
          <input ref={galleryRef} className="hiddenFile" type="file" accept="image/jpeg,image/png,image/webp" onChange={(e)=>chooseFile(e.target.files?.[0])}/>
          <div className="photoButtons"><button type="button" className="primary" onClick={()=>setCameraOpen(true)}><Camera size={18}/>{t.camera}</button><button type="button" className="secondary" onClick={()=>galleryRef.current?.click()}><Images size={18}/>{t.gallery}</button>{file&&<button type="button" className="ghost" onClick={()=>{setFile(null);setPreview('');setOut(null);setFarmWeather(null);}}><RotateCcw size={16}/>{t.retake}</button>}</div>
          {file&&<small className="filename">{t.selectedPhoto}: {file.name}</small>}
        </div>
        <button className="primary wide analyzeButton" onClick={scan} disabled={!file||busy||!cropName.trim()}>{busy?<RefreshCw className="spin"/>:<BrainCircuit/>}{busy?t.analyzingPlant:t.analyzePlant}</button>
      </div>

      <div className="panel resultPanel">{!out?<div className="emptyDiagnosis"><ScanLine size={46}/><p>{t.noData}</p></div>:<PlantResult out={out} t={t} lang={lang} weather={farmWeather}/>}</div>
    </section>
    <DiseaseProgressTracker t={t} lang={lang} progress={progress} history={scanHistory}/>
    <CameraModal open={cameraOpen} onClose={()=>setCameraOpen(false)} onCapture={(captured)=>{chooseFile(captured);setCameraOpen(false);}} t={t}/>
  </>;
}

function DiseaseProgressTracker({t,lang,progress,history}) {
  const status=progress?.status;
  const tone=status==='improving'?'good':status==='worsening'?'bad':'stable';
  return <section className="panel progressTracker">
    <div className="panelhead"><div><span className="kicker">{t.diseaseProgress}</span><h3>{t.progressTitle}</h3></div><Activity/></div>
    {!progress||status==='no_scans'?<div className="progressEmpty"><Camera/><span>{t.progressNeedScans}</span></div>:<>
      <div className={`progressHero ${tone}`}><div>{status==='improving'?<TrendingDown/>:status==='worsening'?<TrendingUp/>:<Activity/>}<span>{status==='first_scan'?t.firstScan:status==='improving'?t.improving:status==='worsening'?t.worsening:t.stable}</span></div>{progress.delta!=null&&<b>{progress.delta>0?'+':''}{progress.delta} {t.riskPoints}</b>}</div>
      {progress.latest&&<div className="progressCompare"><div><span>{t.previousScan}</span>{progress.previous?<><b>{Math.round(progress.previous.risk)}/100</b><small>{formatDateTime(progress.previous.created_at,lang)}</small></>:<b>—</b>}</div><ChevronRight/><div><span>{t.latestScan}</span><b>{Math.round(progress.latest.risk)}/100</b><small>{formatDateTime(progress.latest.created_at,lang)}</small></div></div>}
      <p className="progressNote">{t.progressNote}</p>
      {history?.length>1&&<div className="miniScanHistory">{[...history].reverse().slice(-6).map((x)=><div key={x.scan_id}><span>{formatDateTime(x.created_at,lang)}</span><b>{Math.round(x.disease_risk_pct)}</b></div>)}</div>}
    </>}
  </section>;
}

function PlantResult({out,t,lang,weather}) {
  const mainLabel = out.analysis_mode==='broad_visual_triage' ? visualLabel(out.label,t) : out.label;
  const treatment=out.treatment;
  return <div className="plantResult">
    <div className="resultTop"><div><span className="kicker">{t.photoRiskResult}</span><h2>{mainLabel}</h2><p>{t[`mode_${out.analysis_mode}`]||out.analysis_mode}</p></div><div className={`riskCircle ${out.disease_risk_pct>=70?'high':out.disease_risk_pct>=40?'moderate':'low'}`}><b>{Math.round(out.disease_risk_pct)}</b><span>/100</span></div></div>
    <div className="metricGrid"><Metric icon={<CircleGauge/>} label={t.confidence} value={`${Math.round(out.confidence_pct)}%`}/><Metric icon={<Images/>} label={t.imageQuality} value={`${Math.round(out.image_quality_pct)}%`}/><Metric icon={<AlertTriangle/>} label={t.riskFromPhoto} value={`${Math.round(out.disease_risk_pct)}%`}/></div>
    <div className={`useBanner ${out.usable_for_risk?'ok':'warn'}`}>{out.usable_for_risk?<CheckCircle2/>:<AlertTriangle/>}<span>{out.usable_for_risk?t.usableInRisk:t.notUsableInRisk}</span></div>
    {out.broad_visual&&<div className="resultBlock"><span>{t.visualTriage}</span><b>{visualLabel(out.broad_visual.label,t)}</b><small>{Math.round(out.broad_visual.confidence_pct)}% {t.confidence}</small></div>}
    {out.analysis_mode==='leaf_specific_plus_visual'&&out.specific_leaf?.label&&<div className="resultBlock specific"><span>{t.specificLeafResult}</span><b>{out.specific_leaf.label}</b><small>{Math.round(out.specific_leaf.confidence_pct)}% {t.confidence}</small></div>}
    {out.top_predictions?.length>0&&<div className="predictionList"><span className="blockTitle">{t.topPredictions}</span>{out.top_predictions.map((item,i)=><div key={`${item.label}-${i}`}><span>{out.analysis_mode==='broad_visual_triage'?visualLabel(item.label,t):item.label}</span><b>{Math.round(item.confidence_pct)}%</b></div>)}</div>}
    {out.warnings?.length>0&&<div className="warnings">{out.warnings.map((w)=><p key={w}><AlertTriangle size={15}/>{warningLabel(w,t)}</p>)}</div>}
    {treatment&&<TreatmentPlan treatment={treatment} t={t} weather={weather} lang={lang}/>}
  </div>;
}

function treatmentAction(code,t){return t[`treatmentAction_${code}`]||code.replaceAll('_',' ');}
function chemicalCategory(code,t){return t[`chemical_${code}`]||code.replaceAll('_',' ');}
function treatmentDetail(code,t){return t[`detail_${code}`]||code?.replaceAll('_',' ')||'';}
function chemicalReason(code,t){return t[`chemicalReason_${code}`]||treatmentDetail(code,t);}
function sprayAvoid(code,t){return t[`avoid_${code}`]||treatmentDetail(code,t);}

function TreatmentPlan({treatment,t,weather,lang}) {
  const chemical=treatment.chemical||{};
  const spray=weather?.spray_window;
  return <div className="treatmentPlan detailedTreatment">
    <div className="treatmentHead"><div><span className="kicker">{t.smartTreatmentPlan}</span><h3>{t[`treatmentKind_${treatment.kind}`]||treatment.kind}</h3></div><span className={`treatmentRisk ${treatment.risk_level}`}>{t[treatment.risk_level]||treatment.risk_level}</span></div>

    <div className="diagnosisExplain">
      <div className="explainSection"><span>{t.whatProblem}</span><b>{treatmentDetail(treatment.problem_code,t)}</b><p>{t.photoDiagnosisExplain}</p></div>
      <div className="explainSection"><span>{t.visibleSymptoms}</span><ul>{(treatment.symptom_codes||[]).map((code)=><li key={code}>{treatmentDetail(code,t)}</li>)}</ul></div>
      <div className="explainSection"><span>{t.possibleCauses}</span><ul>{(treatment.cause_codes||[]).map((code)=><li key={code}>{treatmentDetail(code,t)}</li>)}</ul></div>
    </div>

    <div className="treatmentActions"><b>{t.recommendedNextSteps}</b>{(treatment.action_codes||[]).map((code)=><div key={code}><CheckCircle2 size={15}/><span>{treatmentAction(code,t)}</span></div>)}</div>

    {(treatment.prevention_codes||[]).length>0&&<div className="preventionBox"><b>{t.prevention}</b>{treatment.prevention_codes.map((code)=><div key={code}><ShieldCheck size={14}/><span>{treatmentDetail(code,t)}</span></div>)}</div>}

    <div className={`chemicalCard ${chemical.recommended?'available':'hold'}`}>
      <div className="chemicalTitle"><Beaker/><div><span>{t.pesticideChemicalOption}</span><b>{chemicalCategory(chemical.category_code,t)}</b></div></div>
      <div className="whyChemical"><b>{t.whyThisChemical}</b><p>{chemicalReason(chemical.reason_code,t)}</p></div>
      <p>{chemical.recommended?t.chemicalCategoryOnly:t.chemicalNotRecommended}</p>
      <div className="avoidSpray"><b>{t.whenNotToSpray}</b>{(treatment.avoid_spray_codes||[]).map((code)=><div key={code}><AlertTriangle size={14}/><span>{sprayAvoid(code,t)}</span></div>)}</div>
      <div className="chemicalSafety"><ShieldAlert size={16}/><span>{t.chemicalSafety}</span></div>
      <a href={treatment.official_reference_url} target="_blank" rel="noreferrer">{t.verifyOfficialRegistration}<ExternalLink size={13}/></a>
    </div>
    {spray&&<div className={`sprayAfterDiagnosis ${spray.status}`}><div><CloudSun/><span>{t.weatherAwareSpray}</span></div><b>{t[`spray_${spray.status}`]||t.sprayUnavailable}</b>{spray.start_time&&<small>{shortTime(spray.start_time,lang)} – {shortTime(spray.end_time,lang)} • {Math.round(spray.score||0)}/100</small>}<p>{t.sprayWindowNote}</p></div>}
  </div>;
}

function Metric({icon,label,value}) { return <div className="metric"><span>{icon}{label}</span><b>{value}</b></div>; }

function CameraModal({open,onClose,onCapture,t}) {
  const videoRef=useRef(null); const streamRef=useRef(null); const [err,setErr]=useState(''); const [starting,setStarting]=useState(false);
  const stop=()=>{streamRef.current?.getTracks()?.forEach((track)=>track.stop());streamRef.current=null;if(videoRef.current)videoRef.current.srcObject=null;};
  async function start(){setErr('');setStarting(true);stop();try{if(!navigator.mediaDevices?.getUserMedia)throw new Error('getUserMedia unsupported');const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}},audio:false});streamRef.current=stream;if(videoRef.current){videoRef.current.srcObject=stream;await videoRef.current.play();}}catch{setErr(t.cameraUnavailable);}finally{setStarting(false);}}
  useEffect(()=>{if(open)start();else stop();return stop;},[open]);
  async function capture(){const video=videoRef.current;if(!video||!video.videoWidth)return;const canvas=document.createElement('canvas');canvas.width=video.videoWidth;canvas.height=video.videoHeight;const ctx=canvas.getContext('2d');ctx.drawImage(video,0,0);canvas.toBlob((blob)=>{if(!blob)return;const file=new File([blob],`agritech-camera-${Date.now()}.jpg`,{type:'image/jpeg'});stop();onCapture(file);},'image/jpeg',0.92);}
  if(!open)return null;
  return <div className="modalBackdrop"><div className="cameraModal"><div className="modalHead"><div><h3>{t.cameraTitle}</h3><p>{t.cameraHint}</p></div><button onClick={()=>{stop();onClose();}}><X/></button></div><div className="videoWrap"><video ref={videoRef} playsInline muted/>{starting&&<div className="cameraLoading"><RefreshCw className="spin"/><span>{t.startCamera}</span></div>}</div>{err&&<div className="error">{err}</div>}<div className="cameraActions"><button className="secondary" onClick={start} disabled={starting}><RotateCcw size={17}/>{t.startCamera}</button><button className="primary" onClick={capture} disabled={starting||!!err}><Camera size={18}/>{t.capture}</button></div></div></div>;
}

function ActionPlanPage({t,lang,farm,setMsg}) {
  const [plan,setPlan]=useState(null);
  const [busy,setBusy]=useState(false);
  async function load(){
    if(!farm?.id){setPlan(null);return;}
    setBusy(true);
    try{const {data}=await client.get(`/assessments/action-plan/${farm.id}`);setPlan(data);}catch(error){setMsg(error.response?.data?.detail||t.requestFailed);}finally{setBusy(false);}
  }
  useEffect(()=>{load();},[farm?.id]);
  async function toggle(task){
    const next=!task.completed;
    try{
      await client.post(`/assessments/action-plan/${farm.id}/toggle`,{task_key:task.task_key,task_date:task.task_date,completed:next});
      setPlan((cur)=>({...cur,tasks:cur.tasks.map((x)=>x.task_key===task.task_key&&x.task_date===task.task_date?{...x,completed:next}:x)}));
    }catch{setMsg(t.requestFailed);}
  }
  if(!farm)return <EmptyState t={t} icon={<MapPinned/>} title={t.createFarmToBegin}/>;
  const groups=(plan?.tasks||[]).reduce((acc,item)=>{(acc[item.task_date]??=[]).push(item);return acc;},{});
  return <section className="actionPlanPage">
    <div className="panel actionPlanHero"><div><span className="kicker">{t.smartActionCalendar}</span><h2>{t.actionPlanFor} {farm.name}</h2><p>{t.actionPlanIntro}</p></div><button className="secondary" onClick={load} disabled={busy}><RefreshCw className={busy?'spin':''} size={16}/>{t.refresh}</button></div>
    {busy&&!plan?<div className="panel loadingCard"><RefreshCw className="spin"/><span>{t.loading}</span></div>:Object.keys(groups).length===0?<div className="panel"><Empty t={t}/></div>:Object.entries(groups).map(([day,tasks])=><section className="panel taskDay" key={day}><div className="taskDayHead"><CalendarCheck2/><div><b>{formatTaskDate(day,lang,t)}</b><span>{tasks.filter(x=>x.completed).length}/{tasks.length} {t.completed}</span></div></div><div className="taskList">{tasks.map((task)=><button className={`taskItem ${task.completed?'done':''}`} key={`${task.task_key}-${task.task_date}`} onClick={()=>toggle(task)}><span className={`taskCheck ${task.completed?'checked':''}`}>{task.completed?<CheckCircle2 size={18}/>:<span/>}</span><div><span className={`priority ${task.priority}`}>{priorityLabel(task.priority==='immediate'?'IMMEDIATE':task.priority==='today'?'TODAY':'ROUTINE',t)}</span><b>{t[`taskTitle_${task.title_code}`]||task.title_code}</b><small>{t[`taskReason_${task.reason_code}`]||task.reason_code}</small></div></button>)}</div></section>) }
  </section>;
}

function formatTaskDate(value,lang,t){
  const d=new Date(`${value}T12:00:00`);const today=new Date();today.setHours(12,0,0,0);const diff=Math.round((d-today)/86400000);
  if(diff===0)return t.todayLabel;if(diff===1)return t.tomorrowLabel;
  try{return new Intl.DateTimeFormat(localeFor(lang),{weekday:'long',day:'numeric',month:'short'}).format(d);}catch{return value;}
}

function HistoryPage({t,lang,data}) {
  const [filter,setFilter]=useState('all');
  const now=Date.now();
  const days=filter==='7'?7:filter==='30'?30:null;
  const filtered=(data||[]).filter((row)=>{if(!days)return true;const d=new Date(String(row.created_at).replace(' ','T')+'Z').getTime();return Number.isFinite(d)&&now-d<=days*86400000;});
  const latest=data?.[data.length-1]; const previous=data?.[data.length-2];
  const delta=(a,b)=>a==null||b==null?null:Math.round((Number(a)-Number(b))*10)/10;
  const changes=latest&&previous?[
    ['overall',delta(latest.overall_risk,previous.overall_risk),'pts'],
    ['temperature',delta(latest.temperature_c,previous.temperature_c),'°C'],
    ['soilMoistureChange',delta(latest.soil_moisture_pct,previous.soil_moisture_pct),'%'],
    ['rainChange',delta(latest.rainfall_next_24h_mm,previous.rainfall_next_24h_mm),' mm'],
    ['plantRiskChange',delta(latest.disease,previous.disease),' pts'],
  ].filter(([,v])=>v!=null):[];
  return <>
    <section className="panel historyHead"><div><span className="kicker">{t.riskTrend}</span><h3>{t.assessmentHistory}</h3></div><div className="historyFilters">{[['all',t.all],['7',t.last7Days],['30',t.last30Days]].map(([id,label])=><button className={filter===id?'on':''} onClick={()=>setFilter(id)} key={id}>{label}</button>)}</div></section>
    {latest&&previous&&<section className="panel whatChanged"><div className="panelhead"><div><span className="kicker">{t.whatChanged}</span><h3>{delta(latest.overall_risk,previous.overall_risk)>0?t.riskIncreased:delta(latest.overall_risk,previous.overall_risk)<0?t.riskDecreased:t.riskStable}</h3><p>{t.whatChangedIntro}</p></div>{delta(latest.overall_risk,previous.overall_risk)>0?<TrendingUp/>:<TrendingDown/>}</div><div className="changeGrid">{changes.map(([key,value,unit])=><div className={value>0?'up':value<0?'down':''} key={key}><span>{t[key]}</span><b>{value>0?'+':''}{value}{unit}</b></div>)}</div><small>{t.changeExplanationHint}</small></section>}
    <section className="panel"><h3>{t.riskTrend}</h3>{filtered.length===0?<Empty t={t}/>:<><div className="chart"><ResponsiveContainer width="100%" height={320}><LineChart data={filtered}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="created_at" tickFormatter={(v)=>formatDateTime(v,lang).split(',')[0]}/><YAxis domain={[0,100]}/><Tooltip labelFormatter={(v)=>formatDateTime(v,lang)}/><Line type="monotone" dataKey="overall_risk" name={t.overall} stroke="#20884d" strokeWidth={3}/><Line type="monotone" dataKey="water" name={t.water} stroke="#3b82f6" strokeWidth={2}/><Line type="monotone" dataKey="disease" name={t.diseaseRisk} stroke="#ef8354" strokeWidth={2}/></LineChart></ResponsiveContainer></div><div className="table historyTable"><div className="tr th"><span>{t.dateTime}</span><span>{t.farm}</span><span>{t.risk}</span><span>{t.confidence}</span><span>{t.source}</span></div>{[...filtered].reverse().map((row)=><div className="tr" key={row.id}><span>{formatDateTime(row.created_at,lang)}</span><span>{row.farm_name||'—'}<small>{row.crop||''}</small></span><span>{row.overall_risk} • {statusLabel(row.status,t)}</span><span>{row.confidence}%</span><span>{row.source==='live-weather'?t.sourceLive:t.sourceManual}</span></div>)}</div></>}</section>
  </>;
}

function AboutPage({t}) { return <section className="panel about"><div className="abouticon"><BrainCircuit/></div><h2>{t.aboutTitle}</h2><p>{t.aboutText}</p><div className="aboutgrid"><div><BrainCircuit/><b>{t.hybridAi}</b><span>{t.hybridAiText}</span></div><div><CircleGauge/><b>{t.explainable}</b><span>{t.explainableText}</span></div><div><CloudSun/><b>{t.weatherIntelligence}</b><span>{t.weatherIntelligenceText}</span></div><div><Beaker/><b>{t.treatmentIntelligence}</b><span>{t.treatmentIntelligenceText}</span></div><div><SlidersHorizontal/><b>{t.whatIfFeature}</b><span>{t.whatIfFeatureText}</span></div><div><Sprout/><b>{t.farmerFirst}</b><span>{t.farmerFirstText}</span></div><div><FlaskConical/><b>{t.research}</b><span>{t.researchText}</span></div></div><div className="modelNote"><Info/><p>{t.plantModelNote}</p></div><p className="disclaimer">{t.disclaimer}</p></section>; }

function displayScanLabel(label,t){return label?.includes(' — ')?label:visualLabel(label,t);}
function Empty({t}) { return <div className="empty"><Leaf/><span>{t.noData}</span></div>; }
function EmptyState({t,icon,title,button,onClick}) { return <div className="panel emptyState"><div>{icon}</div><h2>{title}</h2>{button&&<button className="primary" onClick={onClick}>{button}</button>}</div>; }
function Field({label,value,onChange,type='text',placeholder='',inputMode,maxLength,icon,help,required=false}) { return <label className="field"><span>{label}</span><div className={icon?'inputWithIcon':''}>{icon}<input type={type} value={value} placeholder={placeholder} inputMode={inputMode} maxLength={maxLength} required={required} onChange={(e)=>onChange(e.target.value)} step={type==='number'?'any':undefined}/></div>{help&&<small>{help}</small>}</label>; }
function SelectField({label,value,onChange,options,help}) { return <label className="field"><span>{label}</span><select value={value} onChange={(e)=>onChange(e.target.value)}>{options.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>{help&&<small>{help}</small>}</label>; }
