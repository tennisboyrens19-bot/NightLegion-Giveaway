function events(){
  const tab = queryParam('tab') === 'competitions' ? 'competitions' : 'events';
  return `<div class="page container events-page">
    <div class="tabs"><a class="${tab==='events'?'active':''}" href="#/events">Events</a><a class="${tab==='competitions'?'active':''}" href="#/events?tab=competitions">Competitions</a></div>
    ${tab==='events' ? `
      ${panel(`<div class="event-strip"><div><div class="eyebrow">✥ &nbsp; PLANNING</div><h1>NightLegion Bingo 2026</h1><div class="sub">Starts 4 September at 17:00 &nbsp; <span class="purple-dot">•</span> &nbsp; Tiles revealed 2 September at 19:12</div></div><div class="progress-wrap"><div><div class="progress-label"><span>REGION UNLOCKS</span><b>0 / 94</b></div><div class="progress-line"><i></i></div><div class="ticks"><span>0</span><span>14</span><span>24</span><span>34</span><span>44</span><span>56</span><span>68</span><span>80</span><span>94</span></div></div></div><div class="token-card"><div class="token-icon">⌘</div><div><b>0</b><small>PICK TOKENS</small></div><div class="split"><b>NightLegion</b><small>0 spent · 0 regions</small></div></div></div>`, 'panel-purple event-top')}
      ${eventPlanning()}` : `
      ${pageHeader('CLAN EVENTS','Competitions','Current and recent NightLegion competitions.')}
      <div class="competition-grid big">${competitions.map(competitionCard).join('')}</div>
      ${panel(`<div class="section-head"><div><div class="eyebrow">RECENT</div><h2>Competition history</h2></div></div><div class="history-list">${[['BOTW','Duke Sucellus','NL Ryan','+717 KC'],['SOTW','Runecrafting','NL Zeifer','+9.8M XP'],['BOTW','Nex','NL Pur3','+356 KC'],['SOTW','Slayer','NL Sennin','+7.1M XP']].map((r,i)=>`<div class="history-row"><span class="history-index">0${i+1}</span><span><b>${r[0]}</b><small>${r[1]}</small></span><strong>${r[2]}</strong><em>${r[3]}</em></div>`).join('')}</div>`,'panel-purple')}`}
  </div>`;
}

