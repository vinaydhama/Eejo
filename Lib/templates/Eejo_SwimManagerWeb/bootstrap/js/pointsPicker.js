

{/* <script type="module"> */}
// Export a function you can `await` from any page
export function openPointsPicker(options = {}) {
  const schemes = options.schemes ?? [
    { id: 1, label: 'Option 1 — 7,5,3 then 0s', array: [7,5,3,0,0,0,0,0,0,0] },
    { id: 2, label: 'Option 2 — example',      array: [10,6,4,2,1,0,0,0,0,0] },
    { id: 3, label: 'Option 3 — example',      array: [9,7,6,5,4,3,2,1,0,0] },
  ];
  const initialSchemeId = options.initialSchemeId ?? 1;

  // Create a dialog
  const dlg = document.createElement('dialog');
  dlg.style.padding = '0';
  dlg.style.border = '0';
  dlg.style.maxWidth = '640px';
  dlg.style.width = 'min(95vw, 640px)';
  dlg.style.borderRadius = '10px';
  dlg.style.boxShadow = '0 12px 28px rgba(0,0,0,.2)';
  dlg.innerHTML = `
    <form method="dialog" style="margin:0;background:#fff;color:#0e1116;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
      <header style="padding:14px 16px;border-bottom:1px solid #d0d7de;display:flex;justify-content:space-between;align-items:center;">
        <strong>Points (10 places)</strong>
        <button value="cancel" aria-label="Close" style="border:0;background:transparent;font-size:18px;cursor:pointer;">✕</button>
      </header>

      <section style="padding:12px 16px;">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
          <label for="scheme"><strong>Scheme</strong></label>
          <select id="scheme" style="padding:6px 8px;border:1px solid #d0d7de;border-radius:6px;"></select>
          <button id="btn-fill" type="button" style="padding:6px 10px;border:1px solid #0a84ff;border-radius:6px;background:#fff;cursor:pointer;">Auto Fill</button>
          <button id="btn-clear" type="button" style="padding:6px 10px;border:1px solid #d0d7de;border-radius:6px;background:#fff;cursor:pointer;">Clear</button>
        </div>

        <div id="grid" style="display:grid;grid-template-columns:repeat(5, minmax(80px,120px));gap:8px;"></div>
        <div style="font-size:12px;color:#666;margin-top:6px;">Enter points manually or use a scheme. Press <strong>OK</strong> to return the array.</div>
      </section>

      <footer style="padding:12px 16px;border-top:1px solid #d0d7de;display:flex;justify-content:flex-end;gap:8px;">
        <button value="cancel" style="padding:8px 12px;border:1px solid #d0d7de;border-radius:6px;background:#fff;cursor:pointer;">Cancel</button>
        <button id="ok" value="ok" style="padding:8px 12px;border:1px solid #0a84ff;border-radius:6px;background:#fff;cursor:pointer;">OK</button>
      </footer>
    </form>
  `;
  document.body.appendChild(dlg);

  // Wire controls
  const schemeSel = dlg.querySelector('#scheme');
  const btnFill   = dlg.querySelector('#btn-fill');
  const btnClear  = dlg.querySelector('#btn-clear');
  const grid      = dlg.querySelector('#grid');

  // Populate scheme options
  for (const s of schemes) {
    const opt = document.createElement('option');
    opt.value = String(s.id);
    opt.textContent = s.label;
    opt.dataset.array = JSON.stringify(s.array);
    if (s.id === initialSchemeId) opt.selected = true;
    schemeSel.appendChild(opt);
  }

  // Build 10 inputs
  const inputs = [];
  for (let i = 0; i < 10; i++) {
    const wrap = document.createElement('div');
    wrap.innerHTML = `
      <label style="font-size:12px;color:#555;display:block;margin-bottom:4px;">Place ${i+1}</label>
      <input type="number" inputmode="numeric" min="0" step="1"
             style="width:100%;padding:6px 8px;border:1px solid #d0d7de;border-radius:6px;" />
    `;
    grid.appendChild(wrap);
    inputs.push(wrap.querySelector('input'));
  }

  // Helpers
  const fillBySelected = () => {
    const opt = schemeSel.selectedOptions[0];
    const arr = JSON.parse(opt.dataset.array || '[]');
    const ten = Array.from({length:10}, (_, i) => Number(arr[i] ?? 0));
    ten.forEach((v, i) => (inputs[i].value = String(v)));
  };
  const clearAll = () => inputs.forEach(inp => (inp.value = ''));

  // Events
  btnFill.addEventListener('click', fillBySelected);
  btnClear.addEventListener('click', clearAll);

  // Autofill once on open
  fillBySelected();

  // Return a Promise that resolves with the 10-element array (or null if cancelled)
  return new Promise((resolve) => {
    dlg.addEventListener('close', () => {
      const ok = dlg.returnValue === 'ok';
      const values = inputs.map(inp => {
        const t = inp.value.trim();
        return t === '' ? 0 : Number(t);
      });
      dlg.remove();           // cleanup
      resolve(ok ? values : null);
    });

    // Show the modal dialog
    try { dlg.showModal(); }  // supported in modern browsers
    catch { dlg.setAttribute('open', ''); } // fallback (acts like non-modal)
  });
}
// </script>
