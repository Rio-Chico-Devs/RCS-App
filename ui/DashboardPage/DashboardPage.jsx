import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css';

/* ═══════════════════════════════════════════
   CHART COMPONENTS
═══════════════════════════════════════════ */

/* SVG line chart — usato per 90d e 1y */
const LineChart = ({ values, labels }) => {
  const max   = Math.max(...values);
  const min   = Math.min(...values);
  const range = max - min || 1;

  const PL = 50, PR = 8, PT = 8, PB = 22;
  const W  = 500, H = 120;
  const CW = W - PL - PR, CH = H - PT - PB;

  const toX = (i) => PL + (i / (values.length - 1)) * CW;
  const toY = (v) => PT + CH - ((v - min) / range) * CH;

  const line = values.map((v, i) => `${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');
  const area = [
    `M ${toX(0).toFixed(1)},${(PT + CH).toFixed(1)}`,
    values.map((v, i) => `L ${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' '),
    `L ${toX(values.length - 1).toFixed(1)},${(PT + CH).toFixed(1)} Z`,
  ].join(' ');

  const yTicks = [0, 0.33, 0.67, 1].map(t => ({
    y:   PT + (1 - t) * CH,
    lbl: `€${((min + t * range) / 1000).toFixed(0)}k`,
  }));

  const step = Math.ceil(labels.length / 7);

  return (
    <div className="chart-svg-wrap">
      <svg className="chart-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#0ff" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#0ff" stopOpacity="0"    />
          </linearGradient>
        </defs>
        {/* Griglia + etichette Y */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={PL} y1={t.y} x2={W - PR} y2={t.y}
              stroke="rgba(0,255,255,0.08)" strokeWidth="0.8" />
            <text x={PL - 4} y={t.y + 3} fontSize="9"
              fill="rgba(0,255,255,0.45)" textAnchor="end" fontFamily="Share Tech Mono, monospace">
              {t.lbl}
            </text>
          </g>
        ))}
        {/* Area */}
        <path d={area} fill="url(#areaGrad)" />
        {/* Linea */}
        <polyline points={line} fill="none" stroke="#0ff"
          strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        {/* Punti dati */}
        {values.map((v, i) => (
          <circle key={i} cx={toX(i)} cy={toY(v)} r="2.8"
            fill="#0ff" opacity="0.9" />
        ))}
        {/* Etichette X */}
        {labels.map((lbl, i) => {
          if (i % step !== 0 && i !== labels.length - 1) return null;
          return (
            <text key={i} x={toX(i)} y={H - 4} fontSize="8"
              fill="rgba(0,255,255,0.5)" textAnchor="middle"
              fontFamily="Share Tech Mono, monospace">
              {lbl}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

/* Bar chart — usato per 7d e 30d con valori reali */
const BarChart = ({ values, labels, period }) => {
  const max = Math.max(...values);
  return (
    <div className={`chart-bar-area${period === '30d' ? ' chart-dense' : ''}`}>
      {values.map((v, i) => (
        <div className="chart-col" key={i}>
          <div
            className="chart-bar"
            style={{ '--bar-h': `${(v / max) * 100}%` }}
            title={`€ ${v.toLocaleString('it-IT')}`}
          />
          <span className="chart-lbl">{labels[i]}</span>
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════
   ECG WAVEFORM
═══════════════════════════════════════════ */
const ECG_METRICS = [
  { id: 'fatturato',   label: 'Fatturato',    color: 'var(--color-primary,#0ff)', speed: '9s',
    values: [40,45,43,50,55,52,60,63,58,68,72,70,75,80,78,85,82,88,85,90,88,95,92,97] },
  { id: 'utenti',      label: 'Nuovi Utenti', color: 'rgba(0,200,255,0.95)',       speed: '7s',
    values: [30,35,32,40,38,45,50,48,55,52,60,58,65,62,68,65,72,70,75,72,80,78,83,80] },
  { id: 'conversioni', label: 'Conversioni',  color: 'rgba(0,255,150,0.95)',       speed: '11s',
    values: [55,58,53,60,62,58,65,68,63,70,72,68,75,78,73,80,77,82,80,85,82,87,84,88] },
  { id: 'ordine',      label: 'Ordine Medio', color: 'rgba(255,210,0,0.95)',       speed: '8s',
    values: [35,40,38,45,48,44,52,55,50,58,62,58,65,68,63,72,70,75,72,78,75,82,78,85] },
];

const genPoints = (values) => {
  const doubled = [...values, ...values];
  const n = doubled.length - 1;
  return doubled.map((v, i) =>
    `${((i / n) * 800).toFixed(1)},${(55 - (v / 100) * 48).toFixed(1)}`
  ).join(' ');
};

/* ═══════════════════════════════════════════
   DATE LABELS
═══════════════════════════════════════════ */
const getEcgDates = (period) => {
  const today = new Date(2026, 2, 30);
  const days  = { '7d': 7, '30d': 30, '90d': 90, '1y': 365 }[period];
  return [0, 1, 2, 3, 4].map(i => {
    const d = new Date(today);
    d.setDate(today.getDate() - Math.round(days - (days * i) / 4));
    return period === '1y'
      ? d.toLocaleDateString('it-IT', { month: 'short', year: '2-digit' })
      : `${d.getDate()}/${d.getMonth() + 1}`;
  });
};

/* ═══════════════════════════════════════════
   SETTORI
═══════════════════════════════════════════ */
const SECTORS = [
  { name: 'AI / ML Tools',   pct: 45 },
  { name: 'E-Commerce',      pct: 34 },
  { name: 'SaaS Platform',   pct: 28 },
  { name: 'Healthcare Tech', pct: 22 },
  { name: 'Fintech',         pct: 19 },
];

/* ═══════════════════════════════════════════
   DATI PER PERIODO  (valori reali in €)
═══════════════════════════════════════════ */
const DATA = {
  '7d': {
    chartType: 'bar',
    chartValues: [580, 720, 490, 850, 680, 920, 980],
    chartLabels: ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'],
    chartNote:   'valori giornalieri · €',
    total:       '€ 5.220',
    kpi: { fatturato: '€ 4.820', utenti: '1.247', conversioni: '6,4%', ordine: '€ 127' },
    trend: { fatturato: '+12%', utenti: '+8%', conversioni: '-1,2%', ordine: '+5%' },
    up:    { fatturato: true,    utenti: true,  conversioni: false,    ordine: true  },
    transactions: [
      { id: '#2041', client: 'Agenzia Neon', service: 'Web Dev',    amount: '€ 980',   status: 'pagato'   },
      { id: '#2040', client: 'Studio M',     service: 'Multimedia', amount: '€ 450',   status: 'pagato'   },
      { id: '#2039', client: 'TechFlow Srl', service: 'Consulenza', amount: '€ 320',   status: 'in corso' },
      { id: '#2038', client: 'Nova Brand',   service: 'Presenza',   amount: '€ 670',   status: 'pagato'   },
      { id: '#2037', client: 'Pixel & Co',   service: 'Web Dev',    amount: '€ 1.200', status: 'attesa'   },
    ],
  },
  '30d': {
    chartType: 'bar',
    chartValues: [480,520,410,580,620,660,440,620,680,740,700,760,680,800,840,780,860,820,880,850,910,870,820,890,840,920,880,910,950,920],
    chartLabels: ['1','','','','5','','','','','10','','','','','15','','','','','20','','','','','25','','','','','30'],
    chartNote:   'Marzo 2026 · dati giornalieri · €',
    total:       '€ 22.100',
    kpi: { fatturato: '€ 18.340', utenti: '5.890', conversioni: '7,1%', ordine: '€ 143' },
    trend: { fatturato: '+22%', utenti: '+15%', conversioni: '+0,9%', ordine: '+11%' },
    up:    { fatturato: true,    utenti: true,  conversioni: true,      ordine: true  },
    transactions: [
      { id: '#2041', client: 'Agenzia Neon', service: 'Web Dev',    amount: '€ 980',   status: 'pagato'   },
      { id: '#2040', client: 'Studio M',     service: 'Multimedia', amount: '€ 450',   status: 'pagato'   },
      { id: '#2039', client: 'TechFlow Srl', service: 'Consulenza', amount: '€ 320',   status: 'in corso' },
      { id: '#2038', client: 'Nova Brand',   service: 'Presenza',   amount: '€ 670',   status: 'pagato'   },
      { id: '#2036', client: 'MediaX',       service: 'Multimedia', amount: '€ 890',   status: 'pagato'   },
      { id: '#2035', client: 'StartupZone',  service: 'Web Dev',    amount: '€ 2.100', status: 'pagato'   },
    ],
  },
  '90d': {
    chartType: 'line',
    chartValues: [8200, 9400, 10100, 11200, 10600, 12400, 11800, 13600, 13100, 14800, 14200, 16000, 17200],
    chartLabels: ['3/1','10/1','17/1','24/1','31/1','7/2','14/2','21/2','28/2','7/3','14/3','21/3','28/3'],
    chartNote:   'Gen – Mar 2026 · dati settimanali · €',
    total:       '€ 152.800',
    kpi: { fatturato: '€ 52.160', utenti: '16.420', conversioni: '8,3%', ordine: '€ 158' },
    trend: { fatturato: '+31%', utenti: '+24%', conversioni: '+2,1%', ordine: '+18%' },
    up:    { fatturato: true,    utenti: true,  conversioni: true,      ordine: true  },
    transactions: [
      { id: '#2041', client: 'Agenzia Neon', service: 'Web Dev',    amount: '€ 980',   status: 'pagato' },
      { id: '#2038', client: 'Nova Brand',   service: 'Presenza',   amount: '€ 670',   status: 'pagato' },
      { id: '#2035', client: 'StartupZone',  service: 'Web Dev',    amount: '€ 2.100', status: 'pagato' },
      { id: '#2032', client: 'Industria 4',  service: 'Consulenza', amount: '€ 1.500', status: 'pagato' },
      { id: '#2028', client: 'GreenTech',    service: 'Web Dev',    amount: '€ 3.400', status: 'pagato' },
      { id: '#2021', client: 'FashionLab',   service: 'Multimedia', amount: '€ 720',   status: 'pagato' },
    ],
  },
  '1y': {
    chartType: 'line',
    chartValues: [12400, 14200, 15800, 15100, 16800, 17600, 16900, 18800, 19200, 20800, 21600, 23000],
    chartLabels: ["Apr'25", 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic', "Gen'26", 'Feb', 'Mar'],
    chartNote:   'Apr 2025 – Mar 2026 · dati mensili · €',
    total:       '€ 192.200',
    kpi: { fatturato: '€ 198.400', utenti: '62.300', conversioni: '9,1%', ordine: '€ 172' },
    trend: { fatturato: '+44%', utenti: '+38%', conversioni: '+3,4%', ordine: '+26%' },
    up:    { fatturato: true,    utenti: true,  conversioni: true,      ordine: true  },
    transactions: [
      { id: '#2041', client: 'Agenzia Neon', service: 'Web Dev',    amount: '€ 980',   status: 'pagato' },
      { id: '#2035', client: 'StartupZone',  service: 'Web Dev',    amount: '€ 2.100', status: 'pagato' },
      { id: '#2028', client: 'GreenTech',    service: 'Web Dev',    amount: '€ 3.400', status: 'pagato' },
      { id: '#2020', client: 'MegaCorp',     service: 'Consulenza', amount: '€ 5.200', status: 'pagato' },
      { id: '#2015', client: 'Innovatech',   service: 'Web Dev',    amount: '€ 4.800', status: 'pagato' },
      { id: '#2008', client: 'GlobalBrand',  service: 'Multimedia', amount: '€ 1.900', status: 'pagato' },
    ],
  },
};

const PERIODS      = ['7d', '30d', '90d', '1y'];
const PERIOD_LABEL = { '7d': '7 Giorni', '30d': '30 Giorni', '90d': '90 Giorni', '1y': 'Annuale' };

const statusClass = (s) => {
  if (s === 'pagato')   return 'status-paid';
  if (s === 'in corso') return 'status-progress';
  return 'status-pending';
};

/* ═══════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════ */
const DashboardPage = () => {
  const navigate = useNavigate();
  const [period,     setPeriod]     = useState('30d');
  const [fading,     setFading]     = useState(false);
  const [ecgPlaying, setEcgPlaying] = useState(
    Object.fromEntries(ECG_METRICS.map(m => [m.id, true]))
  );

  const switchPeriod = (p) => {
    if (p === period) return;
    setFading(true);
    setTimeout(() => { setPeriod(p); setFading(false); }, 220);
  };

  const toggleEcg = (id) =>
    setEcgPlaying(prev => ({ ...prev, [id]: !prev[id] }));

  useEffect(() => {
    document.body.classList.add('dashboard-page-body');
    return () => document.body.classList.remove('dashboard-page-body');
  }, []);

  const d         = DATA[period];
  const ecgDates  = getEcgDates(period);

  return (
    <div className="dash-wrapper">
      <div className="dash-grid-overlay" />
      <div className="dash-layout">

        {/* ── Header ── */}
        <header className="dash-header">
          <button className="dash-back-btn" onClick={() => navigate('/portfolio/componenti')}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M19 12H5M5 12l7-7M5 12l7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Showcase</span>
          </button>
          <div className="dash-title-group">
            <h1 className="dash-title">Analytics Dashboard</h1>
            <p className="dash-subtitle">{d.chartNote}</p>
          </div>
          <div className="dash-header-right">
            <span className="dash-total-label">Totale periodo</span>
            <span className="dash-total-value">{d.total}</span>
            <div className="dash-live-badge">
              <span className="live-dot" />LIVE
            </div>
          </div>
        </header>

        {/* ── Selettore periodo mobile ── */}
        <div className="period-bar-mobile">
          {PERIODS.map(p => (
            <button
              key={p}
              className={`period-btn${period === p ? ' active' : ''}`}
              onClick={() => switchPeriod(p)}
            >
              {PERIOD_LABEL[p]}
            </button>
          ))}
        </div>

        {/* ── KPI cards — visibili solo su mobile ── */}
        <div className={`kpi-mobile-grid dash-fade${fading ? ' out' : ''}`}>
          {ECG_METRICS.map(m => (
            <div className="kpi-mobile-card" key={m.id}>
              <span className="kpi-mobile-label">{m.label}</span>
              <span className="kpi-mobile-value" style={{ color: m.color }}>{d.kpi[m.id]}</span>
              <span className={`kpi-mobile-trend ${d.up[m.id] ? 'up' : 'down'}`}>
                {d.up[m.id] ? '▲' : '▼'} {d.trend[m.id]}
              </span>
            </div>
          ))}
        </div>

        {/* ── Griglia desktop: 3 colonne ── */}
        <div className={`dash-main-grid dash-fade${fading ? ' out' : ''}`}>

          {/* ZONA 1 — Transazioni */}
          <div className="dash-zone">
            <div className="zone-hd">
              <h2 className="zone-title">Transazioni Recenti</h2>
            </div>
            <div className="zone-scroll">
              <table className="txn-table">
                <thead>
                  <tr>
                    <th>ID</th><th>Cliente</th><th>Servizio</th><th>Importo</th><th>Stato</th>
                  </tr>
                </thead>
                <tbody>
                  {d.transactions.map((t, i) => (
                    <tr key={i}>
                      <td className="td-id">{t.id}</td>
                      <td>{t.client}</td>
                      <td className="td-svc">{t.service}</td>
                      <td className="td-amt">{t.amount}</td>
                      <td><span className={`dash-status ${statusClass(t.status)}`}>{t.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Colonna centrale: ZONA 2 + ZONA 4 */}
          <div className="dash-center-col">

            {/* ZONA 2 — Grafico */}
            <div className="dash-zone dash-zone-chart">
              <div className="zone-hd">
                <h2 className="zone-title">Andamento Fatturato</h2>
                <span className="zone-unit">{d.chartNote}</span>
              </div>
              {d.chartType === 'line'
                ? <LineChart values={d.chartValues} labels={d.chartLabels} />
                : <BarChart  values={d.chartValues} labels={d.chartLabels} period={period} />
              }
            </div>

            {/* ZONA 4 — Settori */}
            <div className="dash-zone dash-zone-sectors">
              <div className="zone-hd">
                <h2 className="zone-title">Crescita Settori 2025</h2>
                <span className="zone-unit">dati simulati</span>
              </div>
              <div className="sectors-list">
                {SECTORS.map((s, i) => (
                  <div className="sector-row" key={i}>
                    <span className="sector-name">{s.name}</span>
                    <div className="sector-track">
                      <div className="sector-bar" style={{ '--s-pct': `${s.pct}%` }} />
                    </div>
                    <span className="sector-pct">+{s.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Colonna destra: ZONA 3 + ZONA 5 */}
          <div className="dash-right-col">

            {/* ZONA 3 — ECG */}
            <div className="dash-zone dash-zone-ecg">
              <div className="zone-hd">
                <h2 className="zone-title">Metriche Attive</h2>
                <span className="zone-unit">{d.chartNote.split('·')[0].trim()}</span>
              </div>
              <div className="ecg-list">
                {ECG_METRICS.map((m) => {
                  const pts     = genPoints(m.values);
                  const playing = ecgPlaying[m.id];
                  return (
                    <div className="ecg-metric" key={m.id}>
                      <div className="ecg-top">
                        <span className="ecg-label">{m.label}</span>
                        <span className="ecg-value" style={{ color: m.color }}>{d.kpi[m.id]}</span>
                        <span className={`ecg-trend ${d.up[m.id] ? 'up' : 'down'}`}>
                          {d.up[m.id] ? '▲' : '▼'} {d.trend[m.id]}
                        </span>
                        <button
                          className={`ecg-btn${playing ? ' pause' : ' play'}`}
                          onClick={() => toggleEcg(m.id)}
                          aria-label={playing ? 'Pausa' : 'Avvia'}
                        >
                          {playing
                            ? <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="3" width="4" height="18"/><rect x="15" y="3" width="4" height="18"/></svg>
                            : <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
                          }
                        </button>
                      </div>
                      <div className="ecg-canvas">
                        <svg className="ecg-svg" viewBox="0 0 800 60"
                          preserveAspectRatio="none"
                          style={{ animationDuration: m.speed, animationPlayState: playing ? 'running' : 'paused' }}
                        >
                          <polyline className="ecg-line" points={pts} style={{ stroke: m.color }} />
                        </svg>
                      </div>
                      <div className="ecg-axis-wrap">
                        <div className="ecg-axis"
                          style={{ animationDuration: m.speed, animationPlayState: playing ? 'running' : 'paused' }}
                        >
                          {[0, 1].map(rep => (
                            <div key={rep} className="ecg-axis-half">
                              {ecgDates.map((label, i) => (
                                <span key={i} className="ecg-date">{label}</span>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ZONA 5 — Periodo */}
            <div className="dash-zone dash-zone-period">
              <div className="zone-hd">
                <h2 className="zone-title">Periodo</h2>
              </div>
              <div className="period-grid">
                {PERIODS.map(p => (
                  <button
                    key={p}
                    className={`period-btn${period === p ? ' active' : ''}`}
                    onClick={() => switchPeriod(p)}
                  >
                    {PERIOD_LABEL[p]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;