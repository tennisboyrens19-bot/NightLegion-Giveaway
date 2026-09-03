const app = document.getElementById('app');
const nav = document.getElementById('mainNav');
const menuButton = document.getElementById('menuButton');
const loginModal = document.getElementById('loginModal');
const profileDrawer = document.getElementById('profileDrawer');
const drawerBackdrop = document.getElementById('drawerBackdrop');
const toast = document.getElementById('toast');

const CONFIG = {
  discordInvite: 'https://discord.gg/AP2aK742SZ',
  discordOAuthUrl: '', // Set this to your NightLegion Discord OAuth2 authorize URL when ready.
};

const routes = ['home','events','leaderboard','clog','speedruns','ranks'];
let selectedBingoTeam = 'NightLegion Main';
const nf = new Intl.NumberFormat('en-GB');

const members = [
  {name:'NL Ryan', rank:'Owner', points:15420, monthly:1220, xp:'1.94b', clog:1284, speed:11, joined:'2024-01-12', avatar:'♛'},
  {name:'NL Zeifer', rank:'Deputy Owner', points:14410, monthly:1115, xp:'1.68b', clog:1217, speed:9, joined:'2024-02-03', avatar:'♜'},
  {name:'NL Pur3', rank:'General', points:13755, monthly:1040, xp:'1.44b', clog:1191, speed:13, joined:'2024-03-18', avatar:'✦'},
  {name:'NL M B', rank:'General', points:12840, monthly:980, xp:'1.22b', clog:1136, speed:7, joined:'2024-03-29', avatar:'✦'},
  {name:'NL Sennin', rank:'Major', points:11970, monthly:915, xp:'1.05b', clog:1108, speed:5, joined:'2024-05-11', avatar:'✧'},
  {name:'NL Dracul', rank:'Captain', points:11225, monthly:866, xp:'948m', clog:1054, speed:6, joined:'2024-05-24', avatar:'◆'},
  {name:'NL Meme', rank:'Lieutenant', points:10610, monthly:812, xp:'883m', clog:1009, speed:4, joined:'2024-06-08', avatar:'◇'},
  {name:'NL Phaze', rank:'Lieutenant', points:9840, monthly:773, xp:'810m', clog:976, speed:2, joined:'2024-07-01', avatar:'◇'},
  {name:'NL Kier', rank:'Sergeant', points:9230, monthly:712, xp:'724m', clog:912, speed:1, joined:'2024-07-19', avatar:'◈'},
  {name:'NL Vulc', rank:'Sergeant', points:8770, monthly:680, xp:'662m', clog:888, speed:3, joined:'2024-08-02', avatar:'◈'},
  {name:'NL TothMate', rank:'Corporal', points:8125, monthly:610, xp:'593m', clog:843, speed:0, joined:'2024-09-14', avatar:'◉'},
  {name:'NL Stray', rank:'Corporal', points:7640, monthly:572, xp:'548m', clog:816, speed:1, joined:'2024-10-04', avatar:'◉'},
  {name:'NL Wynn', rank:'Private', points:6995, monthly:529, xp:'501m', clog:770, speed:0, joined:'2025-01-22', avatar:'●'},
  {name:'NL Zire', rank:'Private', points:6420, monthly:481, xp:'442m', clog:731, speed:0, joined:'2025-02-16', avatar:'●'},
  {name:'NL Yohne', rank:'Recruit', points:5850, monthly:422, xp:'399m', clog:684, speed:0, joined:'2025-04-08', avatar:'○'},
];

const ranks = [
  {name:'Owner', threshold:'Special', monthly:'—', icon:'♛', description:'Clan owner and final authority.', group:'Leadership'},
  {name:'Deputy Owner', threshold:'Special', monthly:'—', icon:'♜', description:'Senior clan leadership and owner delegate.', group:'Leadership'},
  {name:'General', threshold:'Special', monthly:'—', icon:'✦', description:'Senior staff rank with clan-wide responsibility.', group:'Staff'},
  {name:'Major', threshold:'Special', monthly:'—', icon:'✧', description:'Staff rank responsible for moderation and events.', group:'Staff'},
  {name:'Captain', threshold:'10,000 pts', monthly:'750/mo', icon:'◆', description:'Veteran progression rank.', group:'Progression'},
  {name:'Lieutenant', threshold:'8,000 pts', monthly:'600/mo', icon:'◇', description:'Established progression rank.', group:'Progression'},
  {name:'Sergeant', threshold:'6,000 pts', monthly:'450/mo', icon:'◈', description:'Active progression rank.', group:'Progression'},
  {name:'Corporal', threshold:'4,000 pts', monthly:'300/mo', icon:'◉', description:'Consistent clan contributor.', group:'Progression'},
  {name:'Private', threshold:'2,000 pts', monthly:'150/mo', icon:'●', description:'Regular member progression rank.', group:'Progression'},
  {name:'Recruit', threshold:'0 pts', monthly:'—', icon:'○', description:'Entry member rank.', group:'Progression'},
];

