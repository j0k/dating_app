(function () {
  const cardStack = document.getElementById('cardStack');
  const emptyFeed = document.getElementById('emptyFeed');
  const btnSkip = document.getElementById('btnSkip');
  const btnLike = document.getElementById('btnLike');
  const btnApplyFilters = document.getElementById('btnApplyFilters');
  const btnReload = document.getElementById('btnReload');

  let profiles = [];
  let currentIndex = 0;
  let startX = 0;

  function getQuery() {
    const params = new URLSearchParams();
    params.set('limit', '20');
    const ageMin = document.getElementById('ageMin')?.value;
    const ageMax = document.getElementById('ageMax')?.value;
    if (ageMin) params.set('age_min', ageMin);
    if (ageMax) params.set('age_max', ageMax);
    const gender = document.getElementById('filterGender')?.value;
    if (gender) params.set('gender', gender);
    if (document.getElementById('onlyReal')?.checked) params.set('only_real', '1');
    const mapLat = document.getElementById('feedMapCenterLat')?.value;
    const mapLon = document.getElementById('feedMapCenterLon')?.value;
    const mapRadiusKm = document.getElementById('mapRadiusKm')?.value;
    const mapRadius = mapRadiusKm || document.getElementById('mapRadius')?.value;
    if (mapLat && mapLon && mapRadius) {
      params.set('map_lat', mapLat);
      params.set('map_lon', mapLon);
      params.set('map_radius_km', mapRadius);
    }
    return params.toString();
  }

  function getCountQuery() {
    var p = new URLSearchParams();
    var ageMin = document.getElementById('ageMin')?.value;
    var ageMax = document.getElementById('ageMax')?.value;
    if (ageMin) p.set('age_min', ageMin);
    if (ageMax) p.set('age_max', ageMax);
    var gender = document.getElementById('filterGender')?.value;
    if (gender) p.set('gender', gender);
    if (document.getElementById('onlyReal')?.checked) p.set('only_real', '1');
    var mapLat = document.getElementById('feedMapCenterLat')?.value;
    var mapLon = document.getElementById('feedMapCenterLon')?.value;
    var mapRadius = document.getElementById('mapRadiusKm')?.value || document.getElementById('mapRadius')?.value;
    if (mapLat && mapLon && mapRadius) p.set('map_lat', mapLat), p.set('map_lon', mapLon), p.set('map_radius_km', mapRadius);
    return p.toString();
  }

  var countTimeout = null;
  function updateMapCount() {
    var wrap = document.getElementById('feedMapCountWrap');
    var el = document.getElementById('feedMapCount');
    if (!el) return;
    var mapLat = document.getElementById('feedMapCenterLat')?.value;
    var mapLon = document.getElementById('feedMapCenterLon')?.value;
    var mapRadius = document.getElementById('mapRadiusKm')?.value || document.getElementById('mapRadius')?.value;
    if (!mapLat || !mapLon || !mapRadius) {
      el.textContent = '—';
      return;
    }
    el.textContent = '…';
    if (countTimeout) clearTimeout(countTimeout);
    countTimeout = setTimeout(function () {
      fetch('/api/recommendations/count?' + getCountQuery(), { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.count != null) el.textContent = data.count;
          else el.textContent = '—';
        })
        .catch(function () { el.textContent = '—'; });
      countTimeout = null;
    }, 300);
  }

  function fetchRecommendations() {
    return fetch('/api/recommendations?' + getQuery(), { credentials: 'same-origin' })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('Failed to load')))
      .then(data => data.profiles || []);
  }

  var goalLabels = { serious: 'Серьёзные', dating: 'Знакомства', friendship: 'Дружба', open: 'Открытые', unsure: 'Пока не знаю' };
  var typeLabels = { monogamous: 'Моногамия', polyamorous: 'Полиамория', any: 'Любые' };

  function renderCard(profile, index) {
    const card = document.createElement('div');
    card.className = 'profile-card';
    card.dataset.userId = profile.user_id;
    card.dataset.index = index;
    const age = profile.age != null ? profile.age + ' лет' : '';
    const meta = [age, profile.city].filter(Boolean).join(' · ');
    const photo = profile.avatar_url
      ? '<img src="' + escapeHtml(profile.avatar_url) + '" alt="">'
      : '<span>👤</span>';
    const tags = (profile.interests || []).slice(0, 5).map(i => '<span class="tag">' + escapeHtml(i) + '</span>').join('');
    var goalType = [];
    if (profile.relationship_goal && goalLabels[profile.relationship_goal]) goalType.push(goalLabels[profile.relationship_goal]);
    if (profile.relationship_type && typeLabels[profile.relationship_type]) goalType.push(typeLabels[profile.relationship_type]);
    const goalTypeHtml = goalType.length ? '<p class="card-meta card-goal">' + escapeHtml(goalType.join(' · ')) + '</p>' : '';
    card.innerHTML =
      '<div class="card-photo">' + photo + ((profile.match_score != null && profile.match_score > 0) ? '<span class="card-match-badge">' + escapeHtml(String(profile.match_score)) + '%</span>' : '') + '</div>' +
      '<div class="card-body">' +
      '<h2 class="card-name">' + escapeHtml(profile.name) + '</h2>' +
      (meta ? '<p class="card-meta">' + escapeHtml(meta) + '</p>' : '') +
      goalTypeHtml +
      (profile.about ? '<p class="card-about">' + escapeHtml(profile.about) + '</p>' : '') +
      (tags ? '<div class="card-interests">' + tags + '</div>' : '') +
      '</div>';
    return card;
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function showCards() {
    cardStack.innerHTML = '';
    if (profiles.length === 0) {
      cardStack.style.display = 'none';
      emptyFeed.style.display = 'block';
      return;
    }
    cardStack.style.display = 'block';
    emptyFeed.style.display = 'none';
    const top = Math.min(currentIndex + 2, profiles.length);
    for (let i = currentIndex; i < top; i++) {
      const profile = profiles[i];
      const card = renderCard(profile, i);
      card.style.zIndex = profiles.length - i;
      cardStack.appendChild(card);
    }
  }

  function sendReaction(isLike) {
    const profile = profiles[currentIndex];
    if (!profile) return Promise.resolve();
    return fetch('/api/like', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify({ to_user_id: profile.user_id, is_like: isLike })
    }).then(r => r.json()).then(data => {
      if (data.new_match && data.match_id) {
        if (confirm('Это матч! Перейти в чат?')) {
          window.location.href = '/chat/' + data.match_id;
        }
      }
      return data;
    });
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function swipeCard(direction) {
    const cards = cardStack.querySelectorAll('.profile-card');
    const topCard = cards[0];
    if (!topCard || !profiles[currentIndex]) return;
    const profile = profiles[currentIndex];
    topCard.classList.add(direction === 'left' ? 'swipe-left' : 'swipe-right');
    sendReaction(direction === 'right').then(() => {
      currentIndex++;
      setTimeout(() => {
        topCard.remove();
        if (currentIndex < profiles.length) {
          const next = profiles[currentIndex];
          const newCard = renderCard(next, currentIndex);
          newCard.style.zIndex = 0;
          cardStack.appendChild(newCard);
        } else {
          showCards();
        }
      }, 300);
    }).catch(() => {
      topCard.classList.remove('swipe-left', 'swipe-right');
    });
  }

  function load() {
    currentIndex = 0;
    fetchRecommendations().then(p => {
      profiles = p;
      showCards();
      if (window.updateFeedMapProfiles) window.updateFeedMapProfiles(p);
      updateMapCount();
    }).catch(() => {
      profiles = [];
      showCards();
      if (window.updateFeedMapProfiles) window.updateFeedMapProfiles([]);
      updateMapCount();
    });
  }

  (function initAgeSliders() {
    var ageMinEl = document.getElementById('ageMin');
    var ageMaxEl = document.getElementById('ageMax');
    var ageMinVal = document.getElementById('ageMinValue');
    var ageMaxVal = document.getElementById('ageMaxValue');
    function updateAgeLabels() {
      if (ageMinVal) ageMinVal.textContent = ageMinEl.value;
      if (ageMaxVal) ageMaxVal.textContent = ageMaxEl.value;
    }
    function onAgeMinInput() {
      var min = parseInt(ageMinEl.value, 10);
      var max = parseInt(ageMaxEl.value, 10);
      if (min > max) { ageMaxEl.value = min; ageMaxVal.textContent = min; }
      ageMinVal.textContent = ageMinEl.value;
    }
    function onAgeMaxInput() {
      var min = parseInt(ageMinEl.value, 10);
      var max = parseInt(ageMaxEl.value, 10);
      if (max < min) { ageMinEl.value = max; ageMinVal.textContent = max; }
      ageMaxVal.textContent = ageMaxEl.value;
    }
    if (ageMinEl) { ageMinEl.addEventListener('input', onAgeMinInput); ageMinVal.textContent = ageMinEl.value; }
    if (ageMaxEl) { ageMaxEl.addEventListener('input', onAgeMaxInput); ageMaxVal.textContent = ageMaxEl.value; }
  })();

  var filterGender = document.getElementById('filterGender');
  if (filterGender) filterGender.addEventListener('change', updateMapCount);

  var btnSearchMain = document.getElementById('btnSearchMain');
  if (btnSearchMain) {
    btnSearchMain.addEventListener('click', function () {
      var lat = document.getElementById('feedMapCenterLat').value;
      var lon = document.getElementById('feedMapCenterLon').value;
      if (!lat || !lon) {
        alert('Сначала укажите себя на карте: кликните по карте или нажмите «Я здесь».');
        return;
      }
      load();
    });
  }

  btnSkip.addEventListener('click', () => swipeCard('left'));
  btnLike.addEventListener('click', () => swipeCard('right'));
  btnApplyFilters.addEventListener('click', load);
  btnReload.addEventListener('click', load);

  cardStack.addEventListener('mousedown', e => { startX = e.clientX; });
  cardStack.addEventListener('mouseup', e => {
    const dx = e.clientX - startX;
    if (Math.abs(dx) > 80) swipeCard(dx < 0 ? 'left' : 'right');
  });
  cardStack.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  cardStack.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 80) swipeCard(dx < 0 ? 'left' : 'right');
  }, { passive: true });

  var feedMapEl = document.getElementById('feedMap');
  if (feedMapEl && typeof L !== 'undefined') {
    var feedMap = L.map('feedMap', { attributionControl: false }).setView([55.75, 37.62], 4);
    feedMap.addControl(L.control.attribution({ prefix: '' }).addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'));
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(feedMap);
    var feedMapCircle = null;
    var feedMapMarker = null;
    var profileMarkersLayer = L.layerGroup().addTo(feedMap);

    window.updateFeedMapProfiles = function (profilesList) {
      profileMarkersLayer.clearLayers();
      if (!profilesList || !profilesList.length) return;
      profilesList.forEach(function (p) {
        var lat = p.lat != null ? parseFloat(p.lat) : null;
        var lon = p.lon != null ? parseFloat(p.lon) : null;
        if (lat == null || lon == null) return;
        var isMale = p.gender === 'male';
        var symbol = isMale ? '\u2642' : '\u2640';
        var icon = L.divIcon({
          className: 'map-profile-icon ' + (isMale ? 'map-profile-male' : 'map-profile-female'),
          html: '<span>' + symbol + '</span>',
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });
        var marker = L.marker([lat, lon], { icon: icon }).addTo(profileMarkersLayer);
        var name = p.name || 'Профиль';
        var age = p.age != null ? p.age + ' лет' : '';
        marker.bindPopup('<strong>' + (name.replace(/</g, '&lt;').replace(/>/g, '&gt;')) + '</strong>' + (age ? '<br>' + age : ''));
      });
    };

    function getRadiusKm() {
      var km = document.getElementById('mapRadiusKm').value;
      if (km) return parseFloat(km, 10);
      var sel = document.getElementById('mapRadius').value;
      return sel ? parseFloat(sel, 10) : 0;
    }

    function setMapCenter(lat, lon) {
      document.getElementById('feedMapCenterLat').value = lat;
      document.getElementById('feedMapCenterLon').value = lon;
      if (feedMapMarker) feedMap.removeLayer(feedMapMarker);
      feedMapMarker = L.marker([lat, lon], { draggable: true }).addTo(feedMap);
      feedMapMarker.on('dragend', function () {
        var pos = feedMapMarker.getLatLng();
        document.getElementById('feedMapCenterLat').value = pos.lat;
        document.getElementById('feedMapCenterLon').value = pos.lng;
        updateFeedMapCircle();
      });
      updateFeedMapCircle();
    }
    function setRadiusKm(km) {
      document.getElementById('mapRadiusKm').value = km;
      document.getElementById('mapRadius').value = km;
      updateFeedMapCircle();
    }
    window._feedMapSetCenter = setMapCenter;
    window._feedMapSetRadius = setRadiusKm;
    window._feedMapSetView = function (lat, lon, zoom) { feedMap.setView([lat, lon], zoom || 11); };

    function updateFeedMapCircle() {
      var lat = document.getElementById('feedMapCenterLat').value;
      var lon = document.getElementById('feedMapCenterLon').value;
      var radiusKm = getRadiusKm();
      if (feedMapCircle) feedMap.removeLayer(feedMapCircle);
      if (lat && lon && radiusKm > 0) {
        var centerLat = parseFloat(lat);
        var centerLon = parseFloat(lon);
        var radiusM = radiusKm * 1000;
        feedMapCircle = L.circle([centerLat, centerLon], {
          radius: radiusM,
          color: '#e8b923',
          weight: 2,
          fillOpacity: 0.15
        }).addTo(feedMap);
      }
      updateMapCount();
    }

    feedMap.on('click', function (e) {
      setMapCenter(e.latlng.lat, e.latlng.lng);
      load();
    });

    document.getElementById('btnMyLocation').addEventListener('click', function () {
      var btn = this;
      if (!navigator.geolocation) {
        alert('Геолокация не поддерживается браузером.');
        return;
      }
      btn.disabled = true;
      btn.textContent = 'Определяю…';
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          var lat = pos.coords.latitude;
          var lon = pos.coords.longitude;
          setMapCenter(lat, lon);
          feedMap.setView([lat, lon], 12);
          load();
          btn.disabled = false;
          btn.textContent = 'Я здесь';
        },
        function () {
          alert('Не удалось определить местоположение. Разрешите доступ к геолокации или укажите точку на карте вручную.');
          btn.disabled = false;
          btn.textContent = 'Я здесь';
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });

    document.getElementById('mapRadius').addEventListener('change', function () {
      var v = this.value;
      var kmEl = document.getElementById('mapRadiusKm');
      if (kmEl) kmEl.value = v;
      updateFeedMapCircle();
      updateMapCount();
      if (document.getElementById('feedMapCenterLat').value && document.getElementById('feedMapCenterLon').value) load();
    });

    fetch('/api/me/profile', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (me) {
        if (me && me.lat != null && me.lon != null) {
          setMapCenter(parseFloat(me.lat), parseFloat(me.lon));
          feedMap.setView([parseFloat(me.lat), parseFloat(me.lon)], 10);
        }
        load();
      })
      .catch(function () { load(); });
  } else {
    load();
  }
})();
