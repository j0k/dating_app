(function () {
  const bulletinList = document.getElementById('bulletinList');
  const bulletinForm = document.getElementById('bulletinForm');
  const mapEl = document.getElementById('map');

  function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function loadAnnouncements() {
    fetch('/api/announcements?limit=30', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        const list = data.announcements || [];
        if (list.length === 0) {
          bulletinList.innerHTML = '<p style="color: var(--text-muted);">Пока нет объявлений.</p>';
          return;
        }
        bulletinList.innerHTML = list.map(a => {
          const date = a.created_at ? new Date(a.created_at).toLocaleDateString('ru-RU', {
            day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
          }) : '';
          return '<div class="bulletin-item">' +
            '<div class="bulletin-title">' + escapeHtml(a.title) + '</div>' +
            '<div class="bulletin-meta">' + escapeHtml(a.author_name) + (date ? ' · ' + date : '') + '</div>' +
            (a.body ? '<div class="bulletin-body">' + escapeHtml(a.body) + '</div>' : '') +
            '</div>';
        }).join('');
      })
      .catch(() => {
        bulletinList.innerHTML = '<p style="color: var(--text-muted);">Не удалось загрузить объявления.</p>';
      });
  }

  if (bulletinForm) {
    bulletinForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const title = document.getElementById('annTitle').value.trim();
      const body = document.getElementById('annBody').value.trim();
      const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      fetch('/api/announcements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
        credentials: 'same-origin',
        body: JSON.stringify({ title: title, body: body })
      })
        .then(r => r.json())
        .then(data => {
          if (data.error) {
            alert(data.error);
            return;
          }
          document.getElementById('annTitle').value = '';
          document.getElementById('annBody').value = '';
          loadAnnouncements();
        })
        .catch(() => alert('Ошибка отправки'));
    });
  }

  loadAnnouncements();

  if (mapEl) {
    var map = L.map('map', { attributionControl: false }).setView([55.75, 37.62], 3);
    map.addControl(L.control.attribution({ prefix: '' }).addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'));
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    var markers = L.markerClusterGroup({ chunkedLoading: true });
    map.addLayer(markers);
    fetch('/api/map-users', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        var users = data.users || [];
        if (users.length === 0) return;
        var bounds = [];
        users.forEach(function (u) {
          var m = L.marker([u.lat, u.lon]);
          var popup = '<strong>' + escapeHtml(u.name) + '</strong>';
          if (u.city) popup += '<br>' + escapeHtml(u.city);
          m.bindPopup(popup);
          markers.addLayer(m);
          bounds.push([u.lat, u.lon]);
        });
        if (bounds.length > 1) map.fitBounds(bounds, { padding: [20, 20] });
        else if (bounds.length === 1) map.setView(bounds[0], 10);
      })
      .catch(function () {});
  }
})();