function leaderboard(){
  const sort = queryParam('sort') || 'points';
  let rows=[...members];
  if(sort==='monthly') rows.sort((a,b)=>b.monthly-a.monthly);
  if(sort==='clog') rows.sort((a,b)=>b.clog-a.clog);
  return `<div class="page container leaderboard-page">
    ${pageHeader('CLAN','Leaderboard','NightLegion member standings.',`<div class="head-actions"><div class="segmented"><a class="${sort==='points'?'active':''}" href="#/leaderboard?sort=points">Points</a><a class="${sort==='monthly'?'active':''}" href="#/leaderboard?sort=monthly">Monthly</a><a class="${sort==='clog'?'active':''}" href="#/leaderboard?sort=clog">Clog</a></div><label class="search-wrap">⌕<input class="search" id="leaderSearch" placeholder="Search player" /></label></div>`)}
    <div class="podium-grid section">${rows.slice(0,3).map((m,i)=>`<button class="panel podium-card p${i+1}" data-member="${m.name}"><span class="podium-rank">${['I','II','III'][i]}</span><span class="podium-avatar">${m.avatar}</span><strong>${m.name}</strong><small>${m.rank}</small><b>${nf.format(sort==='monthly'?m.monthly:sort==='clog'?m.clog:m.points)}</b><em>${sort==='monthly'?'points this month':sort==='clog'?'collection slots':'clan points'}</em></button>`).join('')}</div>
    ${panel(`<div class="table-card"><table class="table" id="leaderTable"><thead><tr><th>#</th><th>Player</th><th>Rank</th><th>Clan points</th><th>This month</th><th>Total XP</th></tr></thead><tbody>${rows.map(memberRow).join('')}</tbody></table><div class="no-results hidden" id="leaderEmpty">No members match that search.</div></div>`,'panel-purple')}
  </div>`;
}

function clog(){
  const totalComplete = collectionCategories.reduce((s,x)=>s+x.complete,0);
  const totalSlots = collectionCategories.reduce((s,x)=>s+x.total,0);
  return `<div class="page container clog-page">
    ${pageHeader('COLLECTION LOG','Clog','Clan collection-log overview.',`<label class="search-wrap">⌕<input class="search" id="clogSearch" placeholder="Search collection" /></label>`)}
    <div class="clog-summary section panel panel-purple"><div class="clog-ring" style="--p:${percent(totalComplete,totalSlots)}"><div><strong>${percent(totalComplete,totalSlots)}%</strong><span>complete</span></div></div><div class="clog-summary-copy"><div class="eyebrow">NIGHTLEGION TOTAL</div><h2>${nf.format(totalComplete)} <span>/ ${nf.format(totalSlots)}</span></h2><p>Combined progress across tracked collection-log categories.</p></div><div class="clog-summary-stats"><div><span>Unique slots</span><b>1,525</b></div><div><span>Members tracked</span><b>94</b></div><div><span>Pets owned</span><b>41</b></div></div></div>
    <div class="cards-grid section" id="clogCategories">${collectionCategories.map(c=>panel(`<button class="content-card clog-category" data-clog="${c.name}"><div class="content-icon">${c.icon}</div><div class="eyebrow">${c.name.toUpperCase()}</div><h3>${nf.format(c.complete)} <span>/ ${nf.format(c.total)}</span></h3><p>${c.note}</p><div class="progress-mini"><span style="width:${percent(c.complete,c.total)}%"></span></div><small>${percent(c.complete,c.total)}% complete</small></button>`)).join('')}</div>
    ${panel(`<div class="section-head"><div><div class="eyebrow">HIGHLIGHTS</div><h2>Collection highlights</h2></div></div><div class="highlight-grid" id="clogHighlights">${collectionHighlights.map(x=>`<div class="highlight-row" data-search="${x.join(' ').toLowerCase()}"><span class="item-placeholder">${x[0][0]}</span><span><b>${x[0]}</b><small>${x[1]}</small></span><strong>${x[2]}</strong><em>${x[3]}</em></div>`).join('')}</div>`,'panel-purple')}
  </div>`;
}

function speedruns(){
  const cat = queryParam('category') || 'All';
  const categories = ['All',...new Set(speedrunRows.map(x=>x.category))];
  const rows = cat==='All' ? speedrunRows : speedrunRows.filter(x=>x.category===cat);
  return `<div class="page container speed-page">
    ${pageHeader('RECORDS','Speedruns','NightLegion best times and raid records.')}
    <div class="filter-pills section">${categories.map(x=>`<a class="${x===cat?'active':''}" href="#/speedruns?category=${encodeURIComponent(x)}">${x}</a>`).join('')}</div>
    <div class="speed-feature-grid">${rows.slice(0,3).map((r,i)=>`<button class="panel record-card" data-member="${r.player}"><div class="record-badge">${i+1}</div><div class="eyebrow">${r.category.toUpperCase()}</div><h3>${r.time}</h3><p>${r.team}</p><div class="record-owner"><span class="avatar-mini">${members.find(m=>m.name===r.player)?.avatar||'NL'}</span><span>${r.player}<small>${dateLabel(r.date)}</small></span></div></button>`).join('')}</div>
    ${panel(`<div class="table-card speed-table"><table class="table"><thead><tr><th>#</th><th>Category</th><th>Team / Scale</th><th>Player</th><th>Best time</th><th>Date</th></tr></thead><tbody>${rows.map((r,i)=>`<tr class="click-row" data-member="${r.player}"><td class="rank-num">${i+1}</td><td class="name-cell">${r.category}</td><td>${r.team}</td><td>${r.player}</td><td class="value green">${r.time}</td><td class="value">${dateLabel(r.date)}</td></tr>`).join('')}</tbody></table></div>`,'panel-purple')}
  </div>`;
}

function rankRow(r){
  return `<div class="rank-row"><div class="rank-icon">${r.icon}</div><div class="rank-main"><h3>${r.name}</h3><p>${r.description}</p></div><div class="rank-points"><strong>${r.threshold}</strong><small>${r.monthly}</small></div></div>`;
}
function sourceRow(s){
  return `<div class="source-row"><div class="source-icon">${s.icon}</div><div><h4>${s.title}</h4><p>${s.description}</p></div><strong>${s.points}</strong></div>`;
}
function ranksPage(){
  const groups=['Leadership','Staff','Progression'];
  const sources=['Progression','Achievements','Drops','Loyalty'];
  return `<div class="page container ranks-page">
    ${pageHeader('CLAN PROGRESSION','Ranks','NightLegion rank progression and point sources.')}
    <div class="rank-layout section"><div class="rank-column">${groups.map(g=>panel(`<div class="section-head compact"><div><div class="eyebrow">${g.toUpperCase()}</div><h2>${g}</h2></div></div><div class="rank-list">${ranks.filter(r=>r.group===g).map(rankRow).join('')}</div>`,g==='Progression'?'panel-purple':'')).join('')}</div>
    <aside class="rank-sidebar">${panel(`<div class="profile-summary"><div class="profile-avatar">NL</div><div class="eyebrow">YOUR PROFILE</div><h3>Login to view progress</h3><p>See your current rank, points and next-rank progress.</p><button class="primary-wide js-login">Login with Discord</button></div>`,'panel-purple sticky-card')}</aside></div>
    <div class="section section-head standalone"><div><div class="eyebrow">POINT SOURCES</div><h2>How points are earned</h2></div></div>
    <div class="source-sections">${sources.map(g=>panel(`<button class="collapse-head" data-collapse="${g}"><span><span class="triangle">▾</span><b>${g}</b></span><small>${pointSources.filter(s=>s.group===g).length} sources</small></button><div class="collapse-body" data-collapse-body="${g}">${pointSources.filter(s=>s.group===g).map(sourceRow).join('')}</div>`)).join('')}</div>
  </div>`;
}

function render(){
  const r=route(); setActive(r);
  app.innerHTML=({home,events,leaderboard,clog,speedruns,ranks:ranksPage}[r])();
  nav.classList.remove('open'); menuButton.setAttribute('aria-expanded','false');
  bindPageInteractions();
  window.scrollTo({top:0,behavior:'auto'});
}

function bindPageInteractions(){
  document.querySelectorAll('[data-member]').forEach(el=>el.addEventListener('click',()=>openMember(el.dataset.member)));
  document.querySelectorAll('.js-login').forEach(el=>el.addEventListener('click',openLogin));

  const leaderSearch=document.getElementById('leaderSearch');
  if(leaderSearch){ leaderSearch.addEventListener('input',()=>{const q=leaderSearch.value.trim().toLowerCase();let shown=0;document.querySelectorAll('#leaderTable tbody tr').forEach(tr=>{const ok=tr.textContent.toLowerCase().includes(q);tr.classList.toggle('hidden',!ok);if(ok)shown++});document.getElementById('leaderEmpty').classList.toggle('hidden',shown!==0);}); }

  const clogSearch=document.getElementById('clogSearch');
  if(clogSearch){ clogSearch.addEventListener('input',()=>{const q=clogSearch.value.trim().toLowerCase();document.querySelectorAll('.clog-category').forEach(x=>x.closest('.panel').classList.toggle('hidden',!x.textContent.toLowerCase().includes(q)));document.querySelectorAll('[data-search]').forEach(x=>x.classList.toggle('hidden',!x.dataset.search.includes(q)));}); }

  document.querySelectorAll('[data-collapse]').forEach(btn=>btn.addEventListener('click',()=>{const key=btn.dataset.collapse;const body=document.querySelector(`[data-collapse-body="${key}"]`);const closed=body.classList.toggle('collapsed');btn.classList.toggle('collapsed',closed);}));
  document.querySelectorAll('[data-task]').forEach(tile=>tile.addEventListener('click',()=>showToast(`${tile.dataset.task} · event tile preview`)));
  document.querySelectorAll('[data-team]').forEach(card=>card.addEventListener('click',()=>{selectedBingoTeam=card.dataset.team;showToast(`${selectedBingoTeam} selected`);render();}));
}

function openMember(name){
  const m=members.find(x=>x.name===name); if(!m) return;
  const idx=members.indexOf(m)+1;
  profileDrawer.innerHTML=`<button class="drawer-close" id="drawerClose" type="button">×</button><div class="drawer-hero"><div class="drawer-avatar">${m.avatar}</div><div class="eyebrow">NIGHTLEGION MEMBER</div><h2>${m.name}</h2><span class="tag purple">${m.rank}</span></div><div class="drawer-stats"><div><span>Clan rank</span><b>#${idx}</b></div><div><span>Clan points</span><b>${nf.format(m.points)}</b></div><div><span>This month</span><b class="green">+${nf.format(m.monthly)}</b></div><div><span>Total XP</span><b>${m.xp}</b></div><div><span>Collection log</span><b>${nf.format(m.clog)}</b></div><div><span>Speed records</span><b>${m.speed}</b></div></div><div class="drawer-section"><div class="eyebrow">PROGRESSION</div><div class="drawer-progress-label"><span>Current progression</span><b>${Math.min(99,Math.round(m.points/155))}%</b></div><div class="progress-mini large"><span style="width:${Math.min(99,Math.round(m.points/155))}%"></span></div></div><div class="drawer-section"><div class="eyebrow">MEMBER SINCE</div><p>${dateLabel(m.joined)}</p></div>`;
  profileDrawer.classList.add('open'); drawerBackdrop.classList.remove('hidden'); profileDrawer.setAttribute('aria-hidden','false');
  document.getElementById('drawerClose').addEventListener('click',closeDrawer);
}
function closeDrawer(){ profileDrawer.classList.remove('open'); drawerBackdrop.classList.add('hidden'); profileDrawer.setAttribute('aria-hidden','true'); }
function openLogin(){ loginModal.classList.remove('hidden'); }
function closeLogin(){ loginModal.classList.add('hidden'); }
function showToast(message){ toast.textContent=message;toast.classList.add('show');clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>toast.classList.remove('show'),1800); }

menuButton.addEventListener('click',()=>{const open=nav.classList.toggle('open');menuButton.setAttribute('aria-expanded',String(open));});
document.getElementById('loginButton').addEventListener('click',openLogin);
document.getElementById('closeModal').addEventListener('click',closeLogin);
loginModal.addEventListener('click',e=>{if(e.target===loginModal)closeLogin();});
drawerBackdrop.addEventListener('click',closeDrawer);
document.getElementById('discordLogin').addEventListener('click',()=>{ if(CONFIG.discordOAuthUrl){ location.href=CONFIG.discordOAuthUrl; } else { showToast('Discord OAuth URL is not configured yet'); window.open(CONFIG.discordInvite,'_blank','noopener,noreferrer'); } });
window.addEventListener('hashchange',render);
window.addEventListener('keydown',e=>{if(e.key==='Escape'){closeLogin();closeDrawer();}});
render();
