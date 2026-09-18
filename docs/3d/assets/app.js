(() => {
  'use strict';

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const PT_MONTHS = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
  const ES_MONTHS = ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];
  const MS_CENTER = {longitude:-54.48, latitude:-20.60};
  const INITIAL_VIEW = {longitude:-54.48, latitude:-20.60, zoom:4.55, pitch:48, bearing:-10, minZoom:4.0, maxZoom:11};
  const Q_REF = 2000;           // referência fixa para manter comparabilidade visual mensal
  const MAX_WIDTH_M = 4600;     // largura cartográfica máxima aproximada
  const MAX_RIVER_HEIGHT_M = 14000; // altura visual máxima do pulso fluvial; não é altitude física
  const TERRAIN_EXAGGERATION = 1.65; // exagero visual moderado do relevo, não altera os dados hidrológicos
  const TERRARIUM = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png';
  const HILLSHADE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Hillshade/MapServer/tile/{z}/{y}/{x}';

  let lang = localStorage.getItem('pulso-ms-lang') === 'es' ? 'es' : 'pt';
  let month = 0;
  let playing = false;
  let playTimer = null;
  let archiveIndex = null;
  let pinRivers = null;
  let glofasRivers = null;
  let boundary = null;
  let temperature = null;
  let pinToGlofas = null;
  let riverParts = [];
  let currentQ = null;
  let currentDate = null;
  let currentSummary = {};
  let outflow = null;
  let outflowMap = new Map();
  let deckgl = null;

  const L = (pt, es) => lang === 'es' ? es : pt;
  const fmt = (v,d=1) => Number.isFinite(Number(v)) ? new Intl.NumberFormat(lang==='es'?'es-ES':'pt-BR',{maximumFractionDigits:d,minimumFractionDigits:d}).format(Number(v)) : '—';
  const num = v => {
    const n=Number(v); if(!Number.isFinite(n)) return '—';
    if(n>=1000) return new Intl.NumberFormat(lang==='es'?'es-ES':'pt-BR',{maximumFractionDigits:0}).format(n);
    if(n>=10) return fmt(n,1); if(n>=1) return fmt(n,2); return fmt(n,3);
  };
  const json = async url => {const r=await fetch(url,{cache:'no-store'}); if(!r.ok) throw new Error(`${r.status} ${url}`); return r.json();};

  function setLoading(text){
    $('#loadingText').textContent=text;
    $('#loading').hidden=false;
  }
  function hideLoading(){ $('#loading').hidden=true; }

  function eachLine(geom, cb){
    if(!geom) return;
    if(geom.type==='LineString') cb(geom.coordinates);
    else if(geom.type==='MultiLineString') geom.coordinates.forEach(cb);
  }
  function featureAnchor(feature){
    let sx=0,sy=0,n=0;
    eachLine(feature?.geometry,coords=>{for(const c of coords){if(Array.isArray(c)&&Number.isFinite(c[0])&&Number.isFinite(c[1])){sx+=c[0];sy+=c[1];n++;}}});
    return n?{lon:sx/n,lat:sy/n}:null;
  }

  function buildMapping(){
    const gpoints=glofasRivers.features.map(featureAnchor);
    const cell=.25,bins=new Map();
    const key=(lon,lat)=>`${Math.floor((lon+180)/cell)},${Math.floor((lat+90)/cell)}`;
    gpoints.forEach((p,i)=>{if(!p)return;const k=key(p.lon,p.lat);if(!bins.has(k))bins.set(k,[]);bins.get(k).push(i);});
    const out=new Int32Array(pinRivers.features.length);out.fill(-1);
    pinRivers.features.forEach((f,pi)=>{
      const p=featureAnchor(f); if(!p)return;
      const bx=Math.floor((p.lon+180)/cell),by=Math.floor((p.lat+90)/cell);let best=-1,bestD=Infinity;
      for(let ring=0;ring<=6&&best<0;ring++){
        for(let dx=-ring;dx<=ring;dx++) for(let dy=-ring;dy<=ring;dy++){
          if(ring&&Math.max(Math.abs(dx),Math.abs(dy))!==ring)continue;
          const arr=bins.get(`${bx+dx},${by+dy}`); if(!arr)continue;
          for(const gi of arr){
            const g=gpoints[gi],cx=Math.cos(p.lat*Math.PI/180),dd=((g.lon-p.lon)*cx)**2+(g.lat-p.lat)**2;
            if(dd<bestD){bestD=dd;best=gi;}
          }
        }
      }
      out[pi]=best;
    });
    pinToGlofas=out;

    riverParts=[];
    pinRivers.features.forEach((f,fi)=>{
      eachLine(f.geometry,path=>{
        if(path.length>1) riverParts.push({featureIndex:fi,path});
      });
    });
  }

  function tempColor(t,alpha=220){
    const x=Math.max(0,Math.min(1,(Number(t)-16)/16));
    const stops=[[38,120,170],[58,171,187],[104,199,142],[232,198,77],[220,111,66]];
    const s=x*(stops.length-1),i=Math.min(stops.length-2,Math.floor(s)),f=s-i,a=stops[i],b=stops[i+1];
    return [Math.round(a[0]+(b[0]-a[0])*f),Math.round(a[1]+(b[1]-a[1])*f),Math.round(a[2]+(b[2]-a[2])*f),alpha];
  }
  function qAtPin(fi){
    const gi=pinToGlofas?.[fi] ?? -1;
    if(gi<0 || !currentQ) return null;
    const q=Number(currentQ[gi]);
    return Number.isFinite(q)&&q>=0?q:null;
  }
  function tempAtPin(fi){
    const arr=temperature?.months?.[String(month+1).padStart(2,'0')];
    if(!Array.isArray(arr)) return null;
    const t=Number(arr[fi]); return Number.isFinite(t)?t:null;
  }
  function qRatio(q){
    if(!Number.isFinite(q)||q<=0)return 0;
    return Math.max(0,Math.min(1,Math.log1p(q)/Math.log1p(Q_REF)));
  }

  function riverHeight(q){
    const r=qRatio(q);
    if(r<=0) return 0;
    // Mantém escala fixa entre meses e realça mudanças sem deixar os rios maiores dominarem toda a cena.
    return MAX_RIVER_HEIGHT_M*Math.pow(r,.82);
  }
  function shadeColor(color, factor, alpha=230){
    const c=color||[56,174,190,230];
    return [
      Math.max(0,Math.min(255,Math.round(c[0]*factor))),
      Math.max(0,Math.min(255,Math.round(c[1]*factor))),
      Math.max(0,Math.min(255,Math.round(c[2]*factor))),
      alpha
    ];
  }
  function volumePath(d, factor){
    const h=riverHeight(qAtPin(d.featureIndex))*factor;
    return d.path.map(p=>[p[0],p[1],h]);
  }


  function ringArea(ring){
    let a=0;
    for(let i=0,j=ring.length-1;i<ring.length;j=i++){
      const p=ring[i],q=ring[j];
      a+=(q[0]*p[1]-p[0]*q[1]);
    }
    return a/2;
  }
  function orientRing(ring, clockwise){
    if(!Array.isArray(ring)) return ring;
    const r=ring.slice();
    const isClockwise=ringArea(r)<0;
    if(isClockwise!==clockwise) r.reverse();
    return r;
  }
  function makeOutsideMask(){
    const geom=boundary?.features?.[0]?.geometry;
    if(!geom || geom.type!=='Polygon' || !geom.coordinates?.[0]?.length) return null;
    const b=geometryBounds(boundary);
    if(!b) return null;
    const [[minLon,minLat],[maxLon,maxLat]]=b;
    const dx=Math.max(2.5,(maxLon-minLon)*.65),dy=Math.max(2.5,(maxLat-minLat)*.55);
    const outer=orientRing([
      [minLon-dx,minLat-dy],[maxLon+dx,minLat-dy],[maxLon+dx,maxLat+dy],
      [minLon-dx,maxLat+dy],[minLon-dx,minLat-dy]
    ],false);
    const hole=orientRing(geom.coordinates[0],true);
    return {type:'Feature',properties:{role:'outside-mask'},geometry:{type:'Polygon',coordinates:[outer,hole]}};
  }

  function renderLayers(){
    if(!deckgl || !pinRivers) return;
    const {PathLayer, GeoJsonLayer, TerrainLayer, LightingEffect, AmbientLight, DirectionalLight} = deck;
    const TerrainExtension = deck._TerrainExtension;
    const terrainExtensions = TerrainExtension ? [new TerrainExtension()] : [];

    const ambient = new AmbientLight({color:[255,255,255],intensity:.82});
    const dir = new DirectionalLight({color:[248,252,250],intensity:.55,direction:[-3,-5,-7]});
    const lighting = new LightingEffect({ambientLight:ambient,directionalLight:dir});
    const s=TERRAIN_EXAGGERATION;

    const terrain = new TerrainLayer({
      id:'terrain-dem',
      minZoom:0,
      maxZoom:12,
      strategy:'no-overlap',
      elevationData:TERRARIUM,
      texture:HILLSHADE,
      elevationDecoder:{rScaler:256*s,gScaler:1*s,bScaler:(1/256)*s,offset:-32768*s},
      meshMaxError: window.matchMedia('(max-width:720px)').matches ? 14 : 8,
      color:[190,211,207],
      opacity:1,
      material:{ambient:.88,diffuse:.28,shininess:1,specularColor:[0,0,0]},
      operation:'terrain+draw',
      pickable:'3d'
    });

    const outsideMask = new GeoJsonLayer({
      id:'outside-ms-mask',
      data:makeOutsideMask(),
      stroked:false,
      filled:true,
      getFillColor:[72,113,127,185],
      pickable:false,
      extensions:terrainExtensions,
      terrainDrawMode:'drape'
    });

    const boundaryLayer = new GeoJsonLayer({
      id:'boundary-terrain',
      data:boundary,
      stroked:true,filled:false,
      getLineColor:[17,65,80,245],getLineWidth:4,lineWidthMinPixels:2.2,
      pickable:false,
      extensions:terrainExtensions,
      terrainDrawMode:'drape'
    });

    const contextLayer = new PathLayer({
      id:'river-context-terrain',
      data:riverParts,
      getPath:d=>d.path,
      getColor:[27,69,77,40],
      getWidth:120,
      widthUnits:'meters',
      widthMinPixels:.35,
      widthMaxPixels:2.2,
      rounded:true,capRounded:true,jointRounded:true,
      pickable:false,
      extensions:terrainExtensions,
      terrainDrawMode:'drape'
    });

    const footprintLayer = new PathLayer({
      id:'river-footprint-terrain',
      data:riverParts,
      getPath:d=>d.path,
      getColor:d=>{
        const q=qAtPin(d.featureIndex);
        if(!Number.isFinite(q)||q<=0)return [58,92,98,5];
        return [18,70,80,42];
      },
      getWidth:d=>260+(MAX_WIDTH_M*1.18)*qRatio(qAtPin(d.featureIndex)),
      widthUnits:'meters',widthMinPixels:.55,widthMaxPixels:12,
      rounded:true,capRounded:true,jointRounded:true,
      pickable:false,
      extensions:terrainExtensions,
      terrainDrawMode:'drape',
      updateTriggers:{getColor:[month,currentDate?.toISOString()],getWidth:[month,currentDate?.toISOString()]}
    });

    // “Volume” hidrológico visual: empilhamos várias fitas a alturas crescentes.
    // A altura codifica descarga GloFAS em escala logarítmica fixa e NÃO representa
    // altitude física nem volume armazenado no rio.
    const volumeParts = riverParts.filter(d=>{
      const q=qAtPin(d.featureIndex);
      return Number.isFinite(q) && q>0;
    });
    const mobile=window.matchMedia('(max-width:720px)').matches;
    const sliceCount=mobile?5:7;
    const volumeLayers=[];
    for(let i=1;i<=sliceCount;i++){
      const f=i/sliceCount;
      volumeLayers.push(new PathLayer({
        id:`river-volume-${i}`,
        data:volumeParts,
        getPath:d=>volumePath(d,f),
        getColor:d=>{
          const t=tempAtPin(d.featureIndex);
          const base=Number.isFinite(t)?tempColor(t,235):[56,174,190,235];
          const brightness=.42+.53*f;
          return shadeColor(base,brightness,205+Math.round(35*f));
        },
        getWidth:d=>{
          const r=qRatio(qAtPin(d.featureIndex));
          const base=180+MAX_WIDTH_M*r;
          // leve afunilamento: a base é mais larga que o topo
          return base*(1.15-.15*f);
        },
        widthUnits:'meters',
        widthMinPixels:.75,
        widthMaxPixels:14,
        rounded:true,capRounded:true,jointRounded:true,
        pickable:false,
        parameters:{depthTest:true},
        extensions:terrainExtensions,
        terrainDrawMode:'offset',
        updateTriggers:{
          getPath:[month,currentDate?.toISOString(),f],
          getColor:[month,currentDate?.toISOString(),f],
          getWidth:[month,currentDate?.toISOString(),f]
        }
      }));
    }

    const pulseTopLayer = new PathLayer({
      id:'river-volume-top',
      data:volumeParts,
      getPath:d=>volumePath(d,1),
      getColor:d=>{
        const t=tempAtPin(d.featureIndex);
        return Number.isFinite(t)?tempColor(t,252):[82,208,216,248];
      },
      getWidth:d=>160+(MAX_WIDTH_M*.96)*qRatio(qAtPin(d.featureIndex)),
      widthUnits:'meters',
      widthMinPixels:1,
      widthMaxPixels:15,
      rounded:true,capRounded:true,jointRounded:true,
      pickable:true,autoHighlight:true,highlightColor:[255,255,255,125],
      parameters:{depthTest:true},
      extensions:terrainExtensions,
      terrainDrawMode:'offset',
      updateTriggers:{
        getPath:[month,currentDate?.toISOString()],
        getColor:[month,currentDate?.toISOString()],
        getWidth:[month,currentDate?.toISOString()]
      }
    });

    deckgl.setProps({
      layers:[terrain,outsideMask,boundaryLayer,contextLayer,footprintLayer,...volumeLayers,pulseTopLayer],
      effects:[lighting]
    });
  }

  function geometryBounds(fc){
    let minLon=Infinity,minLat=Infinity,maxLon=-Infinity,maxLat=-Infinity;
    const walk=c=>{
      if(!Array.isArray(c))return;
      if(typeof c[0]==='number'&&typeof c[1]==='number'){
        minLon=Math.min(minLon,c[0]);maxLon=Math.max(maxLon,c[0]);minLat=Math.min(minLat,c[1]);maxLat=Math.max(maxLat,c[1]);return;
      }
      c.forEach(walk);
    };
    for(const f of fc?.features||[])walk(f.geometry?.coordinates);
    return Number.isFinite(minLon)?[[minLon,minLat],[maxLon,maxLat]]:null;
  }

  function fittedState(){
    const el=$('#deckRoot'),rect=el.getBoundingClientRect(),b=geometryBounds(boundary);
    if(!b||!rect.width||!rect.height)return {...INITIAL_VIEW};
    const mobile=window.matchMedia('(max-width:720px)').matches;
    const vp=new deck.WebMercatorViewport({width:rect.width,height:rect.height,longitude:MS_CENTER.longitude,latitude:MS_CENTER.latitude,zoom:5});
    const fit=vp.fitBounds(b,{padding:mobile?42:85,maxZoom:6.7});
    // A vista inicial privilegia reconhecimento do estado inteiro. O usuário pode inclinar depois.
    return {
      longitude:fit.longitude,
      latitude:fit.latitude-.12,
      zoom:fit.zoom-(mobile?.58:.78),
      pitch:mobile?46:50,
      bearing:-10,
      minZoom:4.0,
      maxZoom:11
    };
  }

  function resetCamera(duration=700){
    const v=fittedState();
    deckgl.setProps({initialViewState:{...v,transitionDuration:duration}});
  }

  function createDeck(){
    deckgl = new deck.DeckGL({
      container:'deckRoot',
      initialViewState:{...INITIAL_VIEW},
      controller:{
        ...(deck.TerrainController ? {type:deck.TerrainController} : {}),
        dragPan:true,
        dragRotate:true,
        scrollZoom:{smooth:true,speed:.008},
        touchZoom:true,
        touchRotate:true,
        multiTouchDrag:true,
        doubleClickZoom:true,
        inertia:true
      },
      layers:[],
      getTooltip:({object})=>{
        if(!object || object.featureIndex==null) return null;
        const q=qAtPin(object.featureIndex),t=tempAtPin(object.featureIndex);
        return {
          html:`<div style="font-family:Inter,Segoe UI,Arial;padding:4px 2px"><b>${L('Trecho fluvial','Tramo fluvial')}</b><br>${L('Descarga','Caudal')}: ${num(q)} m³/s<br>${L('Temperatura','Temperatura')}: ${Number.isFinite(t)?fmt(t,1)+' °C':'—'}<br>${L('Altura visual','Altura visual')}: ${num(riverHeight(q))} m</div>`,
          style:{background:'#082b35',color:'#efffff',fontSize:'12px',borderRadius:'10px'}
        };
      }
    });
  }

  function updateClock(){
    const labels=lang==='es'?ES_MONTHS:PT_MONTHS;
    $('#clockMonth').textContent=labels[month];
    $$('.month-dot').forEach((d,i)=>d.classList.toggle('active',i===month));
  }
  function buildClock(){
    const c=$('#yearClock');
    for(let i=0;i<12;i++){
      const a=(i/12)*Math.PI*2-Math.PI/2,r=43,x=52+Math.cos(a)*r,y=52+Math.sin(a)*r;
      const dot=document.createElement('i');dot.className='month-dot';dot.style.left=`${x}px`;dot.style.top=`${y}px`;dot.title=(lang==='es'?ES_MONTHS:PT_MONTHS)[i];
      c.appendChild(dot);
    }
    updateClock();
  }

  function applyLanguage(){
    document.documentElement.lang=lang==='es'?'es':'pt-BR';
    $$('[data-pt][data-es]').forEach(el=>el.textContent=lang==='es'?el.dataset.es:el.dataset.pt);
    $$('[data-lang-block]').forEach(el=>el.hidden=el.dataset.langBlock!==lang);
    $('#langPt').classList.toggle('active',lang==='pt');
    $('#langEs').classList.toggle('active',lang==='es');
    if(currentDate) $('#dateLabel').textContent=formatDate(currentDate);
    updateClock();
    drawChart();
  }
  function formatDate(d){
    const labels=lang==='es'?ES_MONTHS:PT_MONTHS;
    return `${d.getDate()} ${labels[d.getMonth()]} ${d.getFullYear()}`;
  }

  function chooseRepresentativeDate(monthKey){
    const info=archiveIndex?.months?.[monthKey];
    const dates=info?.dates||[];
    if(!dates.length)return null;
    let best=dates[0],diff=99;
    dates.forEach(x=>{const dd=Math.abs(Number(x.slice(8,10))-15);if(dd<diff){best=x;diff=dd;}});
    return best;
  }

  async function loadMonth(m){
    month=(m+12)%12;
    const key=`2025-${String(month+1).padStart(2,'0')}`;
    const info=archiveIndex?.months?.[key];
    if(!info) throw new Error(`Sem bloco ${key}`);
    const dateToken=chooseRepresentativeDate(key);
    setLoading(L(`Carregando ${key}…`,`Cargando ${key}…`));

    const [meta,binResp]=await Promise.all([
      json(`../data/pulse-v8/${info.meta}`),
      fetch(`../data/pulse-v8/${info.binary}`,{cache:'no-store'})
    ]);
    if(!binResp.ok) throw new Error(`${binResp.status} ${info.binary}`);
    const buffer=await binResp.arrayBuffer();
    const values=new Float32Array(buffer);
    const pos=meta.dates.indexOf(dateToken);
    if(pos<0) throw new Error(`Data ${dateToken} ausente`);
    const n=Number(meta.segment_count),start=pos*n;
    currentQ=values.subarray(start,start+n);
    currentSummary=meta.summaries?.[pos]||{};
    currentDate=new Date(`${dateToken}T12:00:00`);
    $('#dateLabel').textContent=formatDate(currentDate);

    const vals=[];let max=0,active=0;
    for(const q0 of currentQ){const q=Number(q0);if(!Number.isFinite(q)||q<0)continue;vals.push(q);if(q>0)active++;if(q>max)max=q;}
    vals.sort((a,b)=>a-b);
    const p90=Number(currentSummary.discharge_p90_m3s);
    const p90calc=vals.length?vals[Math.min(vals.length-1,Math.floor((vals.length-1)*.9))]:null;
    const p90v=Number.isFinite(p90)?p90:p90calc;
    const maxv=Number(currentSummary.discharge_max_m3s);
    const activev=Number(currentSummary.segments_positive);

    const tsum=temperature?.summary?.[String(month+1).padStart(2,'0')];
    const t=Number(tsum?.median_c ?? tsum?.mean_c);
    $('#tempValue').textContent=Number.isFinite(t)?`${fmt(t,1)}°C`:'—';
    $('#p90Value').textContent=num(p90v);
    $('#maxValue').textContent=num(Number.isFinite(maxv)?maxv:max);
    $('#activeValue').textContent=new Intl.NumberFormat(lang==='es'?'es-ES':'pt-BR').format(Number.isFinite(activev)?activev:active);

    updateClock();
    updateOutflow();
    renderLayers();
    hideLoading();
  }

  function outflowValueFor(token){
    const i=outflowMap.get(token);
    if(!Number.isInteger(i))return null;
    const v=Number(outflow.values_m3s[i]);
    return Number.isFinite(v)&&v>=0?v:null;
  }
  function updateOutflow(){
    if(!currentDate){$('#outflowValue').textContent='—';return;}
    const token=currentDate.toISOString().slice(0,10),v=outflowValueFor(token);
    $('#outflowValue').textContent=v==null?'—':num(v);
    drawChart();
  }

  function rows2025(){
    if(!outflow)return[];
    const rows=[];
    for(let i=0;i<outflow.dates.length;i++){
      const d=outflow.dates[i]; if(!d.startsWith('2025-'))continue;
      const v=Number(outflow.values_m3s[i]); if(Number.isFinite(v)&&v>=0)rows.push({date:d,value:v});
    }
    return rows;
  }
  function drawChart(){
    const canvas=$('#chart'),wrap=$('#chartWrap'),empty=$('#chartEmpty');
    const rect=wrap.getBoundingClientRect(),w=Math.max(10,Math.round(rect.width)),h=Math.max(50,Math.round(rect.height)),dpr=Math.max(1,Math.min(2,devicePixelRatio||1));
    canvas.width=w*dpr;canvas.height=h*dpr;const c=canvas.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);
    const rows=rows2025();
    if(!rows.length){empty.hidden=false;$('#outflowPeak').textContent=L('pico anual —','pico anual —');return;}
    empty.hidden=true;
    const max=Math.max(...rows.map(r=>r.value),1),pad=5,x=i=>pad+i/(rows.length-1)*(w-pad*2),y=v=>pad+(1-v/max)*(h-pad*2);
    c.beginPath();rows.forEach((r,i)=>{const px=x(i),py=y(r.value);i?c.lineTo(px,py):c.moveTo(px,py)});c.strokeStyle='#6bd0d0';c.lineWidth=1.6;c.lineJoin='round';c.stroke();
    c.lineTo(x(rows.length-1),h-pad);c.lineTo(x(0),h-pad);c.closePath();const g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,'rgba(84,205,202,.28)');g.addColorStop(1,'rgba(84,205,202,.01)');c.fillStyle=g;c.fill();
    if(currentDate){
      const token=currentDate.toISOString().slice(0,10);let i=rows.findIndex(r=>r.date===token);
      if(i<0){const day=Math.floor((currentDate-new Date(2025,0,1,12))/86400000);i=Math.max(0,Math.min(rows.length-1,day));}
      const px=x(i),py=y(rows[i].value);c.beginPath();c.moveTo(px,pad);c.lineTo(px,h-pad);c.strokeStyle='rgba(255,255,255,.75)';c.lineWidth=1;c.stroke();c.beginPath();c.arc(px,py,3.5,0,Math.PI*2);c.fillStyle='#fff';c.fill();
    }
    let peak=rows[0];for(const r of rows)if(r.value>peak.value)peak=r;
    $('#outflowPeak').textContent=`${L('pico','pico')} ${peak.date.slice(8,10)}/${peak.date.slice(5,7)} · ${num(peak.value)} m³/s`;
  }

  function selectFromChart(clientX){
    const rows=rows2025();if(!rows.length)return;
    const rect=$('#chartWrap').getBoundingClientRect(),t=Math.max(0,Math.min(1,(clientX-rect.left)/rect.width)),i=Math.round(t*(rows.length-1));
    const d=new Date(`${rows[i].date}T12:00:00`);
    loadMonth(d.getMonth()).catch(console.error);
  }

  async function init(){
    try{
      setLoading(L('Carregando geometria e série 2025…','Cargando geometría y serie 2025…'));
      buildClock();
      createDeck();

      [archiveIndex,pinRivers,glofasRivers,boundary,temperature] = await Promise.all([
        json('../data/pulse-v8/index.json'),
        json('../data/rivers.geojson'),
        json('../data/glofas_network.geojson'),
        json('../data/boundary.geojson'),
        json('../data/temperature-climatology.json')
      ]);
      try{
        outflow=await json('../data/outflow-ms.json');
        if(Array.isArray(outflow?.dates)&&Array.isArray(outflow?.values_m3s)) outflowMap=new Map(outflow.dates.map((d,i)=>[d,i]));
        else outflow=null;
      }catch(_){outflow=null;}

      buildMapping();
      resetCamera(0);
      await loadMonth(0);
      applyLanguage();
    }catch(err){
      console.error(err);
      $('#loadingText').textContent=L(`Falha: ${err.message}`,`Fallo: ${err.message}`);
    }
  }

  $('#langBtn').addEventListener('click',()=>{lang=lang==='pt'?'es':'pt';localStorage.setItem('pulso-ms-lang',lang);applyLanguage();});
  $('#helpBtn').addEventListener('click',()=>$('#helpDialog').showModal());
  $('#closeHelp').addEventListener('click',()=>$('#helpDialog').close());
  $('#helpDialog').addEventListener('click',e=>{if(e.target===$('#helpDialog'))$('#helpDialog').close();});
  $('#prevMonth').addEventListener('click',()=>loadMonth(month-1).catch(console.error));
  $('#nextMonth').addEventListener('click',()=>loadMonth(month+1).catch(console.error));
  $('#playBtn').addEventListener('click',()=>{
    playing=!playing;$('#playBtn span').textContent=playing?'Ⅱ':'▶';
    if(playTimer){clearInterval(playTimer);playTimer=null;}
    if(playing) playTimer=setInterval(()=>loadMonth(month+1).catch(console.error),1500);
  });
  function currentCamera(){
    const v=deckgl?.viewManager?.getViewports?.()?.[0];
    return v?{longitude:v.longitude,latitude:v.latitude,zoom:v.zoom,pitch:v.pitch,bearing:v.bearing,minZoom:4.0,maxZoom:11}:fittedState();
  }
  $('#zoomIn').addEventListener('click',()=>{const vs=currentCamera();deckgl.setProps({initialViewState:{...vs,zoom:Math.min(11,vs.zoom+.45),transitionDuration:250}});});
  $('#zoomOut').addEventListener('click',()=>{const vs=currentCamera();deckgl.setProps({initialViewState:{...vs,zoom:Math.max(4.0,vs.zoom-.45),transitionDuration:250}});});
  $('#resetView').addEventListener('click',()=>resetCamera(700));

  let chartDrag=false;
  $('#chartWrap').addEventListener('pointerdown',e=>{chartDrag=true;$('#chartWrap').setPointerCapture?.(e.pointerId);selectFromChart(e.clientX);});
  $('#chartWrap').addEventListener('pointermove',e=>{if(chartDrag)selectFromChart(e.clientX);});
  $('#chartWrap').addEventListener('pointerup',()=>chartDrag=false);
  $('#chartWrap').addEventListener('pointercancel',()=>chartDrag=false);

  window.addEventListener('resize',()=>drawChart());
  init();
})();