const collectionCategories = [
  {name:'Bosses', complete:6218, total:7540, icon:'☠', note:'Boss uniques and boss collection-log slots'},
  {name:'Raids', complete:1948, total:2420, icon:'⚔', note:'Chambers, Theatre and Tombs collections'},
  {name:'Clues', complete:2144, total:3100, icon:'✉', note:'Treasure trail collection-log slots'},
  {name:'Minigames', complete:1301, total:1880, icon:'✥', note:'Minigame and activity rewards'},
  {name:'Other', complete:1229, total:2050, icon:'◆', note:'Miscellaneous collection-log categories'},
  {name:'Pets', complete:41, total:67, icon:'♟', note:'Unique pets owned by clan members'},
];

const collectionHighlights = [
  ['Twisted bow','Raids','14 owners','Very rare'],['Tumeken’s shadow','Raids','18 owners','Very rare'],['Scythe of vitur','Raids','16 owners','Very rare'],
  ['Torva full helm','Bosses','27 owners','Rare'],['Nexling','Pets','7 owners','Pet'],['Bloodhound','Pets','4 owners','Pet'],
  ['3rd age pickaxe','Clues','1 owner','Mega rare'],['Jar of darkness','Bosses','11 owners','Rare']
];

const speedrunRows = [
  {category:'Corrupted Gauntlet', team:'Solo', player:'NL Ryan', time:'5:42.60', date:'2026-08-29'},
  {category:'Tombs of Amascut', team:'Solo 500', player:'NL Zeifer', time:'18:11.20', date:'2026-08-28'},
  {category:'Theatre of Blood', team:'4-man', player:'NL Pur3', time:'15:36.40', date:'2026-08-25'},
  {category:'Chambers of Xeric', team:'Solo', player:'NL M B', time:'21:48.00', date:'2026-08-23'},
  {category:'Inferno', team:'Solo', player:'NL Sennin', time:'47:12.80', date:'2026-08-21'},
  {category:'Colosseum', team:'Solo', player:'NL Dracul', time:'20:01.40', date:'2026-08-18'},
  {category:'Tombs of Amascut', team:'8-man 400', player:'NL Ryan', time:'14:48.60', date:'2026-08-14'},
  {category:'Theatre of Blood', team:'5-man', player:'NL Pur3', time:'14:55.40', date:'2026-08-12'},
  {category:'Chambers of Xeric', team:'5-man CM', player:'NL Zeifer', time:'18:37.20', date:'2026-08-10'},
];

const competitions = [
  {type:'Boss of the Week', title:'Vorkath', status:'Live', metric:'Kills gained', end:'7 September · 21:37', prize:'300M GP', players:18, leader:'NL Ryan', score:'+428 KC', icon:'🐉'},
  {type:'Skill of the Week', title:'Firemaking', status:'Live', metric:'XP gained', end:'7 September · 21:37', prize:'200M GP', players:23, leader:'NL Zeifer', score:'+14.2M XP', icon:'🔥'},
  {type:'Clan Competition', title:'NightLegion Bingo 2026', status:'Planning', metric:'Region board', end:'Starts 4 September', prize:'Clan event', players:64, leader:'—', score:'0 / 94 regions', icon:'✥'},
];

const bingoTeams = [
  {name:'NightLegion Main', count:16, active:true, starts:['Karamja','Misthalin','Global','Sailing'], members:['NL Ryan','NL Zeifer','NL Pur3','NL M B','NL Sennin','NL Dracul','NL Meme','NL Phaze','NL Kier','NL Vulc','NL TothMate','NL Stray','NL Wynn','NL Zire','NL Yohne']},
  {name:'NightLegion PVM', count:16, starts:['Asgarnia','Kandarin'], members:['Aick Rstley','Archivor','Depurrence','BurniLN','Vibe','Tylor']},
  {name:'NightLegion Iron', count:16, starts:['Fremennik','Kourend'], members:['Iron Chakka','Moe','Nippy','Zanny']},
  {name:'NightLegion Casuals', count:16, starts:['Morytania','Desert'], members:['Skill Issue','Ariana','Plant Lover','Tommy Gunz']},
];

