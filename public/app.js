/**
 * Smart Entertainment Recommender - Application Client Script
 * Controls Page Routing, Canvas Animations, API Integration, Carousel, and Modal Popups
 * Supports dual-mode execution: Live API backend & Static GitHub Pages fallback.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const landingPage = document.getElementById('landing-page');
  const dashboardPage = document.getElementById('dashboard-page');
  const btnGetStarted = document.getElementById('btn-get-started');
  const btnHeroSearch = document.getElementById('btn-hero-search');
  const btnHomeNav = document.getElementById('btn-home-nav');
  const btnBackLanding = document.getElementById('btn-back-landing');

  const trendsCarousel = document.getElementById('trends-carousel');
  const btnPrevCarousel = document.getElementById('carousel-prev');

  const selectTitleSearch = document.getElementById('select-title-search');
  const selectSource = document.getElementById('select-source');
  const selectGenre = document.getElementById('select-genre');
  const selectRating = document.getElementById('select-rating');
  const selectLanguage = document.getElementById('select-language');
  const inputTopN = document.getElementById('input-top-n');
  const btnRunRec = document.getElementById('btn-run-recommendation');
  const platformTabs = document.querySelectorAll('.platform-tab');
  const cardsGrid = document.getElementById('recommendation-cards-grid');
  const queryHeading = document.getElementById('query-movie-heading');

  const modal = document.getElementById('movie-detail-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');

  let allTitlesList = [];
  let catalogData = [];
  let currentSourceFilter = 'all';

  const DEFAULT_POSTER = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500&auto=format&fit=crop&q=60';
  const API_BASE = '/api';

  function getValidPosterUrl(url) {
    if (!url || typeof url !== 'string') return DEFAULT_POSTER;
    const trimmed = url.trim();
    if (trimmed.toLowerCase().startsWith('http://') || trimmed.toLowerCase().startsWith('https://')) {
      return trimmed;
    }
    return DEFAULT_POSTER;
  }

  // --------------------------------------------------------------------------
  // PAGE NAVIGATION ROUTER
  // --------------------------------------------------------------------------
  function navigateTo(pageId) {
    if (pageId === 'dashboard') {
      landingPage.classList.remove('active');
      dashboardPage.classList.add('active');
      window.scrollTo(0, 0);
      loadDashboardData();
    } else {
      dashboardPage.classList.remove('active');
      landingPage.classList.add('active');
      window.scrollTo(0, 0);
    }
  }

  btnGetStarted.addEventListener('click', () => navigateTo('dashboard'));
  btnHeroSearch.addEventListener('click', () => navigateTo('dashboard'));
  btnHomeNav.addEventListener('click', (e) => {
    e.preventDefault();
    navigateTo('landing');
  });
  btnBackLanding.addEventListener('click', (e) => {
    e.preventDefault();
    navigateTo('landing');
  });

  if (window.location.hash === '#dashboard') {
    navigateTo('dashboard');
  }

  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href').replace('#', '');
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // --------------------------------------------------------------------------
  // CANVAS LIGHT TRAILS ANIMATION
  // --------------------------------------------------------------------------
  function initLightTrailsCanvas() {
    const canvas = document.getElementById('light-trails-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resizeCanvas() {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
      }
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const particles = [];
    const particleCount = 40;

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 1,
        speedX: (Math.random() - 0.5) * 1.6,
        speedY: (Math.random() - 0.5) * 1.6,
        color: Math.random() > 0.5 ? 'rgba(0, 242, 254, ' : 'rgba(157, 78, 221, ',
        alpha: Math.random() * 0.6 + 0.2,
      });
    }

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const time = Date.now() * 0.0012;

      ctx.save();
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.strokeStyle = `rgba(0, 242, 254, ${0.25 + Math.sin(time) * 0.1})`;
      ctx.moveTo(centerX, centerY);
      ctx.quadraticCurveTo(centerX - 100, centerY - 60, 85, 75);
      ctx.stroke();

      ctx.beginPath();
      ctx.strokeStyle = `rgba(157, 78, 221, ${0.25 + Math.cos(time) * 0.1})`;
      ctx.moveTo(centerX, centerY);
      ctx.quadraticCurveTo(centerX + 100, centerY - 60, canvas.width - 85, 75);
      ctx.stroke();

      ctx.beginPath();
      ctx.strokeStyle = `rgba(157, 78, 221, ${0.25 + Math.sin(time * 1.3) * 0.1})`;
      ctx.moveTo(centerX, centerY);
      ctx.quadraticCurveTo(centerX - 100, centerY + 60, 85, canvas.height - 75);
      ctx.stroke();

      ctx.beginPath();
      ctx.strokeStyle = `rgba(0, 242, 254, ${0.25 + Math.cos(time * 1.3) * 0.1})`;
      ctx.moveTo(centerX, centerY);
      ctx.quadraticCurveTo(centerX + 100, centerY + 60, canvas.width - 85, canvas.height - 75);
      ctx.stroke();

      ctx.restore();

      particles.forEach(p => {
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
        if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `${p.color}${p.alpha})`;
        ctx.fill();
      });

      requestAnimationFrame(animate);
    }
    animate();
  }
  initLightTrailsCanvas();

  // --------------------------------------------------------------------------
  // CROSS-PLATFORM TRENDS CAROUSEL
  // --------------------------------------------------------------------------
  async function loadTrends() {
    try {
      const res = await fetch(`${API_BASE}/trends`);
      if (res.ok) {
        const json = await res.json();
        if (json.status === 'success' && json.data.length > 0) {
          renderTrendsCarousel(json.data);
          return;
        }
      }
      throw new Error('Fallback to static trends.json');
    } catch (err) {
      try {
        const resStatic = await fetch('data/trends.json');
        const jsonStatic = await resStatic.json();
        if (jsonStatic.data && jsonStatic.data.length > 0) {
          renderTrendsCarousel(jsonStatic.data);
        }
      } catch (e) {
        console.error('Failed to load trends:', e);
      }
    }
  }

  function renderTrendsCarousel(items) {
    trendsCarousel.innerHTML = '';
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'trend-card';
      const poster = getValidPosterUrl(item.poster_url);
      const sourceUpper = (item.source || 'NETFLIX').toUpperCase();

      card.innerHTML = `
        <img src="${poster}" alt="${item.title}" class="trend-poster" loading="lazy" onerror="this.src='${DEFAULT_POSTER}'">
        <div class="trend-overlay">
          <h3 class="trend-title">${item.title}</h3>
          <div class="trend-platforms">
            <span class="platform-badge">${sourceUpper}</span>
            <span class="platform-badge" style="background:rgba(0,242,254,0.25); color:#00F2FE;">★ ${item.rating || '8.5'}</span>
          </div>
        </div>
      `;

      card.addEventListener('click', () => {
        selectTitleSearch.value = item.title;
        selectGenre.value = 'all';
        navigateTo('dashboard');
        fetchRecommendations();
      });

      trendsCarousel.appendChild(card);
    });
  }

  btnPrevCarousel.addEventListener('click', () => {
    trendsCarousel.scrollBy({ left: -260, behavior: 'smooth' });
  });

  loadTrends();

  // --------------------------------------------------------------------------
  // DASHBOARD DATA & METADATA
  // --------------------------------------------------------------------------
  async function loadDashboardData() {
    if (allTitlesList.length === 0) {
      try {
        const res = await fetch(`${API_BASE}/meta`);
        if (res.ok) {
          const json = await res.json();
          if (json.status === 'success') {
            allTitlesList = json.titles || [];
            populateTitleDropdown(allTitlesList);
            populateGenreDropdown(json.genres || []);
            populateLanguageDropdown(json.languages || []);
          }
        } else {
          throw new Error('Use static meta fallback');
        }
      } catch (err) {
        try {
          const resMeta = await fetch('data/meta.json');
          const jsonMeta = await resMeta.json();
          allTitlesList = jsonMeta.titles || [];
          populateTitleDropdown(allTitlesList);
          populateGenreDropdown(jsonMeta.genres || []);
          populateLanguageDropdown(jsonMeta.languages || []);

          const resCat = await fetch('data/catalog.json');
          catalogData = await resCat.json();
        } catch (e) {
          console.error('Failed to load static meta:', e);
        }
      }
    }
    fetchRecommendations();
  }

  const suggestionsBox = document.getElementById('autocomplete-suggestions');
  let selectedSuggestionIndex = -1;

  function renderSuggestions(query) {
    if (!suggestionsBox) return;
    const cleanQuery = query.trim().toLowerCase();

    if (!cleanQuery) {
      suggestionsBox.classList.add('hidden');
      suggestionsBox.innerHTML = '';
      selectedSuggestionIndex = -1;
      return;
    }

    const startsWithMatches = [];
    const includesMatches = [];

    for (let i = 0; i < allTitlesList.length; i++) {
      const t = allTitlesList[i];
      const tLower = t.toLowerCase();
      if (tLower.startsWith(cleanQuery)) {
        startsWithMatches.push(t);
        if (startsWithMatches.length >= 35) break;
      } else if (tLower.includes(cleanQuery)) {
        if (startsWithMatches.length + includesMatches.length < 50) {
          includesMatches.push(t);
        }
      }
    }

    const matches = [...startsWithMatches, ...includesMatches].slice(0, 40);

    if (matches.length === 0) {
      suggestionsBox.innerHTML = `<div class="autocomplete-no-match">No movies matching "${query}"</div>`;
      suggestionsBox.classList.remove('hidden');
      selectedSuggestionIndex = -1;
      return;
    }

    suggestionsBox.innerHTML = '';
    selectedSuggestionIndex = -1;

    matches.forEach((itemTitle, idx) => {
      const div = document.createElement('div');
      div.className = 'autocomplete-item';
      div.dataset.index = idx;
      div.dataset.title = itemTitle;
      div.textContent = itemTitle;

      div.addEventListener('mousedown', (e) => {
        e.preventDefault();
        selectTitleSearch.value = itemTitle;
        selectGenre.value = 'all';
        suggestionsBox.classList.add('hidden');
        fetchRecommendations();
      });

      suggestionsBox.appendChild(div);
    });

    suggestionsBox.classList.remove('hidden');
  }

  function populateTitleDropdown(titles) {
    allTitlesList = titles || [];
    if (!selectTitleSearch.value) {
      selectTitleSearch.value = "The Godfather";
    }
  }

  function populateGenreDropdown(genres) {
    selectGenre.innerHTML = '<option value="all">All Genres</option>';
    genres.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g.charAt(0).toUpperCase() + g.slice(1);
      selectGenre.appendChild(opt);
    });
  }

  function populateLanguageDropdown(languages) {
    selectLanguage.innerHTML = '<option value="all">All Languages</option>';
    languages.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l;
      opt.textContent = l.charAt(0).toUpperCase() + l.slice(1);
      selectLanguage.appendChild(opt);
    });
  }

  // Interlocking Dropdowns
  selectGenre.addEventListener('change', () => {
    if (selectGenre.value !== 'all') {
      selectTitleSearch.value = '';
      if (suggestionsBox) suggestionsBox.classList.add('hidden');
    }
    fetchRecommendations();
  });

  selectTitleSearch.addEventListener('input', (e) => {
    const val = e.target.value;
    if (val.trim() !== '') {
      selectGenre.value = 'all';
    }
    renderSuggestions(val);
    fetchRecommendations();
  });

  selectTitleSearch.addEventListener('focus', () => {
    if (selectTitleSearch.value.trim() !== '') {
      renderSuggestions(selectTitleSearch.value);
    }
  });

  selectTitleSearch.addEventListener('blur', () => {
    setTimeout(() => {
      if (suggestionsBox) suggestionsBox.classList.add('hidden');
    }, 200);
  });

  selectTitleSearch.addEventListener('keydown', (e) => {
    if (!suggestionsBox || suggestionsBox.classList.contains('hidden')) return;
    const items = suggestionsBox.querySelectorAll('.autocomplete-item');
    if (items.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex + 1) % items.length;
      updateActiveSuggestion(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex - 1 + items.length) % items.length;
      updateActiveSuggestion(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedSuggestionIndex >= 0 && items[selectedSuggestionIndex]) {
        const title = items[selectedSuggestionIndex].dataset.title;
        selectTitleSearch.value = title;
        selectGenre.value = 'all';
        suggestionsBox.classList.add('hidden');
        fetchRecommendations();
      }
    } else if (e.key === 'Escape') {
      suggestionsBox.classList.add('hidden');
    }
  });

  function updateActiveSuggestion(items) {
    items.forEach((item, idx) => {
      if (idx === selectedSuggestionIndex) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('active');
      }
    });
  }

  selectSource.addEventListener('change', () => {
    currentSourceFilter = selectSource.value;
    updatePlatformTabsActiveUI();
    fetchRecommendations();
  });

  selectRating.addEventListener('change', () => fetchRecommendations());
  selectLanguage.addEventListener('change', () => fetchRecommendations());
  inputTopN.addEventListener('change', () => fetchRecommendations());
  btnRunRec.addEventListener('click', () => fetchRecommendations());

  platformTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      currentSourceFilter = tab.dataset.source;
      selectSource.value = currentSourceFilter;
      updatePlatformTabsActiveUI();
      fetchRecommendations();
    });
  });

  function updatePlatformTabsActiveUI() {
    platformTabs.forEach(t => {
      if (t.dataset.source === currentSourceFilter) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });
  }

  // --------------------------------------------------------------------------
  // FETCH RECOMMENDATIONS & STATIC FALLBACK ENGINE
  // --------------------------------------------------------------------------
  async function fetchRecommendations() {
    const selectedTitle = selectTitleSearch.value;
    const selectedGenre = selectGenre.value;
    const selectedRating = selectRating.value;
    const selectedLanguage = selectLanguage.value;
    const topN = parseInt(inputTopN.value, 10) || 10;
    const source = currentSourceFilter;

    cardsGrid.innerHTML = `
      <div class="trend-card-skeleton" style="height:140px; grid-column: 1 / -1;"></div>
      <div class="trend-card-skeleton" style="height:140px; grid-column: 1 / -1;"></div>
    `;

    try {
      const params = new URLSearchParams({
        title: selectedTitle,
        genre: selectedGenre,
        source: source,
        rating: selectedRating,
        language: selectedLanguage,
        top_n: topN,
      });

      const res = await fetch(`${API_BASE}/recommend?${params.toString()}`);
      if (res.ok) {
        const json = await res.json();
        if (json.status === 'success') {
          if (selectedTitle && selectedTitle !== 'none') {
            queryHeading.innerHTML = `Recommendations for <span style="color:#00F2FE;">"${json.query_title || selectedTitle}"</span>`;
          } else if (selectedGenre && selectedGenre !== 'all') {
            const formattedGenre = selectedGenre.charAt(0).toUpperCase() + selectedGenre.slice(1);
            const matchCount = json.total_matching !== undefined ? json.total_matching : json.recommendations.length;
            queryHeading.innerHTML = `<span style="color:#10b981;">${matchCount} titles in <b>${formattedGenre}</b></span>`;
          } else {
            queryHeading.textContent = `All Top Recommended Titles`;
          }

          renderRecommendationCards(json.recommendations || [], json.mode);
          return;
        }
      }
      throw new Error('Switching to static fallback search');
    } catch (err) {
      if (catalogData.length === 0) {
        try {
          const resCat = await fetch('data/catalog.json');
          catalogData = await resCat.json();
        } catch (e) {}
      }
      runStaticFallbackSearch(selectedTitle, selectedGenre, source, selectedRating, selectedLanguage, topN);
    }
  }

  function runStaticFallbackSearch(selectedTitle, selectedGenre, sourceFilter, selectedRating, selectedLanguage, topN) {
    if (catalogData.length === 0) {
      cardsGrid.innerHTML = `<div style="color:var(--text-muted); padding:2rem;">No static dataset loaded.</div>`;
      return;
    }

    let filtered = catalogData.slice();

    // Mode 1: Movie similarity search
    if (selectedTitle && selectedTitle.toLowerCase() !== 'none') {
      const queryItem = catalogData.find(item => item.title.toLowerCase() === selectedTitle.toLowerCase()) || { combined: selectedTitle.toLowerCase() };
      const qTokens = (queryItem.combined || selectedTitle.toLowerCase()).split(/\s+/);

      filtered = filtered.filter(item => item.title.toLowerCase() !== selectedTitle.toLowerCase());

      filtered.forEach(item => {
        let score = 0;
        const text = item.combined || '';
        qTokens.forEach(tok => {
          if (tok.length > 3 && text.includes(tok)) score += 1;
        });
        item.similarity_score = Math.min(0.95, 0.25 + (score * 0.15));
        item.similarity_percent = Math.round(item.similarity_score * 100);
      });

      filtered.sort((a, b) => (b.similarity_score || 0) - (a.similarity_score || 0));
      queryHeading.innerHTML = `Recommendations for <span style="color:#00F2FE;">"${selectedTitle}"</span>`;
    } else {
      // Mode 2: Filter browsing
      if (selectedGenre && selectedGenre !== 'all') {
        filtered = filtered.filter(item => item.genre.toLowerCase().includes(selectedGenre.toLowerCase()));
      }

      filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));

      if (selectedGenre && selectedGenre !== 'all') {
        const formattedGenre = selectedGenre.charAt(0).toUpperCase() + selectedGenre.slice(1);
        queryHeading.innerHTML = `<span style="color:#10b981;">${filtered.length} titles in <b>${formattedGenre}</b></span>`;
      } else {
        queryHeading.textContent = `All Top Recommended Titles`;
      }
    }

    // Apply metadata filters
    if (sourceFilter && sourceFilter !== 'all') {
      filtered = filtered.filter(item => item.source.toLowerCase() === sourceFilter.toLowerCase());
    }

    if (selectedRating && selectedRating !== 'all') {
      const minR = parseFloat(selectedRating);
      filtered = filtered.filter(item => (item.rating || 0) >= minR);
    }

    if (selectedLanguage && selectedLanguage !== 'all') {
      filtered = filtered.filter(item => item.language.toLowerCase().includes(selectedLanguage.toLowerCase()));
    }

    renderRecommendationCards(filtered.slice(0, topN), selectedTitle ? 'title' : 'genre');
  }

  function renderRecommendationCards(recs, mode) {
    if (recs.length === 0) {
      cardsGrid.innerHTML = `
        <div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">
          No matching recommendations found for the selected filters. Try adjusting your search or filter choices.
        </div>
      `;
      return;
    }

    cardsGrid.innerHTML = '';
    recs.forEach(item => {
      const card = document.createElement('div');
      card.className = 'recom-card';
      const poster = getValidPosterUrl(item.poster_url);
      const simPercent = item.similarity_percent || Math.round((item.similarity_score || 0.8) * 100);
      const sourceUpper = (item.source || 'NETFLIX').toUpperCase();

      const isGenreMode = (mode === 'genre') || (!selectTitleSearch.value);
      const simLabel = isGenreMode && item.rating ? `★ ${item.rating} Rating` : `${simPercent}% Similarity`;

      card.innerHTML = `
        <div class="card-poster-col">
          <img src="${poster}" alt="${item.title}" class="card-poster-img" loading="lazy" onerror="this.src='${DEFAULT_POSTER}'">
          <div class="card-poster-badge">${sourceUpper}</div>
        </div>
        <div class="card-info-col">
          <div>
            <h4 class="card-movie-title">${item.title}</h4>
            <p class="card-movie-desc">${item.description || 'A featured title matching textual features and similarity metrics.'}</p>
            <div class="card-tags">
              <span class="card-tag">${item.genre || 'Drama'}</span>
              <span class="card-tag">${item.language || 'English'}</span>
              <span class="card-tag">${item.duration ? item.duration + ' min' : 'Feature'}</span>
            </div>
          </div>
          <div class="card-sim-section">
            <div class="card-sim-label">${simLabel}</div>
            <div class="sim-progress-bar">
              <div class="sim-progress-fill" style="width: ${simPercent}%;"></div>
            </div>
          </div>
        </div>
      `;

      card.addEventListener('click', () => openModal(item));
      cardsGrid.appendChild(card);
    });
  }

  // Modal logic
  function openModal(item) {
    const poster = getValidPosterUrl(item.poster_url);
    const modalPosterEl = document.getElementById('modal-poster');
    modalPosterEl.src = poster;
    modalPosterEl.onerror = () => { modalPosterEl.src = DEFAULT_POSTER; };

    document.getElementById('modal-title').textContent = item.title;
    document.getElementById('modal-desc').textContent = item.description || 'Full movie overview and textual feature breakdown.';
    const simPercent = item.similarity_percent || Math.round((item.similarity_score || 0.8) * 100);
    document.getElementById('modal-sim-text').textContent = `${simPercent}% Cosine Similarity`;
    document.getElementById('modal-sim-progress').style.width = `${simPercent}%`;

    const chipsContainer = document.getElementById('modal-chips');
    chipsContainer.innerHTML = `
      <span class="card-tag">${item.genre || 'Drama'}</span>
      <span class="card-tag">${(item.source || '').toUpperCase()}</span>
      <span class="card-tag">${item.rating ? '★ ' + item.rating : 'Top Rated'}</span>
      <span class="card-tag">${item.language || 'English'}</span>
    `;

    modal.classList.remove('hidden');
  }

  btnCloseModal.addEventListener('click', () => modal.classList.add('hidden'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
  });
});
