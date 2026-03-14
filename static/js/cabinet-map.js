(function () {
  const mapEl = document.getElementById('mapPicker');
  const latInput = document.getElementById('lat');
  const lonInput = document.getElementById('lon');
  const btnClear = document.getElementById('btnClearMap');
  if (!mapEl || !latInput || !lonInput) return;

  var map = L.map('mapPicker', { attributionControl: false }).setView([55.75, 37.62], 4);
  map.addControl(L.control.attribution({ prefix: '' }).addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'));
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  var marker = null;

  function updateMarker(lat, lon) {
    if (marker) map.removeLayer(marker);
    if (lat != null && lon != null && !isNaN(lat) && !isNaN(lon)) {
      marker = L.marker([lat, lon]).addTo(map);
      map.setView([lat, lon], 10);
    }
  }

  function setPosition(lat, lon) {
    latInput.value = lat != null ? String(lat) : '';
    lonInput.value = lon != null ? String(lon) : '';
    updateMarker(lat, lon);
  }

  map.on('click', function (e) {
    setPosition(e.latlng.lat, e.latlng.lng);
  });

  if (btnClear) {
    btnClear.addEventListener('click', function () {
      setPosition(null, null);
    });
  }

  function tryShowInitialMarker() {
    var lat = latInput.value ? parseFloat(latInput.value) : null;
    var lon = lonInput.value ? parseFloat(lonInput.value) : null;
    if (lat != null && lon != null && !isNaN(lat) && !isNaN(lon)) {
      updateMarker(lat, lon);
    }
  }
  tryShowInitialMarker();
  setTimeout(tryShowInitialMarker, 600);
})();
