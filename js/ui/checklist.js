/**
 * checklist.js : Checklist de compatibilité (cases à cocher) + calculateur d'alimentation.
 * La progression est gardée dans le navigateur (localStorage) quand c'est possible.
 */
const KEY = 'pc-builder:checklist';

function load() {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch { return {}; }
}
function save(state) {
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* stockage indisponible : on continue sans */ }
}

export function initChecklist() {
  const root = document.getElementById('checklist');
  if (!root) return;
  const boxes = [...root.querySelectorAll('input[type="checkbox"][data-cl]')];
  const bar = document.getElementById('cl-bar');
  const count = document.getElementById('cl-count');
  const done = document.getElementById('cl-done');
  const reset = document.getElementById('cl-reset');
  const state = load();

  boxes.forEach((b) => { b.checked = !!state[b.dataset.cl]; });
  function update() {
    const n = boxes.filter((b) => b.checked).length;
    count.textContent = String(n);
    bar.style.width = `${(n / boxes.length) * 100}%`;
    done.hidden = n !== boxes.length;
    boxes.forEach((b) => { state[b.dataset.cl] = b.checked; });
    save(state);
  }
  boxes.forEach((b) => b.addEventListener('change', update));
  reset.addEventListener('click', () => { boxes.forEach((b) => { b.checked = false; }); update(); });
  update();

  // calculateur : (CPU + GPU + 100 W) × 1,5, arrondi aux 50 W supérieurs
  const cpu = document.getElementById('calc-cpu');
  const gpu = document.getElementById('calc-gpu');
  const cpuOut = document.getElementById('calc-cpu-out');
  const gpuOut = document.getElementById('calc-gpu-out');
  const load_ = document.getElementById('calc-load');
  const psu = document.getElementById('calc-psu');
  if (!cpu || !gpu) return;
  function calc() {
    const c = Number(cpu.value);
    const g = Number(gpu.value);
    const total = c + g + 100;
    const rec = Math.ceil((total * 1.5) / 50) * 50;
    cpuOut.textContent = `${c} W`;
    gpuOut.textContent = `${g} W`;
    load_.textContent = `${total} W`;
    psu.textContent = `${rec} W`;
    for (const r of [cpu, gpu]) {
      const pct = ((r.value - r.min) / (r.max - r.min)) * 100;
      r.style.setProperty('--fill', `${pct}%`);
    }
  }
  cpu.addEventListener('input', calc);
  gpu.addEventListener('input', calc);
  calc();
}