const pointSources = [
  {group:'Progression', title:'XP progression', description:'Earn points from long-term account progression and milestone XP.', points:'10 pts / 10m XP', icon:'⚡'},
  {group:'Progression', title:'200M skill', description:'Awarded once per skill at 200,000,000 XP.', points:'200 pts', icon:'★'},
  {group:'Achievements', title:'Collection log milestones', description:'Milestone rewards as your completed collection-log total rises.', points:'100–3,000 pts', icon:'▦'},
  {group:'Achievements', title:'Combat achievement tiers', description:'Tier completions from Easy through Grandmaster.', points:'33–3,000 pts', icon:'⚔'},
  {group:'Drops', title:'Valuable drops', description:'Tradeable drops at or above the minimum value threshold.', points:'1 pt / 1m GP', icon:'◆'},
  {group:'Drops', title:'Pets', description:'New pets receive the full award; duplicate pet rolls receive a smaller award.', points:'100 / 50 pts', icon:'♟'},
  {group:'Loyalty', title:'Clan loyalty', description:'Recurring award for sustained membership in NightLegion.', points:'50–150 pts', icon:'⌛'},
];

function route(){
  const p = location.hash.replace(/^#\/?/, '').split(/[\/?]/)[0];
  return routes.includes(p) && p ? p : 'home';
}
function queryParam(name){
  const parts = location.hash.split('?');
  return new URLSearchParams(parts[1] || '').get(name);
}
function setActive(r){ document.querySelectorAll('.nav a').forEach(a=>a.classList.toggle('active',a.dataset.route===r)); }
function panel(content, extra=''){ return `<section class="panel ${extra}">${content}</section>`; }
function percent(a,b){ return Math.min(100, Math.round((a/b)*100)); }
function dateLabel(iso){ return new Date(`${iso}T12:00:00`).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}); }
function initials(name){ return name.split(' ').map(x=>x[0]).join('').slice(0,2).toUpperCase(); }
function pageHeader(kicker,title,description,right=''){ return `<div class="page-head"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></div>${right}</div>`; }
function statTile(label,value,sub=''){ return `<div class="stat-card"><span>${label}</span><strong>${value}</strong>${sub?`<small>${sub}</small>`:''}</div>`; }

function memberRow(m,i){
  return `<tr class="click-row" data-member="${m.name}"><td class="rank-num">${i+1}</td><td class="name-cell"><span class="avatar-mini">${m.avatar}</span><span>${m.name}</span></td><td><span class="tag ${i<5?'purple':''}">${m.rank}</span></td><td class="value">${nf.format(m.points)}</td><td class="value green">+${nf.format(m.monthly)}</td><td class="value">${m.xp}</td></tr>`;
}

function home(){
  const top = members.slice(0,3);
  return `<div class="page container home-page">
    <section class="home-hero panel panel-purple">
      <div class="hero-glow"></div>
      <div class="hero-copy">
        <div class="eyebrow">OLD SCHOOL RUNESCAPE CLAN</div>
        <h1>NightLegion</h1>
        <p>Competition, progression and community — built around the people who make the clan.</p>
        <div class="cta-row"><a class="primary" href="#/events">Explore Events</a><a class="secondary" href="#/leaderboard">View Leaderboard</a></div>
      </div>
      <div class="hero-emblem"><div class="crest-ring"><img src="${NL_ASSETS.crest}" alt="NightLegion crest" /></div><span>EST. NIGHTLEGION</span></div>
    </section>

    <div class="stats-grid section">
      ${statTile('Members','94','active clan roster')}
      ${statTile('Clan points','1.87m','combined total')}
      ${statTile('Collection logs','12,840','combined slots')}
      ${statTile('Speedrun records','328','tracked records')}
    </div>

    <div class="home-grid section">
      ${panel(`<div class="section-head"><div><div class="eyebrow">NOW</div><h2>NightLegion Bingo 2026</h2></div><a href="#/events">Open event →</a></div>
        <div class="mini-event"><div class="mini-event-art"><img src="${NL_ASSETS.crest}" alt=""/><span>PLANNING</span></div><div class="mini-event-copy"><h3>Starts 4 September at 17:00</h3><p>Four teams. Region unlocks. A 3×3 board for every region.</p><div class="mini-progress"><span style="width:4%"></span></div><div class="mini-meta"><span>0 / 94 regions</span><span>64 players</span></div></div></div>`, 'panel-purple')}
      ${panel(`<div class="section-head"><div><div class="eyebrow">TOP MEMBERS</div><h2>Clan leaderboard</h2></div><a href="#/leaderboard">Full table →</a></div><div class="podium-list">${top.map((m,i)=>`<button class="podium-row" data-member="${m.name}"><span class="podium-place">${i+1}</span><span class="avatar-mini">${m.avatar}</span><span class="podium-name">${m.name}<small>${m.rank}</small></span><strong>${nf.format(m.points)}</strong></button>`).join('')}</div>`)}
    </div>

    <div class="section section-head standalone"><div><div class="eyebrow">COMPETITIONS</div><h2>Current clan competitions</h2></div><a href="#/events?tab=competitions">View all →</a></div>
    <div class="competition-grid">${competitions.slice(0,3).map(competitionCard).join('')}</div>
  </div>`;
}

