/**
 * charts.js : Petits graphiques en barres (HTML/CSS) pour les ordres de grandeur.
 * Une seule série par graphique (pas de légende), valeur au bout de chaque barre,
 * infobulle au survol ou au focus, et un tableau des valeurs pour l'accessibilité.
 */
import { L, t } from '../i18n.js';

const COLON = L(' : ', ': ');

const CHARTS = {
  latency: {
    title: L('Temps d\'accès aux données', 'How long it takes to reach the data'),
    sub: L('Échelle logarithmique : chaque graduation est 1 000 fois plus longue que la précédente.', 'Logarithmic scale: each tick mark is 1,000 times longer than the one before.'),
    scale: 'log',
    min: 0.5,
    max: 2e7,
    ticks: [[1, '1 ns'], [1e3, '1 µs'], [1e6, '1 ms']],
    grid: [1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7],
    rows: [
      { name: L('Cache L1 (CPU)', 'L1 cache (CPU)'), v: 1, label: '~1 ns' },
      { name: L('Cache L3 (CPU)', 'L3 cache (CPU)'), v: 10, label: '~10 ns' },
      { name: L('RAM DDR5', 'DDR5 RAM'), v: 80, label: '~80 ns', emph: true },
      { name: L('SSD NVMe', 'NVMe SSD'), v: 8e4, label: '~80 µs', emph: true },
      { name: L('Disque dur', 'Hard drive'), v: 8e6, label: '~8 ms' },
    ],
    unit: L('temps d\'accès typique', 'typical access time'),
  },
  storage: {
    title: L('Débit en lecture séquentielle', 'Sequential read speed'),
    sub: L('Gros fichiers, dans les meilleures conditions (en Go/s).', 'Large files, under ideal conditions (in GB/s).'),
    scale: 'linear',
    min: 0,
    max: 15,
    ticks: [[0, '0'], [5, L('5 Go/s', '5 GB/s')], [10, L('10 Go/s', '10 GB/s')], [15, L('15 Go/s', '15 GB/s')]],
    grid: [0, 5, 10, 15],
    rows: [
      { name: L('Disque dur', 'Hard drive'), v: 0.2, label: L('~200 Mo/s', '~200 MB/s') },
      { name: L('SSD SATA', 'SATA SSD'), v: 0.55, label: L('~550 Mo/s', '~550 MB/s') },
      { name: 'NVMe PCIe 3.0', v: 3.5, label: L('~3 500 Mo/s', '~3,500 MB/s') },
      { name: 'NVMe PCIe 4.0', v: 7, label: L('~7 000 Mo/s', '~7,000 MB/s'), emph: true },
      { name: 'NVMe PCIe 5.0', v: 14, label: L('~14 000 Mo/s', '~14,000 MB/s') },
    ],
    unit: L('débit maximal', 'peak speed'),
  },
};

function pct(conf, v) {
  if (conf.scale === 'log') {
    const a = Math.log10(conf.min);
    const b = Math.log10(conf.max);
    return ((Math.log10(Math.max(v, conf.min)) - a) / (b - a)) * 100;
  }
  return ((v - conf.min) / (conf.max - conf.min)) * 100;
}

export function initCharts() {
  const tip = document.createElement('div');
  tip.className = 'chart-tip';
  tip.hidden = true;
  document.body.append(tip);

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      e.target.querySelectorAll('.chart-bar').forEach((b) => { b.style.width = `${b.dataset.w}%`; });
      io.unobserve(e.target);
    }
  }, { threshold: 0.3 });

  document.querySelectorAll('.chart[data-chart]').forEach((el) => {
    const conf = CHARTS[el.dataset.chart];
    if (!conf) return;
    const title = document.createElement('p');
    title.className = 'chart-title';
    title.textContent = conf.title;
    const sub = document.createElement('p');
    sub.className = 'chart-sub';
    sub.textContent = conf.sub;
    const rows = document.createElement('div');
    rows.className = 'chart-rows';
    const grid = document.createElement('div');
    grid.className = 'chart-grid';
    grid.setAttribute('aria-hidden', 'true');
    for (const g of conf.grid) {
      const s = document.createElement('span');
      s.style.left = `${pct(conf, g)}%`;
      grid.append(s);
    }
    rows.append(grid);
    for (const r of conf.rows) {
      const row = document.createElement('div');
      row.className = 'chart-row';
      const name = document.createElement('span');
      name.className = 'chart-name';
      name.textContent = r.name;
      const track = document.createElement('div');
      track.className = 'chart-track';
      track.tabIndex = 0;
      track.setAttribute('role', 'img');
      track.setAttribute('aria-label', `${r.name}${COLON}${r.label}`);
      const bar = document.createElement('span');
      bar.className = `chart-bar${r.emph ? ' is-emph' : ''}`;
      const w = Math.max(1.5, pct(conf, r.v));
      bar.dataset.w = w.toFixed(2);
      const val = document.createElement('span');
      val.className = 'chart-value';
      val.textContent = r.label;
      val.style.left = `${w}%`;
      if (w > 76) {
        val.style.left = 'auto';
        val.style.right = `${100 - w}%`;
        val.style.paddingRight = '8px';
        val.style.color = 'var(--accent-ink)';
        val.style.fontWeight = '700';
      }
      track.append(bar, val);
      const showTip = (x, y) => {
        tip.textContent = `${r.name}${COLON}${r.label} (${conf.unit})`;
        tip.hidden = false;
        tip.style.left = `${Math.min(window.innerWidth - tip.offsetWidth - 10, x + 14)}px`;
        tip.style.top = `${y - 36}px`;
      };
      track.addEventListener('mousemove', (e) => showTip(e.clientX, e.clientY));
      track.addEventListener('mouseleave', () => { tip.hidden = true; });
      track.addEventListener('focus', () => { const b = track.getBoundingClientRect(); showTip(b.left + b.width * w / 100, b.top); });
      track.addEventListener('blur', () => { tip.hidden = true; });
      row.append(name, track);
      rows.append(row);
    }
    // graduations
    const axis = document.createElement('div');
    axis.className = 'chart-axis';
    axis.setAttribute('aria-hidden', 'true');
    const spacer = document.createElement('span');
    const ticks = document.createElement('div');
    ticks.className = 'chart-axis-ticks';
    for (const [v, lab] of conf.ticks) {
      const s = document.createElement('span');
      s.style.left = `${pct(conf, v)}%`;
      s.textContent = lab;
      ticks.append(s);
    }
    axis.append(spacer, ticks);
    // tableau des valeurs (accessibilité)
    const det = document.createElement('details');
    det.className = 'chart-table';
    const summary = document.createElement('summary');
    summary.textContent = t('seeTable');
    det.append(summary);
    const table = document.createElement('table');
    for (const r of conf.rows) {
      const tr = document.createElement('tr');
      const th = document.createElement('th');
      th.scope = 'row';
      th.textContent = r.name;
      const td = document.createElement('td');
      td.textContent = r.label;
      tr.append(th, td);
      table.append(tr);
    }
    det.append(table);
    el.append(title, sub, rows, axis, det);
    io.observe(el);
  });
}
