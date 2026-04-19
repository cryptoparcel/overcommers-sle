
(function(){
  const surface = document.getElementById('pbSurface');
  const input = document.getElementById('layout_json');
  const form = document.getElementById('pbSaveForm');
  const raw = (document.getElementById('pbInitialJson')?.textContent || '{"version":1,"canvas":{},"blocks":[]}');
  let state;
  try { state = JSON.parse(raw); } catch(e){ state = {version:1, canvas:{minHeight:560}, blocks:[]}; }

  if (!state.canvas) state.canvas = {};
  if (!Array.isArray(state.blocks)) state.blocks = [];
  if (!state.canvas.minHeight) state.canvas.minHeight = 560;

  surface.style.height = `${Number(state.canvas.minHeight)}px`;

  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  const uid = () => 'b' + Math.random().toString(16).slice(2);

  let selectedId = state.blocks[0]?.id || null;
  let drag = null;
  let resize = null;

  function pxFromPct(val, axis){
    const rect = surface.getBoundingClientRect();
    return axis === 'x' ? (val/100)*rect.width : (val/100)*rect.height;
  }
  function pctFromPx(px, axis){
    const rect = surface.getBoundingClientRect();
    return axis === 'x' ? (px/rect.width)*100 : (px/rect.height)*100;
  }
  function serialize(){
    input.value = JSON.stringify(state);
  }

  function render(){
    surface.innerHTML = '';
    const rect = surface.getBoundingClientRect();

    state.blocks.forEach(b => {
      const el = document.createElement('div');
      el.className = 'pb-item' + (b.id===selectedId ? ' selected' : '');
      el.dataset.id = b.id;

      const x = pxFromPct(b.x||0, 'x');
      const y = pxFromPct(b.y||0, 'y');
      const w = pxFromPct(b.w||30, 'x');
      const h = pxFromPct(b.h||20, 'y');

      el.style.left = `${x}px`;
      el.style.top = `${y}px`;
      el.style.width = `${Math.max(160, w)}px`;
      el.style.height = `${Math.max(120, h)}px`;

      const title = (b.content && b.content.title) ? b.content.title : (b.id || 'Block');
      const body = (b.content && b.content.body) ? b.content.body : '';

      el.innerHTML = `
        <div class="pb-item__title">${escapeHtml(title)}</div>
        <div class="pb-item__body">${escapeHtml(body).slice(0,160)}${body.length>160?'…':''}</div>
      `;

      const handle = document.createElement('div');
      handle.className = 'pb-handle br';
      handle.title = 'Resize';
      el.appendChild(handle);

      el.addEventListener('pointerdown', (e) => {
        const id = el.dataset.id;
        selectedId = id;
        const block = state.blocks.find(x => x.id === id);
        if (!block) return;

        const isHandle = e.target.classList.contains('pb-handle');
        const start = { x: e.clientX, y: e.clientY };
        const startB = { x:block.x||0, y:block.y||0, w:block.w||20, h:block.h||20 };

        if (isHandle) {
          resize = { id, start, startB };
        } else {
          drag = { id, start, startB };
        }
        renderPanel();
        render();
        el.setPointerCapture(e.pointerId);
      });

      surface.appendChild(el);
    });

    renderPanel();
  }

  function escapeHtml(s){
    return String(s||'').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderPanel(){
    const panel = document.getElementById('pbPanel');
    if (!panel) return;
    const block = state.blocks.find(b => b.id === selectedId) || null;

    if (!block){
      panel.innerHTML = `
        <p class="muted">No blocks yet.</p>
        <div class="pb-btnrow">
          <button class="btn primary" type="button" id="pbAdd">Add card</button>
        </div>
      `;
      document.getElementById('pbAdd')?.addEventListener('click', addBlock);
      return;
    }

    if (!block.content) block.content = {};
    if (!block.content.buttons) block.content.buttons = [];

    panel.innerHTML = `
      <div class="pb-field">
        <label>Title</label>
        <input id="pbTitle" value="${escapeHtml(block.content.title || '')}">
      </div>
      <div class="pb-field">
        <label>Body</label>
        <textarea id="pbBody">${escapeHtml(block.content.body || '')}</textarea>
      </div>
      <div class="pb-field">
        <label>Buttons (one per line: Label | /path)</label>
        <textarea id="pbButtons">${escapeHtml((block.content.buttons||[]).map(b=>`${b.label} | ${b.href}`).join('\n'))}</textarea>
      </div>
      <div class="pb-field">
        <label>Note (optional)</label>
        <input id="pbNote" value="${escapeHtml(block.content.note || '')}">
      </div>
      <div class="pb-btnrow">
        <button class="btn primary" type="button" id="pbSaveBlock">Apply</button>
        <button class="btn" type="button" id="pbAdd">Add card</button>
        <button class="btn danger" type="button" id="pbDelete">Delete</button>
      </div>
    `;

    document.getElementById('pbSaveBlock')?.addEventListener('click', () => {
      block.content.title = document.getElementById('pbTitle').value.trim();
      block.content.body = document.getElementById('pbBody').value.trim();
      block.content.note = document.getElementById('pbNote').value.trim() || null;

      const lines = document.getElementById('pbButtons').value.split('\n').map(x=>x.trim()).filter(Boolean);
      block.content.buttons = lines.map(line => {
        const parts = line.split('|').map(x=>x.trim());
        return { label: parts[0] || 'Button', href: parts[1] || '#' };
      });

      render();
    });

    document.getElementById('pbAdd')?.addEventListener('click', addBlock);
    document.getElementById('pbDelete')?.addEventListener('click', () => {
      if (!confirm('Delete this block?')) return;
      state.blocks = state.blocks.filter(b => b.id !== selectedId);
      selectedId = state.blocks[0]?.id || null;
      render();
    });
  }

  function addBlock(){
    const id = uid();
    state.blocks.push({
      id,
      type: "card",
      x: 5,
      y: 5,
      w: 40,
      h: 22,
      content: {
        title: "New card",
        body: "Edit me in the panel.",
        buttons: [{label:"Learn more", href:"/"}],
      }
    });
    selectedId = id;
    render();
  }

  function onMove(e){
    const rect = surface.getBoundingClientRect();
    if (drag){
      const block = state.blocks.find(b => b.id === drag.id);
      const dx = e.clientX - drag.start.x;
      const dy = e.clientY - drag.start.y;
      const nx = drag.startB.x + pctFromPx(dx, 'x');
      const ny = drag.startB.y + pctFromPx(dy, 'y');
      block.x = clamp(nx, 0, 100);
      block.y = clamp(ny, 0, 100);
      render();
    }
    if (resize){
      const block = state.blocks.find(b => b.id === resize.id);
      const dx = e.clientX - resize.start.x;
      const dy = e.clientY - resize.start.y;
      const nw = resize.startB.w + pctFromPx(dx, 'x');
      const nh = resize.startB.h + pctFromPx(dy, 'y');
      block.w = clamp(nw, 12, 100);
      block.h = clamp(nh, 12, 100);
      render();
    }
  }

  surface.addEventListener('pointermove', onMove);
  surface.addEventListener('pointerup', () => { drag = null; resize = null; });

  form?.addEventListener('submit', () => { serialize(); });

  render();
})();
