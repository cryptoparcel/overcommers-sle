/* ──────────────────────────────────────────────────────────────
   Photo Uploader — drag-drop + file picker + reorder + remove
   ──────────────────────────────────────────────────────────────
   Works with a textarea of newline-separated URLs (existing format
   for Opening.photos) or a single-URL text input (Event.image_url).

   USAGE (multi-photo, like Opening):
     <textarea id="photos" name="photos"></textarea>
     <script>
       PhotoUploader.init({
         targetSelector: '#photos',
         mode: 'multiple',
         uploadUrl: '/admin/upload-photo',
       });
     </script>

   USAGE (single-photo, like Event):
     <input type="text" id="image_url" name="image_url">
     <script>
       PhotoUploader.init({
         targetSelector: '#image_url',
         mode: 'single',
         uploadUrl: '/admin/upload-photo',
       });
     </script>
   ────────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  function getCSRFToken() {
    // Flask-WTF puts it in every form as a hidden input
    var input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'style' && typeof attrs[k] === 'object') {
          Object.assign(e.style, attrs[k]);
        } else if (k === 'class') {
          e.className = attrs[k];
        } else if (k.indexOf('on') === 0 && typeof attrs[k] === 'function') {
          e.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
        } else {
          e.setAttribute(k, attrs[k]);
        }
      });
    }
    (children || []).forEach(function (c) {
      if (c == null) return;
      e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return e;
  }

  function parseUrls(target, mode) {
    if (mode === 'single') {
      var v = (target.value || '').trim();
      return v ? [v] : [];
    }
    return (target.value || '')
      .split('\n')
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
  }

  function writeUrls(target, urls, mode) {
    target.value = mode === 'single' ? (urls[0] || '') : urls.join('\n');
    // Fire a change event in case other code is listening
    target.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function buildDropzone() {
    var dz = el('div', { class: 'photo-uploader' });
    dz.innerHTML = [
      '<div class="photo-uploader__zone" data-zone>',
        '<svg class="photo-uploader__zone-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">',
          '<rect x="3" y="5" width="18" height="14" rx="2"/>',
          '<circle cx="9" cy="11" r="2"/>',
          '<path d="M21 16l-5-5-8 8"/>',
        '</svg>',
        '<div class="photo-uploader__zone-text">',
          '<strong>Drop photos here</strong> or click to browse',
        '</div>',
        '<div class="photo-uploader__zone-sub">JPG, PNG, GIF, WEBP · up to 16 MB each</div>',
      '</div>',
      '<div class="photo-uploader__thumbs" data-thumbs></div>',
    ].join('');
    return dz;
  }

  function buildThumb(url, isFirst) {
    var wrap = el('div', {
      class: 'photo-uploader__thumb',
      draggable: 'true',
      'data-url': url,
    });
    wrap.innerHTML = [
      '<img src="' + url.replace(/"/g, '&quot;') + '" alt="" loading="lazy">',
      isFirst ? '<span class="photo-uploader__thumb-badge">Cover</span>' : '',
      '<button type="button" class="photo-uploader__thumb-remove" data-remove aria-label="Remove">',
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>',
      '</button>',
      '<div class="photo-uploader__thumb-drag" aria-hidden="true">',
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="6" r="1" fill="currentColor"/><circle cx="15" cy="6" r="1" fill="currentColor"/><circle cx="9" cy="12" r="1" fill="currentColor"/><circle cx="15" cy="12" r="1" fill="currentColor"/><circle cx="9" cy="18" r="1" fill="currentColor"/><circle cx="15" cy="18" r="1" fill="currentColor"/></svg>',
      '</div>',
    ].join('');
    return wrap;
  }

  function buildUploadingStub() {
    var stub = el('div', { class: 'photo-uploader__thumb photo-uploader__thumb--uploading' });
    stub.innerHTML = '<div class="photo-uploader__spinner"></div><div class="photo-uploader__progress">Uploading…</div>';
    return stub;
  }

  function renderThumbs(container, urls, mode) {
    container.innerHTML = '';
    urls.forEach(function (url, i) {
      container.appendChild(buildThumb(url, mode === 'multiple' && i === 0));
    });
  }

  function uploadFile(file, uploadUrl) {
    var fd = new FormData();
    fd.append('file', file);
    var token = getCSRFToken();
    return fetch(uploadUrl, {
      method: 'POST',
      body: fd,
      headers: token ? { 'X-CSRFToken': token } : {},
      credentials: 'same-origin',
    }).then(function (r) {
      if (!r.ok) {
        return r.json().then(function (j) {
          throw new Error(j.error || 'Upload failed (' + r.status + ')');
        }).catch(function () {
          throw new Error('Upload failed (' + r.status + ')');
        });
      }
      return r.json();
    });
  }

  function init(opts) {
    var target = document.querySelector(opts.targetSelector);
    if (!target) return;
    var mode = opts.mode === 'single' ? 'single' : 'multiple';
    var uploadUrl = opts.uploadUrl || '/admin/upload-photo';

    // Hide the raw input/textarea but keep it in the form
    target.style.display = 'none';

    // Build and insert UI after the target
    var ui = buildDropzone();
    target.parentNode.insertBefore(ui, target.nextSibling);

    var zone = ui.querySelector('[data-zone]');
    var thumbs = ui.querySelector('[data-thumbs]');

    // Current URL list state
    var urls = parseUrls(target, mode);
    renderThumbs(thumbs, urls, mode);

    // Hidden file input
    var fileInput = el('input', {
      type: 'file',
      accept: 'image/jpeg,image/png,image/gif,image/webp',
      multiple: mode === 'multiple' ? 'multiple' : null,
      style: { display: 'none' },
    });
    ui.appendChild(fileInput);

    function sync() {
      writeUrls(target, urls, mode);
      renderThumbs(thumbs, urls, mode);
    }

    function handleFiles(fileList) {
      var files = Array.from(fileList || []);
      if (files.length === 0) return;

      // In single mode we only take the first file and replace
      if (mode === 'single') files = files.slice(0, 1);

      files.forEach(function (file) {
        if (!file.type || !file.type.startsWith('image/')) {
          alert('Skipped non-image file: ' + file.name);
          return;
        }
        // Show uploading stub
        var stub = buildUploadingStub();
        thumbs.appendChild(stub);

        uploadFile(file, uploadUrl).then(function (res) {
          stub.remove();
          if (res && res.url) {
            if (mode === 'single') {
              urls = [res.url];
            } else {
              urls.push(res.url);
            }
            sync();
          } else {
            alert('Upload failed: no URL returned');
          }
        }).catch(function (err) {
          stub.remove();
          alert('Upload failed: ' + err.message);
        });
      });
    }

    // Click to browse
    zone.addEventListener('click', function () { fileInput.click(); });
    fileInput.addEventListener('change', function (e) {
      handleFiles(e.target.files);
      e.target.value = ''; // allow re-selecting same file
    });

    // Drag enter/over/leave
    ['dragenter', 'dragover'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('is-dragging');
      });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('is-dragging');
      });
    });
    zone.addEventListener('drop', function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      handleFiles(files);
    });

    // Remove + reorder via delegation
    thumbs.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-remove]');
      if (!btn) return;
      var thumb = btn.closest('.photo-uploader__thumb');
      var url = thumb.getAttribute('data-url');
      urls = urls.filter(function (u) { return u !== url; });
      sync();
    });

    // Drag to reorder (multi mode only)
    if (mode === 'multiple') {
      var draggingEl = null;
      thumbs.addEventListener('dragstart', function (e) {
        var t = e.target.closest('.photo-uploader__thumb');
        if (!t) return;
        draggingEl = t;
        t.classList.add('is-dragging-thumb');
        try { e.dataTransfer.setData('text/plain', t.getAttribute('data-url')); } catch (_) {}
        e.dataTransfer.effectAllowed = 'move';
      });
      thumbs.addEventListener('dragend', function () {
        if (draggingEl) draggingEl.classList.remove('is-dragging-thumb');
        draggingEl = null;
        // Read new order from DOM
        urls = Array.from(thumbs.querySelectorAll('.photo-uploader__thumb'))
          .map(function (t) { return t.getAttribute('data-url'); })
          .filter(Boolean);
        sync();
      });
      thumbs.addEventListener('dragover', function (e) {
        e.preventDefault();
        var target = e.target.closest('.photo-uploader__thumb');
        if (!target || !draggingEl || target === draggingEl) return;
        var rect = target.getBoundingClientRect();
        var after = (e.clientX - rect.left) > rect.width / 2;
        if (after) {
          target.parentNode.insertBefore(draggingEl, target.nextSibling);
        } else {
          target.parentNode.insertBefore(draggingEl, target);
        }
      });
    }
  }

  window.PhotoUploader = { init: init };
})();
