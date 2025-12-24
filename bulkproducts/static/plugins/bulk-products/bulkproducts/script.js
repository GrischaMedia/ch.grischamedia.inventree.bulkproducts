(function() {
  const BP = window.BULKPRODUCTS || {};
  const categories = BP.categories || [];
  const defaultLocationId = BP.defaultLocationId || 0;
  const apiUrl = BP.apiUrl || '';
  const searchLocationsUrl = BP.searchLocationsUrl || '';
  const csrfToken = BP.csrf || '';
  
  let createdParts = [];
  let locationSearchTimeouts = new Map();

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return csrfToken || null;
  }

  function setAlert(kind, msg) {
    const el = document.getElementById('bp-alert');
    if (!el) return;
    el.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-info', 'alert-warning');
    el.classList.add(`alert-${kind}`);
    el.textContent = msg;
  }

  function clearAlert() {
    const el = document.getElementById('bp-alert');
    if (!el) return;
    el.classList.add('d-none');
    el.textContent = '';
  }

  function optionHtml(list, selectedId, placeholder) {
    const ph = placeholder ? `<option value="">${placeholder}</option>` : '';
    return ph + list.map(o => `<option value="${o.id}" ${String(o.id) === String(selectedId) ? 'selected' : ''}>${o.label}</option>`).join('');
  }

  async function searchLocations(query, inputEl, hiddenInput) {
    if (query.length < 1) {
      const dropdown = inputEl.parentElement.querySelector('.bp-location-dropdown');
      if (dropdown) dropdown.classList.remove('show');
      return;
    }

    try {
      const res = await fetch(`${searchLocationsUrl}?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      const results = data.results || [];

      const dropdown = inputEl.parentElement.querySelector('.bp-location-dropdown');
      if (!dropdown) return;

      dropdown.innerHTML = '';
      if (results.length === 0) {
        const noResult = document.createElement('div');
        noResult.className = 'bp-location-item';
        noResult.textContent = 'Keine Ergebnisse';
        dropdown.appendChild(noResult);
      } else {
        results.forEach(loc => {
          const item = document.createElement('div');
          item.className = 'bp-location-item';
          item.textContent = loc.text;
          item.dataset.locationId = loc.id;
          item.addEventListener('click', () => {
            inputEl.value = loc.text;
            hiddenInput.value = loc.id;
            dropdown.classList.remove('show');
          });
          dropdown.appendChild(item);
        });
      }
      dropdown.classList.add('show');
    } catch (e) {
      console.error('Location search error:', e);
    }
  }

  function setupLocationInput(inputEl, hiddenInput) {
    const wrapper = inputEl.parentElement;
    const dropdown = wrapper.querySelector('.bp-location-dropdown');
    const timeoutKey = inputEl;
    
    inputEl.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      
      if (locationSearchTimeouts.has(timeoutKey)) {
        clearTimeout(locationSearchTimeouts.get(timeoutKey));
      }
      
      const timeout = setTimeout(() => {
        searchLocations(query, inputEl, hiddenInput);
      }, 300);
      locationSearchTimeouts.set(timeoutKey, timeout);
    });

    inputEl.addEventListener('focus', () => {
      if (inputEl.value.trim().length > 0) {
        searchLocations(inputEl.value.trim(), inputEl, hiddenInput);
      }
    });

    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        if (dropdown) dropdown.classList.remove('show');
      }
    });
  }

  function rowHtml(rowId) {
    return `
      <tr data-row-id="${rowId}">
        <td class="text-center"></td>
        <td>
          <select class="form-select form-select-sm bp-category">
            ${optionHtml(categories, '', 'Kategorie wählen')}
          </select>
        </td>
        <td><input class="form-control form-control-sm bp-name" type="text" placeholder="Produktname" /></td>
        <td><input class="form-control form-control-sm bp-description" type="text" placeholder="Beschreibung" /></td>
        <td><input class="form-control form-control-sm bp-ipn" type="text" placeholder="IPN" /></td>
        <td><input class="form-control form-control-sm bp-quantity" type="number" min="0" step="1" value="0" /></td>
        <td>
          <div class="bp-location-wrapper">
            <input type="text" class="bp-location-input bp-location-search" placeholder="Lagerort suchen..." autocomplete="off" />
            <input type="hidden" class="bp-location-id" value="" />
            <div class="bp-location-dropdown"></div>
          </div>
        </td>
        <td class="text-end">
          <button type="button" class="btn btn-sm btn-outline-danger bp-remove" title="Zeile entfernen">
            ✕
          </button>
        </td>
      </tr>
    `;
  }

  function addRow() {
    const tbody = document.getElementById('bp-rows');
    if (!tbody) return;
    const rowId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random());
    tbody.insertAdjacentHTML('beforeend', rowHtml(rowId));
    
    const newRow = tbody.querySelector(`tr[data-row-id="${rowId}"]`);
    if (!newRow) return;
    const locationSearch = newRow.querySelector('.bp-location-search');
    const locationId = newRow.querySelector('.bp-location-id');
    if (locationSearch && locationId) {
      setupLocationInput(locationSearch, locationId);
    }
  }

  function reset() {
    clearAlert();
    const tbody = document.getElementById('bp-rows');
    if (tbody) tbody.innerHTML = '';
    const resultEl = document.getElementById('bp-result');
    if (resultEl) resultEl.textContent = 'Noch keine Aktion ausgeführt.';
    const partsContainer = document.getElementById('bp-created-parts');
    if (partsContainer) partsContainer.classList.add('d-none');
    const partsList = document.getElementById('bp-parts-list');
    if (partsList) partsList.innerHTML = '';
    createdParts = [];
    addRow();
  }

  function collectItems() {
    const rows = Array.from(document.querySelectorAll('#bp-rows tr'));
    return rows.map(r => {
      const categoryEl = r.querySelector('.bp-category');
      const locationIdEl = r.querySelector('.bp-location-id');
      
      return {
        category_id: categoryEl ? (categoryEl.value ? Number(categoryEl.value) : null) : null,
        name: r.querySelector('.bp-name')?.value || '',
        description: r.querySelector('.bp-description')?.value || '',
        ipn: r.querySelector('.bp-ipn')?.value || '',
        quantity: r.querySelector('.bp-quantity')?.value || 0,
        location_id: locationIdEl && locationIdEl.value ? Number(locationIdEl.value) : null
      };
    });
  }

  function renderCreatedParts() {
    const container = document.getElementById('bp-parts-list');
    const partsContainer = document.getElementById('bp-created-parts');
    
    if (!container || !partsContainer) return;
    
    if (createdParts.length === 0) {
      partsContainer.classList.add('d-none');
      return;
    }

    partsContainer.classList.remove('d-none');
    container.innerHTML = '';

    createdParts.forEach(part => {
      const item = document.createElement('div');
      item.className = 'list-group-item';
      item.style.display = 'flex';
      item.style.justifyContent = 'space-between';
      item.style.alignItems = 'center';
      
      const link = document.createElement('a');
      link.href = part.url || '#';
      link.target = '_blank';
      link.textContent = part.name;
      
      const info = document.createElement('span');
      info.className = 'text-muted small';
      let infoText = `ID: ${part.id}`;
      if (part.ipn) {
        infoText += ` | IPN: ${part.ipn}`;
      }
      info.textContent = infoText;

      item.appendChild(link);
      item.appendChild(info);
      container.appendChild(item);
    });
  }

  async function submit() {
    clearAlert();
    const items = collectItems();

    if (!items.length) {
      setAlert('danger', 'Keine Zeilen vorhanden.');
      return;
    }

    setAlert('info', 'Erstelle Produkte…');

    const csrf = getCookie('csrftoken');

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrf ? { 'X-CSRFToken': csrf } : {})
        },
        body: JSON.stringify({ items })
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.error === 'creation_disabled') {
          setAlert('danger', 'Fehler: Das Plugin ist nicht zum Erstellen aktiviert. Bitte aktivieren Sie die Einstellung "ALLOW_CREATE" in den Plugin-Einstellungen (Settings → Plugin Settings → Bulk Products).');
        } else {
          setAlert('danger', data.detail || data.error || `Fehler (${res.status})`);
        }
        return;
      }

      const results = data.results || [];
      const ok = results.filter(r => r.success).length;
      const fail = results.filter(r => !r.success).length;

      if (fail === 0) setAlert('success', `Erfolgreich erstellt: ${ok}`);
      else setAlert('danger', `Erstellt: ${ok}, Fehler: ${fail} (Details unten)`);

      createdParts = results.filter(r => r.success && r.part).map(r => r.part);

      const out = [];
      out.push(`<div class="mb-2"><strong>Erstellt:</strong> ${ok} &nbsp;&nbsp; <strong>Fehler:</strong> ${fail}</div>`);
      if (fail > 0) {
        out.push('<ul class="mb-0">');
        for (const r of results) {
          if (!r.success) {
            out.push(`<li class="text-danger">FEHLER: Zeile ${Number(r.index) + 1}: ${r.error}${r.detail ? ` (${r.detail})` : ''}</li>`);
          }
        }
        out.push('</ul>');
      }

      const resultEl = document.getElementById('bp-result');
      if (resultEl) resultEl.innerHTML = out.join('');
      
      renderCreatedParts();
    } catch (e) {
      setAlert('danger', 'Fehler beim Erstellen: ' + (e.message || 'Unbekannter Fehler'));
    }
  }

  function bindEvents() {
    const addRowBtn = document.getElementById('bp-add-row');
    if (addRowBtn) {
      addRowBtn.addEventListener('click', addRow);
    }

    const resetBtn = document.getElementById('bp-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', reset);
    }

    const submitBtn = document.getElementById('bp-submit');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => submit().catch(e => {
        setAlert('danger', e?.message || 'Unbekannter Fehler');
      }));
    }

    const tbody = document.getElementById('bp-rows');
    if (tbody) {
      tbody.addEventListener('click', (e) => {
        if (e.target.closest('.bp-remove')) {
          e.preventDefault();
          e.stopPropagation();
          const row = e.target.closest('tr');
          if (row) {
            row.remove();
          }
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      bindEvents();
      reset();
    });
  } else {
    bindEvents();
    reset();
  }
})();

