(function () {
  const mapEl = document.getElementById('map');
  if (!mapEl) return;

  function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  var map = L.map('map', { attributionControl: false }).setView([55.75, 37.62], 3);
  map.addControl(L.control.attribution({ prefix: '' }).addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'));
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  var markers = L.markerClusterGroup({ chunkedLoading: true });
  map.addLayer(markers);

  fetch('/api/map-users', { credentials: 'same-origin' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var users = data.users || [];
      if (users.length === 0) return;
      var bounds = [];
      users.forEach(function (u) {
        var m = L.marker([u.lat, u.lon]);
        var popup = '<strong>' + escapeHtml(u.name) + '</strong>';
        var parts = [];
        if (u.age != null) parts.push(escapeHtml(u.age) + ' лет');
        if (u.gender_display) parts.push(escapeHtml(u.gender_display));
        if (parts.length) popup += '<br>' + parts.join(' · ');
        if (u.city) popup += '<br>' + escapeHtml(u.city);
        m.bindPopup(popup);
        markers.addLayer(m);
        bounds.push([u.lat, u.lon]);
      });
      if (bounds.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
      else if (bounds.length === 1) map.setView(bounds[0], 10);
    })
    .catch(function () {});
})();
