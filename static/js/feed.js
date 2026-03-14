(function () {
  const cardStack = document.getElementById('cardStack');
  const emptyFeed = document.getElementById('emptyFeed');
  const btnSkip = document.getElementById('btnSkip');
  const btnLike = document.getElementById('btnLike');
  const btnSuperLike = document.getElementById('btnSuperLike');
  const btnApplyFilters = document.getElementById('btnApplyFilters');
  const btnReload = document.getElementById('btnReload');
  const feedBalanceValue = document.getElementById('feedBalanceValue');

  let profiles = [];
  let currentIndex = 0;
  let startX = 0;
  let balance = 100;

  function updateBalanceDisplay() {
    if (feedBalanceValue) feedBalanceValue.textContent = balance;
    if (btnSuperLike) {
      btnSuperLike.disabled = balance < 3;
      btnSuperLike.title = balance < 3 ? 'Недостаточно баланса (нужно 3)' : 'Суперлайк (3 с баланса)';
    }
  }

  function fetchBalance() {
    fetch('/api/me', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        balance = data.balance != null ? data.balance : 100;
        updateBalanceDisplay();
      })
      .catch(function () { updateBalanceDisplay(); });
  }

  function getFilterGender() {
    const male = document.getElementById('filterGenderMale')?.checked;
    const female = document.getElementById('filterGenderFemale')?.checked;
    const other = document.getElementById('filterGenderOther')?.checked;
    if (male && !female && !other) return 'male';
    if (female && !male && !other) return 'female';
    if (other && !male && !female) return 'other';
    return '';
  }

  function ageMaxSliderToAge(sliderPos) {
    if (sliderPos <= 0) return 18;
    return Math.round(18 * Math.pow(1000 / 18, sliderPos / 100));
  }
  function ageMaxAgeToSlider(age) {
    if (age <= 18) return 0;
    return Math.round(100 * Math.log(age / 18) / Math.log(1000 / 18));
  }

  function getQuery() {
    const params = new URLSearchParams();
    params.set('limit', '20');
    const ageMin = document.getElementById('ageMin')?.value;
    const ageMaxEl = document.getElementById('ageMax');
    const ageMax = ageMaxEl ? ageMaxSliderToAge(parseInt(ageMaxEl.value, 10) || 0) : null;
    if (ageMin) params.set('age_min', ageMin);
    if (ageMax != null) params.set('age_max', ageMax);
    const gender = getFilterGender();
    if (gender) params.set('gender', gender);
    const interests = document.getElementById('filterInterests')?.value?.trim();
    if (interests) params.set('interests', interests);
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
    var ageMaxEl = document.getElementById('ageMax');
    var ageMax = ageMaxEl ? ageMaxSliderToAge(parseInt(ageMaxEl.value, 10) || 0) : null;
    if (ageMin) p.set('age_min', ageMin);
    if (ageMax != null) p.set('age_max', ageMax);
    var gender = getFilterGender();
    if (gender) p.set('gender', gender);
    var interests = document.getElementById('filterInterests')?.value?.trim();
    if (interests) p.set('interests', interests);
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

  function defaultAvatarUrl(gender) {
    var g = (gender === 'male' || gender === 'female') ? gender : 'other';
    return '/static/images/avatar-default-' + g + '.svg';
  }

  function renderCard(profile, index) {
    const card = document.createElement('div');
    card.className = 'profile-card';
    card.dataset.userId = profile.user_id;
    card.dataset.index = index;
    const age = profile.age != null ? profile.age + ' лет' : '';
    const meta = [age, profile.city].filter(Boolean).join(' · ');
    const photo = profile.avatar_url
      ? '<img src="' + escapeHtml(profile.avatar_url) + '" alt="">'
      : '<img src="' + escapeHtml(defaultAvatarUrl(profile.gender)) + '" alt="" class="default-avatar">';
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

  function sendReaction(isLike, isSuper) {
    const profile = profiles[currentIndex];
    if (!profile) return Promise.resolve();
    return fetch('/api/like', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify({ to_user_id: profile.user_id, is_like: isLike, is_super: !!isSuper })
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) return Promise.reject(data);
        if (data.balance != null) balance = data.balance;
        updateBalanceDisplay();
        if (data.new_match && data.match_id) showMatchOverlay(data.match_id);
        return data;
      });
    });
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function showMatchOverlay(matchId) {
    const overlay = document.getElementById('matchOverlay');
    if (!overlay) return;
    overlay.dataset.matchId = matchId;
    overlay.classList.add('is-visible');
    overlay.setAttribute('aria-hidden', 'false');
  }

  function hideMatchOverlay() {
    const overlay = document.getElementById('matchOverlay');
    if (!overlay) return;
    overlay.classList.remove('is-visible');
    overlay.setAttribute('aria-hidden', 'true');
    delete overlay.dataset.matchId;
  }

  document.getElementById('matchGoToChat')?.addEventListener('click', function () {
    const matchId = document.getElementById('matchOverlay')?.dataset?.matchId;
    if (matchId) window.location.href = '/chat/' + matchId;
  });
  document.getElementById('matchLater')?.addEventListener('click', hideMatchOverlay);
  document.querySelector('.match-overlay-backdrop')?.addEventListener('click', hideMatchOverlay);

  function swipeCard(direction) {
    const cards = cardStack.querySelectorAll('.profile-card');
    const topCard = cards[0];
    if (!topCard || !profiles[currentIndex]) return;
    const profile = profiles[currentIndex];
    const isLike = direction === 'right' || direction === 'super';
    const isSuper = direction === 'super';
    topCard.classList.add(direction === 'left' ? 'swipe-left' : 'swipe-right');
    sendReaction(isLike, isSuper).then(function () {
      currentIndex++;
      setTimeout(function () {
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
    }).catch(function (err) {
      topCard.classList.remove('swipe-left', 'swipe-right');
      if (err && err.error) alert(err.error);
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
    function getAgeMaxReal() {
      return ageMaxSliderToAge(parseInt(ageMaxEl.value, 10) || 0);
    }
    function onAgeMinInput() {
      var min = parseInt(ageMinEl.value, 10);
      var maxReal = getAgeMaxReal();
      if (min > maxReal) {
        ageMaxEl.value = String(ageMaxAgeToSlider(min));
        if (ageMaxVal) ageMaxVal.textContent = min;
      }
      if (ageMinVal) ageMinVal.textContent = ageMinEl.value;
    }
    function onAgeMaxInput() {
      var min = parseInt(ageMinEl.value, 10);
      var maxReal = getAgeMaxReal();
      if (maxReal < min) {
        ageMinEl.value = String(maxReal);
        if (ageMinVal) ageMinVal.textContent = maxReal;
      }
      if (ageMaxVal) ageMaxVal.textContent = maxReal;
    }
    if (ageMinEl) { ageMinEl.addEventListener('input', onAgeMinInput); ageMinVal.textContent = ageMinEl.value; }
    if (ageMaxEl) {
      ageMaxEl.addEventListener('input', onAgeMaxInput);
      if (ageMaxVal) ageMaxVal.textContent = getAgeMaxReal();
    }
  })();

  ['filterGenderMale', 'filterGenderFemale', 'filterGenderOther'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('change', updateMapCount);
  });

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

  btnSkip.addEventListener('click', function () { swipeCard('left'); });
  btnLike.addEventListener('click', function () { swipeCard('right'); });
  if (btnSuperLike) btnSuperLike.addEventListener('click', function () { swipeCard('super'); });
  btnApplyFilters.addEventListener('click', load);
  btnReload.addEventListener('click', load);
  fetchBalance();

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
    L.Icon.Default.imagePath = 'https://unpkg.com/leaflet@1.9.4/dist/images/';

    function initFeedMap() {
      if (window._feedMapAlreadyInited) return;
      window._feedMapAlreadyInited = true;
      window._feedMapInitCount = (window._feedMapInitCount || 0) + 1;
      if (feedMapEl._leaflet_id != null) {
        feedMapEl.innerHTML = '';
        delete feedMapEl._leaflet_id;
      }
      var feedMap = L.map('feedMap', { attributionControl: false }).setView([55.75, 37.62], 4);
      feedMap.addControl(L.control.attribution({ prefix: '' }).addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'));
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(feedMap);
      var center = feedMap.getCenter();
      var rect = feedMapEl.getBoundingClientRect();
      var mapSize = feedMap.getSize();
      console.log('[feed map] init #' + window._feedMapInitCount + ' at ' + new Date().toISOString() + ' center=' + center.lat + ',' + center.lng + ' zoom=' + feedMap.getZoom() + ' container=' + feedMapEl.offsetWidth + 'x' + feedMapEl.offsetHeight + ' mapSize=' + (mapSize ? mapSize.x + 'x' + mapSize.y : '—') + ' rect=' + Math.round(rect.width) + 'x' + Math.round(rect.height));
      setTimeout(function () {
        feedMap.invalidateSize();
        feedMap.setView(feedMap.getCenter(), feedMap.getZoom());
        var size2 = feedMap.getSize();
        console.log('[feed map] after invalidateSize mapSize=' + (size2 ? size2.x + 'x' + size2.y : '—'));
      }, 100);
      setTimeout(function () {
        feedMap.invalidateSize();
        feedMap.setView(feedMap.getCenter(), feedMap.getZoom());
      }, 350);
      window.addEventListener('resize', function () {
        feedMap.invalidateSize();
        feedMap.setView(feedMap.getCenter(), feedMap.getZoom());
      });
      var feedMapCircle = null;
    var feedMapMarker = null;
    var feedMapRadiusHandle = null;
    var profileMarkersLayer = L.layerGroup().addTo(feedMap);
    var KM_PER_DEG_LAT = 111.32;

    window.updateFeedMapProfiles = function (profilesList) {
      profileMarkersLayer.clearLayers();
      if (!profilesList || !profilesList.length) return;
      profilesList.forEach(function (p) {
        var lat = p.lat != null ? parseFloat(p.lat) : null;
        var lon = p.lon != null ? parseFloat(p.lon) : null;
        if (lat == null || lon == null) return;
        var isMale = p.gender === 'male';
        var isOther = p.gender === 'other';
        var symbol = isMale ? '\u2642' : (isOther ? '\u26A2' : '\u2640');
        var iconClass = isMale ? 'map-profile-male' : (isOther ? 'map-profile-other' : 'map-profile-female');
        var icon = L.divIcon({
          className: 'map-profile-icon ' + iconClass,
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
      var sel = document.getElementById('mapRadius');
      document.getElementById('mapRadiusKm').value = km;
      var opts = [25, 50, 100, 200, 500, 2000];
      var best = opts[0];
      opts.forEach(function (o) { if (Math.abs(o - km) < Math.abs(best - km)) best = o; });
      if (sel) sel.value = String(best);
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
      if (feedMapRadiusHandle) feedMap.removeLayer(feedMapRadiusHandle);
      feedMapRadiusHandle = null;
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
        var handleLat = centerLat + (radiusKm / KM_PER_DEG_LAT);
        var radiusHandleIcon = L.divIcon({
          className: 'feed-map-radius-handle',
          html: '<span></span>',
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });
        feedMapRadiusHandle = L.marker([handleLat, centerLon], { draggable: true, icon: radiusHandleIcon }).addTo(feedMap);
        feedMapRadiusHandle.on('dragend', function () {
          var handlePos = feedMapRadiusHandle.getLatLng();
          var center = L.latLng(centerLat, centerLon);
          var distM = center.distanceTo(handlePos);
          var newKm = Math.round(distM / 1000);
          newKm = Math.max(5, Math.min(2000, newKm));
          var presets = [25, 50, 100, 200, 500, 2000];
          newKm = presets.reduce(function (best, o) { return Math.abs(o - newKm) < Math.abs(best - newKm) ? o : best; });
          setRadiusKm(newKm);
          updateMapCount();
          if (document.getElementById('feedMapCenterLat').value && document.getElementById('feedMapCenterLon').value) load();
        });
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
    }

    var feedMapInited = false;
    var feedMapTimeoutId = null;
    function waitForSize() {
      if (feedMapInited) return;
      if (feedMapEl.offsetWidth > 0 && feedMapEl.offsetHeight > 0) {
        feedMapInited = true;
        if (feedMapTimeoutId != null) clearTimeout(feedMapTimeoutId);
        initFeedMap();
        return;
      }
      requestAnimationFrame(waitForSize);
    }
    requestAnimationFrame(waitForSize);
    feedMapTimeoutId = setTimeout(function () {
      feedMapTimeoutId = null;
      if (!feedMapInited) {
        feedMapInited = true;
        initFeedMap();
      }
    }, 2000);
  } else {
    load();
  }
})();
