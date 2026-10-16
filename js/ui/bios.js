/**
 * bios.js — Faux écran UEFI interactif (onglets, profil EXPO/XMP, ordre de démarrage,
 * enregistrement avec F10). Purement pédagogique : rien n'est réellement modifié.
 */
export function initBios() {
  const root = document.getElementById('bios-screen');
  if (!root) return;
  const tabs = [...root.querySelectorAll('[role="tab"]')];
  const panels = [...root.querySelectorAll('[role="tabpanel"]')];
  const clock = document.getElementById('bios-clock');
  const expo = document.getElementById('bios-expo');
  const expoHelp = document.getElementById('bios-expo-help');
  const bootList = document.getElementById('bios-boot');
  const bootHelp = document.getElementById('bios-boot-help');
  const dialog = document.getElementById('bios-dialog');
  const dialogList = document.getElementById('bios-dialog-list');
  const reboot = document.getElementById('bios-reboot');
  const temp = document.getElementById('bios-temp');
  const fan = document.getElementById('bios-fan');
  const saved = { expo: false, first: 'ssd' };

  // ---------------------------------------------------------------- onglets
  function select(i, focus = false) {
    tabs.forEach((t, j) => {
      const on = i === j;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      panels[j].hidden = !on;
    });
    if (focus) tabs[i].focus();
  }
  tabs.forEach((t, i) => t.addEventListener('click', () => select(i)));
  root.addEventListener('keydown', (e) => {
    const i = tabs.findIndex((t) => t.getAttribute('aria-selected') === 'true');
    if (e.key === 'ArrowRight' && !dialog.contains(e.target)) { e.preventDefault(); select((i + 1) % tabs.length, true); }
    if (e.key === 'ArrowLeft' && !dialog.contains(e.target)) { e.preventDefault(); select((i - 1 + tabs.length) % tabs.length, true); }
    if (e.key === 'F10') { e.preventDefault(); openSave(); }
    if (e.key === 'Escape' && !dialog.hidden) { e.preventDefault(); closeDialog(); }
    if (e.key === 'F7') { e.preventDefault(); bootHelp.textContent = 'Le mode avancé donne accès à tous les réglages : à explorer plus tard, une fois le PC stable.'; }
  });

  // ---------------------------------------------------------------- horloge et capteurs
  const fmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
  const tick = () => { clock.textContent = fmt.format(new Date()); };
  tick();
  setInterval(tick, 30000);
  setInterval(() => {
    if (document.hidden) return;
    const t = 37 + Math.round(Math.random() * 4);
    temp.textContent = `${t} °C`;
    fan.textContent = `${(780 + Math.round(Math.random() * 90)).toLocaleString('fr-FR')} tr/min`;
  }, 2500);

  // ---------------------------------------------------------------- profil EXPO / XMP
  function setExpo(on) {
    expo.setAttribute('aria-pressed', String(on));
    expo.textContent = on ? 'EXPO I · 6000 MT/s' : 'Désactivé';
    root.querySelectorAll('[data-bios="mem-speed"]').forEach((e) => { e.textContent = on ? '6 000 MT/s' : '4 800 MT/s'; });
    root.querySelectorAll('[data-bios="mem-cl"]').forEach((e) => { e.textContent = on ? '30' : '40'; });
    root.querySelectorAll('[data-bios="mem-v"]').forEach((e) => { e.textContent = on ? '1,35 V' : '1,10 V'; });
    expoHelp.textContent = on
      ? 'Profil activé : la mémoire tournera à sa vitesse annoncée (6 000 MT/s, CL30, 1,35 V) après enregistrement et redémarrage.'
      : 'Profil désactivé : la mémoire tourne à sa vitesse standard (JEDEC), plus basse que celle annoncée sur la boîte.';
  }
  expo.addEventListener('click', () => setExpo(expo.getAttribute('aria-pressed') !== 'true'));

  // ---------------------------------------------------------------- ordre de démarrage
  function firstDevice() { return bootList.firstElementChild?.dataset.dev; }
  function updateBootHelp() {
    const first = firstDevice();
    bootHelp.textContent = first === 'usb'
      ? 'La clé USB est en tête : au prochain démarrage, le PC lancera l\'installation du système.'
      : first === 'ssd'
        ? 'Le SSD est en tête : le PC démarre sur le système installé. Pour l\'installation, place la clé USB en premier.'
        : 'Le démarrage réseau sert surtout en entreprise : remets la clé USB ou le SSD en tête.';
  }
  bootList.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-move]');
    if (!btn) return;
    const li = btn.closest('li');
    if (btn.dataset.move === 'up' && li.previousElementSibling) li.parentNode.insertBefore(li, li.previousElementSibling);
    if (btn.dataset.move === 'down' && li.nextElementSibling) li.parentNode.insertBefore(li.nextElementSibling, li);
    li.classList.add('is-moved');
    setTimeout(() => li.classList.remove('is-moved'), 600);
    btn.focus();
    updateBootHelp();
  });
  updateBootHelp();

  // ---------------------------------------------------------------- enregistrer et quitter
  function openSave() {
    const changes = [];
    const expoOn = expo.getAttribute('aria-pressed') === 'true';
    if (expoOn !== saved.expo) changes.push(expoOn ? 'Profil mémoire : EXPO activé (6 000 MT/s)' : 'Profil mémoire : désactivé');
    const first = firstDevice();
    if (first !== saved.first) {
      const label = bootList.firstElementChild.querySelector('span').textContent;
      changes.push(`Premier périphérique de démarrage : ${label}`);
    }
    dialogList.replaceChildren(...(changes.length ? changes : ['Aucune modification']).map((c) => {
      const li = document.createElement('li');
      li.textContent = c;
      return li;
    }));
    dialog.hidden = false;
    document.getElementById('bios-ok').focus();
  }
  function closeDialog() {
    dialog.hidden = true;
    root.focus();
  }
  function doReboot(apply) {
    dialog.hidden = true;
    if (apply) {
      saved.expo = expo.getAttribute('aria-pressed') === 'true';
      saved.first = firstDevice();
    } else {
      setExpo(saved.expo);
    }
    reboot.hidden = false;
    setTimeout(() => {
      reboot.hidden = true;
      select(0);
      root.focus();
    }, 1600);
  }
  document.getElementById('bios-save').addEventListener('click', openSave);
  document.getElementById('bios-discard').addEventListener('click', () => doReboot(false));
  document.getElementById('bios-ok').addEventListener('click', () => doReboot(true));
  document.getElementById('bios-cancel').addEventListener('click', closeDialog);
}