function teamCard(team){
  const active = team.name === selectedBingoTeam;
  return `<button class="panel team-card ${active?'active':''}" data-team="${team.name}"><div class="team-head"><span>${team.name}</span><span>♙ ${team.count}</span></div><div class="team-meta"><span>▣ 4/13</span><span>◌ 0</span><span>0 picks in hand</span></div>${active?`<div class="chips">${team.members.slice(0,10).map(m=>`<span class="chip">${m}</span>`).join('')}</div><div class="starts">STARTS WITH ${team.starts.map(x=>`<span>${x}</span>`).join('')}</div>`:''}</button>`;
}

function eventPlanning(){
  return `<div class="event-grid section">
    <aside class="left-column">
      <div class="pill">✦ PLANNING</div>
      <div class="hero-title">NightLegion<span>Bingo 2026</span></div>
      <div class="meta-row"><span>▣</span><span>Starts 4 September – 7 September</span></div>
      <div class="lead">⚔ &nbsp; Pick a team to paint its starting map, click a region to see what awaits.</div>
      <div class="label">TEAMS</div>
      ${bingoTeams.map(teamCard).join('')}
    </aside>
    <section class="panel panel-purple map-card">
      <div class="map-stage"><div class="map-image"></div><div class="map-hint">✦ &nbsp; Click a region to see what awaits there &nbsp; ✦</div></div>
      <div class="board"><div class="board-head"><div class="region-badge">⚔</div><div><div class="board-title-line"><h3>Karamja</h3><span class="open-pill">◉ OPEN FOR EVERYONE</span></div><div class="board-sub">3×3 board &nbsp;·&nbsp; 13 pts on the board</div></div></div>
      <div class="bingo-grid"><div></div><div class="col">A</div><div class="col">B</div><div class="col">C</div>
      ${[['1','💀|Obtain a Dragon Med Helm','📜|Complete The Bone Voyage 1/5','⛏|Chop 500 Mahogany Logs'],['2','🐍|Kill 250 Jungle Snakes','🥾|Track 5 Do Run (But Gleam)','🧪|Brew a Ranging Potion'],['3','🏹|Equip a Rune Crossbow','🍌|Collect 100 Banana Slices','💍|Craft a Dragonstone Amulet']].map(r=>`<div class="row">${r[0]}</div>${r.slice(1).map(t=>{const [i,tx]=t.split('|');return `<button class="tile" data-task="${tx}"><i>${i}</i><span>${tx}</span></button>`}).join('')}`).join('')}
      </div></div>
    </section>
  </div>`;
}

function competitionCard(c){
  return `<article class="panel competition-card"><div class="competition-top"><div class="competition-icon">${c.icon}</div><div><div class="eyebrow">${c.type.toUpperCase()}</div><h3>${c.title}</h3></div><span class="status ${c.status.toLowerCase()}">${c.status}</span></div><div class="competition-stats"><div><span>Ends</span><b>${c.end}</b></div><div><span>Players</span><b>${c.players}</b></div><div><span>Prize</span><b>${c.prize}</b></div></div><div class="leader-strip"><span>${c.metric}</span><strong>${c.leader}</strong><b>${c.score}</b></div></article>`;
}

