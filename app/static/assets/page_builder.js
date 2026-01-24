(function(){
  const surface = document.getElementById('pbSurface');
  const input = document.getElementById('layout_json');
  const form = document.getElementById('pbSaveForm');
  const raw = (document.getElementById('pbInitialJson')?.textContent || '{"version":1,"canvas":{},"blocks":[]}');

  let state;
  try { state = JSON.parse(raw); } catch(e){ state = {version:1, canvas:{minHeight:560}, blocks:[]}; }

  if (!state.canvas) state.canvas = {};
  if (!Array.isArray(state.blocks)) state.blocks = [];

  const minH = Number(state.canvas.minHeight || 560);
  surface.style.height = `${minH}px`;

  const uid = () => 'b' + Math.random().toString(16).slice(2, 10);

  let selectedId = null;
  let drag = null;
  let resize = null;

  function clamp(n, a, b){ return Math.max(a, Math.min(b, n)); }

  function toPct(px, total){ return (px / total) * 100; }
  function toPx(pct, total){ return (pct / 100) * total; }

  function blockById(id){ return state.blocks.find(b => b.id === id); }

  function serialize(){
    input.value = JSON.stringify({
      version: state.version || 1,
      canvas: {minHeight: state.canvas.minHeight || minH},
      blocks: state.blocks
    });
  }

  function render(){
    surface.querySelectorAll('.pb-block').forEach(n => n.remove());
    const W = surface.clientWidth;
    const H = surface.clientHeight;
    state.blocks.forEach((b, idx) => {
      const el = document.createElement('div');
      el.className = 'pb-block' + (b.id === selectedId ? ' is-selected' : '');
      el.dataset.id = b.id;

      const left = toPx(b.x || 0, W);
      const top = toPx(b.y || 0, H);
      const width = toPx(b.w || 30, W);
      const height = toPx(b.h || 18, H);
      el.style.left = `${left}px`;
      el.style.top = `${top}px`;
      el.style.width = `${width}px`;
      el.style.height = `${height}px`;

      const inner = document.createElement('div');
      inner.className = 'pb-block__inner';

      // Content preview
      inner.innerHTML = previewHtml(b);
      el.appendChild(inner);

      // Resize handle
      const handle = document.createElement('div');
      handle.className = 'pb-handle';
      handle.title = 'Resize';
      el.appendChild(handle);

      // Small label
      const label = document.createElement('div');
      label.className = 'pb-label';
      label.textContent = (b.type || 'block') + ` • ${idx+1}`;
      el.appendChild(label);

      surface.appendChild(el);
    });
    updateInspector();
    serialize();
  }

  function esc(s){
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  }

  function previewHtml(b){
    const t = b.type || 'card';
    const c = b.content || {};
    if (t === 'text'){
      return `<div><div style="font-weight:800;margin-bottom:6px">${esc(c.title || 'Text block')}</div><div style="opacity:.85">${esc(c.body || 'Edit this text in the inspector.')}</div></div>`;
    }
    if (t === 'button'){
      return `<div style="display:flex;align-items:center;justify-content:center;height:100%"><span class="btn">${esc(c.label || 'Button')}</span></div>`;
    }
    if (t === 'image'){
      const url = c.url || '';
      return `<div style="height:100%;border-radius:14px;overflow:hidden;border:1px solid rgba(0,0,0,.08);background:rgba(255,255,255,.55);display:flex;align-items:center;justify-content:center;text-align:center;padding:12px">
        <div>
          <div style="font-weight:800;margin-bottom:6px">Image</div>
          <div style="opacity:.75;font-size:12px">${url ? esc(url) : 'Paste an image URL or upload later'}</div>
        </div>
      </div>`;
    }
    // card default
    const buttons = (c.buttons || []).slice(0,2).map(btn => `<span class="btn" style="margin-right:8px">${esc(btn.label || 'Button')}</span>`).join('');
    return `<div style="height:100%;border-radius:18px;overflow:hidden;border:1px solid rgba(0,0,0,.08);background:rgba(255,255,255,.8);box-shadow:0 14px 40px rgba(0,0,0,.06);padding:18px">
      <div style="font-weight:900;margin-bottom:8px">${esc(c.title || 'Card')}</div>
      <div style="opacity:.85;line-height:1.35">${esc(c.body || 'Card text. Add buttons, links, and more.')}</div>
      <div style="margin-top:12px">${buttons}</div>
    </div>`;
  }

  function select(id){
    selectedId = id;
    render();
  }

  function updateInspector(){
    const b = selectedId ? blockById(selectedId) : null;
    const $ = (id) => document.getElementById(id);
    const empty = !b;
    ['pb_type','pb_title','pb_body','pb_url','pb_btn1_label','pb_btn1_url','pb_btn2_label','pb_btn2_url','pb_x','pb_y','pb_w','pb_h'].forEach(i=>{
      const el = $(i);
      if (!el) return;
      el.disabled = empty;
      if (empty) el.value = '';
    });
    if (!b) return;

    const c = b.content || (b.content = {});
    const buttons = c.buttons || (c.buttons = []);
    while (buttons.length < 2) buttons.push({label:'', url:''});

    $('pb_type').value = b.type || 'card';
    $('pb_title').value = c.title || '';
    $('pb_body').value = c.body || '';
    $('pb_url').value = c.url || '';
    $('pb_btn1_label').value = buttons[0].label || '';
    $('pb_btn1_url').value = buttons[0].url || '';
    $('pb_btn2_label').value = buttons[1].label || '';
    $('pb_btn2_url').value = buttons[1].url || '';

    $('pb_x').value = Math.round(b.x ?? 0);
    $('pb_y').value = Math.round(b.y ?? 0);
    $('pb_w').value = Math.round(b.w ?? 30);
    $('pb_h').value = Math.round(b.h ?? 18);
  }

  function applyInspector(){
    if (!selectedId) return;
    const b = blockById(selectedId);
    if (!b) return;
    const $ = (id) => document.getElementById(id);

    b.type = $('pb_type').value;
    b.content = b.content || {};
    b.content.title = $('pb_title').value;
    b.content.body = $('pb_body').value;

    if (b.type === 'image'){
      b.content.url = $('pb_url').value;
    }
    if (b.type === 'button'){
      b.content.label = $('pb_btn1_label').value || 'Button';
      b.content.url = $('pb_btn1_url').value || '#';
    }

    const btns = b.content.buttons || (b.content.buttons = [{},{}]);
    while (btns.length < 2) btns.push({});
    btns[0].label = $('pb_btn1_label').value;
    btns[0].url = $('pb_btn1_url').value;
    btns[1].label = $('pb_btn2_label').value;
    btns[1].url = $('pb_btn2_url').value;

    b.x = clamp(Number($('pb_x').value || 0), 0, 95);
    b.y = clamp(Number($('pb_y').value || 0), 0, 95);
    b.w = clamp(Number($('pb_w').value || 30), 5, 100);
    b.h = clamp(Number($('pb_h').value || 18), 6, 100);
    render();
  }

  // Toolbar actions
  document.querySelectorAll('[data-pb-add]').forEach(btn => {
    btn.addEventListener('click', () => {
      const t = btn.getAttribute('data-pb-add');
      const id = uid();
      const b = {
        id,
        type: t,
        x: 6,
        y: 6,
        w: t === 'button' ? 22 : (t === 'image' ? 34 : 40),
        h: t === 'text' ? 18 : (t === 'image' ? 30 : 24),
        content: {}
      };
      if (t === 'text') b.content = {title:'New text', body:'Edit me'};
      if (t === 'card') b.content = {title:'New card', body:'Edit this card text', buttons:[{label:'Action', url:'#'}]};
      if (t === 'button') b.content = {label:'Button', url:'#'};
      if (t === 'image') b.content = {url:''};
      if (t === 'spacer') b.type = 'spacer';
      state.blocks.push(b);
      select(id);
    });
  });

  document.getElementById('pbDeleteBtn')?.addEventListener('click', () => {
    if (!selectedId) return;
    state.blocks = state.blocks.filter(b => b.id !== selectedId);
    selectedId = null;
    render();
  });

  // Inspector change listeners
  ['pb_type','pb_title','pb_body','pb_url','pb_btn1_label','pb_btn1_url','pb_btn2_label','pb_btn2_url','pb_x','pb_y','pb_w','pb_h'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', applyInspector);
    document.getElementById(id)?.addEventListener('change', applyInspector);
  });

  // Drag/resize interactions
  surface.addEventListener('pointerdown', (e) => {
    const blockEl = e.target.closest('.pb-block');
    if (!blockEl) return;
    const id = blockEl.dataset.id;
    select(id);

    const b = blockById(id);
    if (!b) return;

    const rect = surface.getBoundingClientRect();
    const W = surface.clientWidth;
    const H = surface.clientHeight;
    const isHandle = e.target.classList.contains('pb-handle');

    if (isHandle){
      resize = {
        id,
        startX: e.clientX,
        startY: e.clientY,
        startW: toPx(b.w || 30, W),
        startH: toPx(b.h || 18, H),
        surfaceW: W,
        surfaceH: H
      };
      blockEl.setPointerCapture(e.pointerId);
      return;
    }

    drag = {
      id,
      startX: e.clientX,
      startY: e.clientY,
      startLeft: toPx(b.x || 0, W),
      startTop: toPx(b.y || 0, H),
      surfaceW: W,
      surfaceH: H
    };
    blockEl.setPointerCapture(e.pointerId);
  });

  surface.addEventListener('pointermove', (e) => {
    if (!drag && !resize) return;
    const W = surface.clientWidth;
    const H = surface.clientHeight;

    if (drag){
      const b = blockById(drag.id);
      if (!b) return;
      const dx = e.clientX - drag.startX;
      const dy = e.clientY - drag.startY;
      const left = clamp(drag.startLeft + dx, 0, W - 20);
      const top = clamp(drag.startTop + dy, 0, H - 20);
      b.x = clamp(toPct(left, W), 0, 95);
      b.y = clamp(toPct(top, H), 0, 95);
      render();
    }

    if (resize){
      const b = blockById(resize.id);
      if (!b) return;
      const dx = e.clientX - resize.startX;
      const dy = e.clientY - resize.startY;
      const newW = clamp(resize.startW + dx, 80, W);
      const newH = clamp(resize.startH + dy, 60, H);
      b.w = clamp(toPct(newW, W), 5, 100);
      b.h = clamp(toPct(newH, H), 6, 100);
      render();
    }
  });

  surface.addEventListener('pointerup', () => {
    drag = null;
    resize = null;
  });

  form?.addEventListener('submit', () => {
    serialize();
  });

  // Initial selection
  if (state.blocks.length) selectedId = state.blocks[0].id;
  render();
})();
