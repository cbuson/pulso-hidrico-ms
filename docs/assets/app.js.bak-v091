(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  const appShell=$('#appShell'), mapEl=$('#msMap'), tileStack=$('#tileStack'), canvas=$('#mapCanvas'), ctx=canvas.getContext('2d');
  const dateInput=$('#dateInput'), dateLabel=$('#dateLabel'), sideDateLabel=$('#sideDateLabel'), daySlider=$('#daySlider');
  const modePill=$('#modePill'), geometryPill=$('#geometryPill'), mapNote=$('#mapNote');
  const dischargeValue=$('#dischargeValue'), dischargeBar=$('#dischargeBar'), tempValue=$('#tempValue'), temperatureBar=$('#temperatureBar');
  const dischargeLabel=$('#dischargeLabel'), dischargeUnit=$('#dischargeUnit'), tempUnit=$('#tempUnit'), realFilesStatus=$('#realFilesStatus');
  const geometryStatus=$('#geometryStatus'), pulseStatus=$('#pulseStatus'), riverLayerCaption=$('#riverLayerCaption'), boundaryLayerCaption=$('#boundaryLayerCaption');
  const playBtn=$('#playBtn'), attr=$('#mapAttribution'), mapFallback=$('#mapFallback');
  const realStats=$('#realStats'), p90Value=$('#p90Value'), maxValue=$('#maxValue'), activeValue=$('#activeValue');
  const legendThinText=$('#legendThinText'), legendThickText=$('#legendThickText'), tempLegend=$('#tempLegend');
  const timelineMode=$('#timelineMode'), scienceNotice=$('#scienceNotice');
  const helpHeaderBtn=$('#helpHeaderBtn'), infoHeaderBtn=$('#infoHeaderBtn'), helpDialog=$('#helpDialog'), infoDialog=$('#infoDialog');
  const langToggle=$('#langToggle'), langPt=$('#langPt'), langEs=$('#langEs');
  const mapTempValue=$('#mapTempValue'), mapFlowValue=$('#mapFlowValue'), mapFlowBar=$('#mapFlowBar'), mapTempCaption=$('#mapTempCaption'), mapMaxValue=$('#mapMaxValue'), mapActiveValue=$('#mapActiveValue');
  const timelineLabels=$$('.timeline-labels span');
  const mobileSheet=$('#mobileSheet'), mobileSheetHead=$('#mobileSheetHead'), mobileSheetTitle=$('#mobileSheetTitle'), mobileSheetClose=$('#mobileSheetClose'), mobileSheetBackdrop=$('#mobileSheetBackdrop');
  const outflowDock=$('#outflowDock'), outflowValue=$('#outflowValue'), outflowSub=$('#outflowSub'), outflowYearLabel=$('#outflowYearLabel'), outflowPeakLabel=$('#outflowPeakLabel'), outflowChart=$('#outflowChart'), outflowChartWrap=$('#outflowChartWrap'), outflowHint=$('#outflowHint');

  const MS_BOUNDS={minLon:-58.25,maxLon:-50.70,minLat:-24.20,maxLat:-17.00};
  const MS_CENTER={lon:-54.48,lat:-20.60};
  const PT_MONTHS=['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
  const ES_MONTHS=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];
  let uiLang=localStorage.getItem('pulso-ms-lang')==='es'?'es':'pt';
  const L=(pt,es)=>uiLang==='es'?es:pt;
  const QUICK_DATES=['2001-02-08','2010-02-08','2020-02-08','2025-02-08'];
  const TILE=256;
  const BASES={
    topo:{templates:['https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],attribution:'Tiles © Esri'},
    osm:{templates:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],attribution:'© OpenStreetMap contributors'},
    sat:{templates:['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],attribution:'Tiles © Esri'},
    light:{templates:['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'],attribution:'Tiles © Esri'},
    hillshade:{templates:['https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}'],attribution:'Hillshade © Esri'}
  };

  const state={
    boundary:null,pinRivers:null,glofasRivers:null,daily:null,tempClimate:null,pinToGlofas:null,
    riverOn:true,boundaryOn:true,tempOn:true,flowOn:true,
    playing:false,timer:null,availableDates:[],datePos:new Map(),availableMonths:[],monthDates:new Map(),archiveIndex:null,monthCache:new Map(),
    baseKey:localStorage.getItem('pulso-ms-basemap')||'hillshade',center:{...MS_CENTER},zoom:6,
    dpr:Math.max(1,Math.min(2,devicePixelRatio||1)),dragging:false,dragStart:null,centerStart:null,
    tileLoads:0,tileErrors:0,tileFailTimer:null,renderQueued:false,requestSerial:0,
    mapPointers:new Map(),gesture:null,lastTapAt:0,lastTapPoint:null,
    outflow:null,outflowDatePos:new Map(),outflowYearData:[],outflowDragTimer:null,
    sheetDrag:null
  };

  function isoDate(d){return d.toISOString().slice(0,10);}
  function parseDate(v){const [y,m,d]=v.split('-').map(Number);return new Date(y,m-1,d,12);}
  function fmtDate(d){const months=uiLang==='es'?ES_MONTHS:PT_MONTHS;return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;}
  function monthKey(d){return isoDate(d).slice(0,7);}
  function daysInMonth(y,m){return new Date(y,m+1,0,12).getDate();}
  function addMonthsClamped(date,n){const day=date.getDate(),first=new Date(date.getFullYear(),date.getMonth()+n,1,12);first.setDate(Math.min(day,daysInMonth(first.getFullYear(),first.getMonth())));return first;}

  function syncTimeline(date){
    if(state.availableDates.length){
      daySlider.disabled=false;daySlider.min='0';daySlider.max=String(Math.max(0,state.availableDates.length-1));
      const pos=state.datePos.get(isoDate(date));if(Number.isInteger(pos))daySlider.value=String(pos);
      const first=state.availableDates[0],last=state.availableDates[state.availableDates.length-1],y0=Number(first.slice(0,4)),y4=Number(last.slice(0,4));
      const years=[0,.25,.5,.75,1].map(f=>String(Math.round(y0+(y4-y0)*f)));timelineLabels.forEach((el,i)=>el.textContent=years[i]||'');
    }else{daySlider.disabled=true;timelineLabels.forEach((el,i)=>el.textContent=['2001','2007','2013','2019','2025'][i]);}
  }
  function setDate(d,{load=true}={}){dateInput.value=isoDate(d);dateLabel.textContent=fmtDate(d);sideDateLabel.textContent=fmtDate(d);syncTimeline(d);return load?updateForDate(d):Promise.resolve();}
  function realDateStep(n){
    const dates=state.availableDates;if(!dates.length)return Promise.resolve();
    const cur=dateInput.value;let i=state.datePos.has(cur)?state.datePos.get(cur):-1;
    if(i<0){i=dates.findIndex(x=>x>=cur);if(i<0)i=dates.length-1;if(n<0&&dates[i]>cur)i--;}
    i=(i+n+dates.length)%dates.length;return setDate(parseDate(dates[i]));
  }
  function closestDateInMonth(month,preferredDay){const dates=state.monthDates.get(month)||[];if(!dates.length)return null;let best=dates[0],diff=Infinity;for(const token of dates){const d=Math.abs(Number(token.slice(8,10))-preferredDay);if(d<diff){best=token;diff=d;}}return best;}
  function realMonthStep(n){
    const months=state.availableMonths;if(!months.length)return Promise.resolve();
    const cur=parseDate(dateInput.value),curKey=monthKey(cur),preferredDay=cur.getDate();let i=months.indexOf(curKey);
    if(i<0){i=months.findIndex(m=>m>curKey);if(i<0)i=months.length-1;if(n<0)i=Math.max(0,i-1);}
    i=(i+n+months.length)%months.length;const token=closestDateInMonth(months[i],preferredDay)||state.monthDates.get(months[i])?.[0];
    return token?setDate(parseDate(token)):Promise.resolve();
  }
  function sliderDate(v){if(!state.availableDates.length)return Promise.resolve();const i=Math.max(0,Math.min(state.availableDates.length-1,Number(v)));return setDate(parseDate(state.availableDates[i]));}

  async function json(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(`${r.status} ${url}`);return r.json();}
  async function firstJson(urls){for(const u of urls){try{return await json(u);}catch(_){}}return null;}
  function isNativeDaily(d){return d?.network?.type==='glofas_lisflood_v4'||d?.format==='pulso-v8-f32';}

  function clampLat(v){return Math.max(-85.05112878,Math.min(85.05112878,v));}
  function worldSize(z){return TILE*(2**z);}
  function project(lon,lat,z=state.zoom){const size=worldSize(z),cl=clampLat(lat),s=Math.sin(cl*Math.PI/180);return{x:(lon+180)/360*size,y:(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*size};}
  function unproject(x,y,z=state.zoom){const size=worldSize(z),lon=x/size*360-180,n=Math.PI-2*Math.PI*y/size,lat=180/Math.PI*Math.atan(Math.sinh(n));return{lon,lat};}
  function viewport(){return{w:Math.max(1,mapEl.clientWidth),h:Math.max(1,mapEl.clientHeight)};}
  function mobileRailWidth(){return window.matchMedia('(max-width:720px)').matches?108:0;}
  function topLeftFor(z=state.zoom,center=state.center){const {w,h}=viewport(),c=project(center.lon,center.lat,z),rail=mobileRailWidth(),cx=(w-rail)/2;return{x:c.x-cx,y:c.y-h/2};}
  function topLeft(){return topLeftFor(state.zoom,state.center);}
  function screen(lon,lat){const p=project(lon,lat),tl=topLeft();return{x:p.x-tl.x,y:p.y-tl.y};}
  function geoAtScreenLocal(x,y,z=state.zoom,center=state.center){const tl=topLeftFor(z,center);return unproject(tl.x+x,tl.y+y,z);}
  function centerForAnchor(anchor,x,y,z){const {w,h}=viewport(),rail=mobileRailWidth(),cx=(w-rail)/2,cy=h/2,a=project(anchor.lon,anchor.lat,z);return unproject(a.x+cx-x,a.y+cy-y,z);}
  function setZoomAt(nextZoom,x,y,anchor=null){const nz=Math.max(4,Math.min(12,nextZoom));if(!Number.isFinite(nz))return;const a=anchor||geoAtScreenLocal(x,y,state.zoom,state.center);state.zoom=nz;state.center=centerForAnchor(a,x,y,nz);scheduleRender();}
  function tileUrl(t,z,x,y){return t.replace('{z}',z).replace('{x}',x).replace('{y}',y);}
  function renderTiles(){
    const base=BASES[state.baseKey]||BASES.hillshade;tileStack.replaceChildren();attr.textContent=base.attribution;state.tileLoads=0;state.tileErrors=0;
    if(state.tileFailTimer){clearTimeout(state.tileFailTimer);state.tileFailTimer=null;}mapEl.classList.remove('tiles-failed');mapFallback.hidden=true;
    const {w,h}=viewport(),tl=topLeft(),n=2**state.zoom,minX=Math.floor(tl.x/TILE)-1,maxX=Math.floor((tl.x+w)/TILE)+1,minY=Math.max(0,Math.floor(tl.y/TILE)-1),maxY=Math.min(n-1,Math.floor((tl.y+h)/TILE)+1);
    base.templates.forEach((template,li)=>{const pane=document.createElement('div');pane.className='tile-pane';pane.style.zIndex=String(10+li);for(let tx=minX;tx<=maxX;tx++){const wx=((tx%n)+n)%n;for(let ty=minY;ty<=maxY;ty++){const im=new Image();im.className='map-tile';im.alt='';im.draggable=false;im.style.left=`${tx*TILE-tl.x}px`;im.style.top=`${ty*TILE-tl.y}px`;im.src=tileUrl(template,state.zoom,wx,ty);im.onload=()=>{state.tileLoads++;mapEl.classList.remove('tiles-failed');mapFallback.hidden=true;};im.onerror=()=>{state.tileErrors++;if(!state.tileFailTimer)state.tileFailTimer=setTimeout(()=>{if(state.tileLoads===0&&state.tileErrors>4){mapEl.classList.add('tiles-failed');mapFallback.hidden=false;}},1000);};pane.appendChild(im);}}tileStack.appendChild(pane);});
  }

  function eachLine(geom,cb){if(!geom)return;if(geom.type==='LineString')cb(geom.coordinates);else if(geom.type==='MultiLineString')geom.coordinates.forEach(cb);else if(geom.type==='Polygon')geom.coordinates.forEach(cb);else if(geom.type==='MultiPolygon')geom.coordinates.flat().forEach(cb);}
  function featureAnchor(feature){let sx=0,sy=0,n=0;eachLine(feature?.geometry,coords=>{for(const c of coords){if(Array.isArray(c)&&Number.isFinite(c[0])&&Number.isFinite(c[1])){sx+=c[0];sy+=c[1];n++;}}});return n?{lon:sx/n,lat:sy/n}:null;}
  function buildPinGlofasMapping(){
    if(!state.pinRivers?.features?.length||!state.glofasRivers?.features?.length){state.pinToGlofas=null;return;}
    const cell=.25,bins=new Map(),gpoints=state.glofasRivers.features.map(featureAnchor);
    const key=(lon,lat)=>`${Math.floor((lon+180)/cell)},${Math.floor((lat+90)/cell)}`;
    gpoints.forEach((p,i)=>{if(!p)return;const k=key(p.lon,p.lat);if(!bins.has(k))bins.set(k,[]);bins.get(k).push(i);});
    const out=new Int32Array(state.pinRivers.features.length);out.fill(-1);
    state.pinRivers.features.forEach((f,pi)=>{
      const p=featureAnchor(f);if(!p)return;const bx=Math.floor((p.lon+180)/cell),by=Math.floor((p.lat+90)/cell);let best=-1,bestD=Infinity;
      for(let ring=0;ring<=6&&best<0;ring++){
        for(let dx=-ring;dx<=ring;dx++)for(let dy=-ring;dy<=ring;dy++){
          if(ring&&Math.max(Math.abs(dx),Math.abs(dy))!==ring)continue;const arr=bins.get(`${bx+dx},${by+dy}`);if(!arr)continue;
          for(const gi of arr){const g=gpoints[gi];const cx=Math.cos(p.lat*Math.PI/180),dd=((g.lon-p.lon)*cx)**2+(g.lat-p.lat)**2;if(dd<bestD){bestD=dd;best=gi;}}
        }
      }
      if(best<0){gpoints.forEach((g,gi)=>{if(!g)return;const cx=Math.cos(p.lat*Math.PI/180),dd=((g.lon-p.lon)*cx)**2+(g.lat-p.lat)**2;if(dd<bestD){bestD=dd;best=gi;}});}
      out[pi]=best;
    });
    state.pinToGlofas=out;
  }

  function tempColor(t){const x=Math.max(0,Math.min(1,(t-16)/16)),stops=[[36,116,167],[53,160,176],[83,190,143],[235,198,73],[216,105,54]],s=x*(stops.length-1),i=Math.min(stops.length-2,Math.floor(s)),f=s-i,a=stops[i],b=stops[i+1];return`rgb(${Math.round(a[0]+(b[0]-a[0])*f)},${Math.round(a[1]+(b[1]-a[1])*f)},${Math.round(a[2]+(b[2]-a[2])*f)})`;}
  function flowWidth(q){if(!Number.isFinite(q)||q<=0)return .34;return Math.max(.72,Math.min(11.5,.42+2.15*Math.log10(q+1)));}
  function featureId(feature,index){const p=feature?.properties||{};return String(p.glofas_id??p.id??p.OBJECTID??index);}
  function glofasDischarge(gi){
    if(!state.daily||gi<0)return null;
    if(state.daily.format==='pulso-v8-f32'){const q=Number(state.daily.values?.[gi]);return Number.isFinite(q)&&q>=0?q:null;}
    const id=featureId(state.glofasRivers?.features?.[gi],gi),rows=state.daily.segments||{};let hit=Array.isArray(rows)?rows.find(r=>String(r.id??r.glofas_id??r.segment_id)===id):rows[id];
    if(hit==null)return null;const q=Array.isArray(hit)?Number(hit[0]):Number(hit.discharge_m3s??hit.discharge??hit.q);return Number.isFinite(q)&&q>=0?q:null;
  }
  function pinDischarge(index){if(!state.daily||!state.pinToGlofas)return null;return glofasDischarge(state.pinToGlofas[index]);}
  function pinTemperature(index,date){if(!state.tempClimate?.months)return null;const month=String(date.getMonth()+1).padStart(2,'0'),arr=state.tempClimate.months[month];if(!Array.isArray(arr))return null;const t=Number(arr[index]);return Number.isFinite(t)?t:null;}
  function temperatureSummary(date){if(!state.tempClimate?.summary)return null;const m=String(date.getMonth()+1).padStart(2,'0'),s=state.tempClimate.summary[m]||{};const v=Number(s.median_c??s.mean_c);return Number.isFinite(v)?v:null;}

  function drawPath(coords,style){if(!coords?.length)return;ctx.beginPath();let started=false;for(const c of coords){const p=screen(c[0],c[1]);if(!started){ctx.moveTo(p.x,p.y);started=true;}else ctx.lineTo(p.x,p.y);}ctx.strokeStyle=style.color;ctx.lineWidth=style.width;ctx.globalAlpha=style.alpha??1;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke();ctx.globalAlpha=1;}
  function renderCanvas(){
    const {w,h}=viewport();canvas.width=Math.round(w*state.dpr);canvas.height=Math.round(h*state.dpr);canvas.style.width=`${w}px`;canvas.style.height=`${h}px`;ctx.setTransform(state.dpr,0,0,state.dpr,0,0);ctx.clearRect(0,0,w,h);
    const date=parseDate(dateInput.value);
    if(state.riverOn&&state.pinRivers?.features?.length){
      state.pinRivers.features.forEach((f,i)=>{
        const q=pinDischarge(i),t=pinTemperature(i,date),width=state.flowOn?flowWidth(q):1.15,color=(state.tempOn&&Number.isFinite(t))?tempColor(t):'#1388ad';
        const alpha=Number.isFinite(q)&&q>0?.93:.30;eachLine(f.geometry,c=>drawPath(c,{color,width,alpha}));
      });
    }
    if(state.boundaryOn&&state.boundary?.features){for(const f of state.boundary.features)eachLine(f.geometry,c=>drawPath(c,{color:'#173c52',width:2.1,alpha:.9}));}
  }
  function renderMap(){renderTiles();renderCanvas();}
  function scheduleRender(){if(state.renderQueued)return;state.renderQueued=true;requestAnimationFrame(()=>{state.renderQueued=false;renderMap();});}
  function fitMS(){const {w,h}=viewport(),mobile=w<=720,rail=mobile?mobileRailWidth():0,usableW=Math.max(160,w-rail),padX=mobile?12:44,padY=mobile?14:44;let z=4;for(let k=10;k>=4;k--){const a=project(MS_BOUNDS.minLon,MS_BOUNDS.maxLat,k),b=project(MS_BOUNDS.maxLon,MS_BOUNDS.minLat,k);if(Math.abs(b.x-a.x)<usableW-padX*2&&Math.abs(b.y-a.y)<h-padY*2){z=k;break;}}state.zoom=z;state.center={...MS_CENTER};scheduleRender();}
  function zoom(delta){const {w,h}=viewport(),rail=mobileRailWidth();setZoomAt(state.zoom+delta,(w-rail)/2,h/2);}

  function locale(){return uiLang==='es'?'es-ES':'pt-BR';}
  function formatNumber(v,digits=0,min=digits){return new Intl.NumberFormat(locale(),{minimumFractionDigits:min,maximumFractionDigits:digits}).format(v);}
  function nf0(v){return formatNumber(v,0,0);}
  function nf1(v){return formatNumber(v,1,1);}
  function nf2(v){return formatNumber(v,2,2);}
  function nf3(v){return formatNumber(v,3,3);}
  function numberText(v){const n=Number(v);if(!Number.isFinite(n))return'—';if(n>=1000)return nf0(Math.round(n));if(n>=10)return nf1(n);if(n>=1)return nf2(n);return nf3(n);}

  async function loadMonthV8(key){
    if(state.monthCache.has(key))return state.monthCache.get(key);const info=state.archiveIndex?.months?.[key];if(!info)return null;
    const promise=(async()=>{const metaUrl=`./data/pulse-v8/${info.meta}`,binUrl=`./data/pulse-v8/${info.binary}`;const [meta,binResp]=await Promise.all([json(metaUrl),fetch(binUrl,{cache:'no-store'})]);if(!binResp.ok)throw new Error(`${binResp.status} ${binUrl}`);const buffer=await binResp.arrayBuffer(),expected=Number(meta.day_count)*Number(meta.segment_count)*4;if(buffer.byteLength!==expected)throw new Error(`binário ${key} inválido: ${buffer.byteLength} B; esperado ${expected} B`);return{meta,values:new Float32Array(buffer)};})();
    state.monthCache.set(key,promise);try{return await promise;}catch(err){state.monthCache.delete(key);throw err;}
  }
  async function loadDailyV8(date){
    if(!state.archiveIndex)return null;const token=isoDate(date),key=token.slice(0,7),info=state.archiveIndex.months?.[key];if(!info||!info.dates?.includes(token))return null;
    const month=await loadMonthV8(key),meta=month.meta,pos=meta.dates.indexOf(token);if(pos<0)return null;const n=Number(meta.segment_count),start=pos*n,end=start+n;if(state.glofasRivers?.features?.length&&state.glofasRivers.features.length!==n)throw new Error(`rede GloFAS=${state.glofasRivers.features.length}; arquivo V8=${n}`);
    return{format:'pulso-v8-f32',date:token,network:{type:'glofas_lisflood_v4',feature_count:n,threshold_upstream_area_km2:250},values:month.values.subarray(start,end),summary:meta.summaries?.[pos]||{},sourceMonth:key};
  }
  async function loadDailyV7(date){try{const d=await json(`./data/pulse/${isoDate(date)}.json`);return isNativeDaily(d)?d:null;}catch(_){return null;}}
  async function loadDaily(date){try{const d=await loadDailyV8(date);if(d)return d;}catch(err){console.error('V8',err);mapNote.textContent=L(`Falha ao ler o bloco V8 ${monthKey(date)}: ${err.message}`,`Fallo al leer el bloque V8 ${monthKey(date)}: ${err.message}`);}return loadDailyV7(date);}

  function completeDailySummary(base,daily){
    const out={...(base||{})};
    if(daily?.format!=='pulso-v8-f32'||!daily.values)return out;
    const vals=[];let max=-Infinity,positive=0,valid=0,zeros=0;
    for(const raw of daily.values){const v=Number(raw);if(!Number.isFinite(v)||v<0)continue;valid++;if(v>0)positive++;else zeros++;if(v>max)max=v;if(!Number.isFinite(Number(out.discharge_p90_m3s)))vals.push(v);}
    if(!Number.isFinite(Number(out.segments_with_discharge)))out.segments_with_discharge=valid;
    if(!Number.isFinite(Number(out.segments_positive)))out.segments_positive=positive;
    if(!Number.isFinite(Number(out.zero_fraction)))out.zero_fraction=valid?zeros/valid:null;
    if(!Number.isFinite(Number(out.discharge_max_m3s)))out.discharge_max_m3s=Number.isFinite(max)?max:null;
    if(!Number.isFinite(Number(out.discharge_p90_m3s))&&vals.length){vals.sort((a,b)=>a-b);const k=(vals.length-1)*.9,i=Math.floor(k),f=k-i;out.discharge_p90_m3s=vals[i]+(vals[Math.min(i+1,vals.length-1)]-vals[i])*f;}
    return out;
  }

  async function loadOutflow(){
    try{
      const d=await json('./data/outflow-ms.json');
      if(Array.isArray(d?.dates)&&Array.isArray(d?.values_m3s)&&d.dates.length===d.values_m3s.length){
        state.outflow=d;state.outflowDatePos=new Map(d.dates.map((x,i)=>[x,i]));
        if(outflowHint)outflowHint.textContent=L('Toque ou arraste para escolher um dia','Toca o arrastra para elegir un día');
        return;
      }
    }catch(_){/* prepared locally; optional until script is run */}
    state.outflow=null;state.outflowDatePos=new Map();
    if(outflowHint)outflowHint.textContent=L('Série de saída ainda não publicada','Serie de salida todavía no publicada');
  }
  function outflowValueFor(token){if(!state.outflow)return null;const i=state.outflowDatePos.get(token);if(!Number.isInteger(i))return null;const v=Number(state.outflow.values_m3s[i]);return Number.isFinite(v)&&v>=0?v:null;}
  function yearOutflow(year){
    if(!state.outflow)return[];const out=[];for(let i=0;i<state.outflow.dates.length;i++){const d=state.outflow.dates[i];if(Number(d.slice(0,4))!==year)continue;const v=Number(state.outflow.values_m3s[i]);if(Number.isFinite(v)&&v>=0)out.push({date:d,value:v,index:i});}return out;
  }
  function drawOutflowChart(date){
    if(!outflowChart||!outflowChartWrap)return;const rect=outflowChartWrap.getBoundingClientRect(),w=Math.max(2,Math.round(rect.width)),h=Math.max(2,Math.round(rect.height)),dpr=Math.max(1,Math.min(2,devicePixelRatio||1));outflowChart.width=Math.round(w*dpr);outflowChart.height=Math.round(h*dpr);const c=outflowChart.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);
    const year=date.getFullYear(),rows=yearOutflow(year);state.outflowYearData=rows;if(outflowYearLabel)outflowYearLabel.textContent=String(year);
    if(!rows.length){c.fillStyle='rgba(210,235,233,.62)';c.font='600 11px Inter, Segoe UI, Arial';c.fillText(L('Série de saída indisponível','Serie de salida no disponible'),8,h/2);if(outflowPeakLabel)outflowPeakLabel.textContent=L('pico anual —','pico anual —');return;}
    const pad={l:4,r:4,t:4,b:4},iw=w-pad.l-pad.r,ih=h-pad.t-pad.b,max=Math.max(...rows.map(r=>r.value),1),x=i=>pad.l+(rows.length===1?0:i/(rows.length-1))*iw,y=v=>pad.t+(1-v/max)*ih;
    c.beginPath();rows.forEach((r,i)=>{const px=x(i),py=y(r.value);if(i===0)c.moveTo(px,py);else c.lineTo(px,py);});c.strokeStyle='#69c4c7';c.lineWidth=1.5;c.lineJoin='round';c.lineCap='round';c.stroke();
    c.lineTo(x(rows.length-1),h-pad.b);c.lineTo(x(0),h-pad.b);c.closePath();const g=c.createLinearGradient(0,pad.t,0,h);g.addColorStop(0,'rgba(82,190,194,.24)');g.addColorStop(1,'rgba(82,190,194,.02)');c.fillStyle=g;c.fill();
    const token=isoDate(date);let pos=rows.findIndex(r=>r.date===token);if(pos<0)pos=Math.max(0,Math.min(rows.length-1,Math.round((date-new Date(year,0,1,12))/(86400000)/(365+(new Date(year,1,29).getMonth()===1?1:0))*rows.length)));const marker=rows[pos];const mx=x(pos),my=y(marker.value);c.beginPath();c.moveTo(mx,pad.t);c.lineTo(mx,h-pad.b);c.strokeStyle='rgba(230,245,242,.72)';c.lineWidth=1;c.stroke();c.beginPath();c.arc(mx,my,3.2,0,Math.PI*2);c.fillStyle='#eef9f7';c.fill();c.strokeStyle='#173d46';c.lineWidth=1.2;c.stroke();
    let peak=rows[0];for(const r of rows)if(r.value>peak.value)peak=r;if(outflowPeakLabel)outflowPeakLabel.textContent=L(`pico ${fmtDate(parseDate(peak.date))} · ${numberText(peak.value)} m³/s`,`pico ${fmtDate(parseDate(peak.date))} · ${numberText(peak.value)} m³/s`);
  }
  function updateOutflow(date){const v=outflowValueFor(isoDate(date));if(outflowValue)outflowValue.textContent=v==null?'—':numberText(v);if(outflowSub)outflowSub.textContent=state.outflow?L('soma dos cruzamentos de saída · GloFAS v4','suma de los cruces de salida · GloFAS v4'):L('série de saída não publicada','serie de salida no publicada');drawOutflowChart(date);}
  let outflowSelectPending=null;
  function selectOutflowAtEvent(e){if(!state.outflowYearData.length||!outflowChartWrap)return;const r=outflowChartWrap.getBoundingClientRect(),x=Math.max(0,Math.min(r.width,e.clientX-r.left)),i=Math.max(0,Math.min(state.outflowYearData.length-1,Math.round(x/Math.max(1,r.width)*(state.outflowYearData.length-1)))),token=state.outflowYearData[i]?.date;if(!token)return;if(outflowSelectPending)clearTimeout(outflowSelectPending);outflowSelectPending=setTimeout(()=>{stopPlayback();setDate(parseDate(token));},45);}

  async function updateForDate(date){
    const serial=++state.requestSerial,token=isoDate(date);state.daily=await loadDaily(date);if(serial!==state.requestSerial)return;
    const realPulse=isNativeDaily(state.daily),temp=temperatureSummary(date),s=completeDailySummary(state.daily?.summary||{},state.daily),p90=Number(s.discharge_p90_m3s),max=Number(s.discharge_max_m3s),active=Number(s.segments_positive),total=Number(s.segments_with_discharge),zero=Number(s.zero_fraction);
    modePill.textContent=L('DADOS REAIS · GLOFAS V4','DATOS REALES · GLOFAS V4');modePill.classList.add('status-pill--real');geometryPill.textContent=L('RIOS PIN / IMASUL','RÍOS PIN / IMASUL');
    if(realPulse){
      dischargeLabel.textContent='P90 GLOFAS';dischargeValue.textContent=numberText(p90);dischargeUnit.textContent=L('m³/s · descarga modelada','m³/s · caudal modelado');const scale=Number.isFinite(p90)?Math.max(3,Math.min(100,Math.log10(p90+1)/4*100)):0;dischargeBar.style.width=`${scale}%`;
      if(mapFlowValue)mapFlowValue.textContent=numberText(p90);if(mapFlowBar)mapFlowBar.style.width=`${scale}%`;if(mapMaxValue)mapMaxValue.textContent=numberText(max);if(mapActiveValue)mapActiveValue.textContent=Number.isFinite(active)?nf0(active):'—';
      realStats.hidden=false;p90Value.textContent=numberText(p90);maxValue.textContent=numberText(max);activeValue.textContent=Number.isFinite(active)?nf0(active):'—';
      legendThinText.textContent=L('menor descarga','menor caudal');legendThickText.textContent=L('maior descarga','mayor caudal');
      const src=state.daily.format==='pulso-v8-f32'?`V8 · ${L('bloco','bloque')} ${state.daily.sourceMonth}`:L('arquivo diário V7','archivo diario V7');mapNote.textContent=uiLang==='es'?`${token} · GloFAS v4 ${src}. El grosor usa escala logarítmica para hacer visibles los cambios; la geometría mostrada es PIN MS / IMASUL.`:`${token} · GloFAS v4 ${src}. A espessura usa escala logarítmica para tornar as mudanças visíveis; a geometria mostrada é PIN MS / IMASUL.`;
    }else{
      dischargeLabel.textContent=L('DESCARGA GLOFAS','CAUDAL GLOFAS');dischargeValue.textContent='—';dischargeUnit.textContent=L('sem dado nesta data','sin dato en esta fecha');dischargeBar.style.width='0%';if(mapFlowValue)mapFlowValue.textContent='—';if(mapFlowBar)mapFlowBar.style.width='0%';if(mapMaxValue)mapMaxValue.textContent='—';if(mapActiveValue)mapActiveValue.textContent='—';realStats.hidden=true;mapNote.textContent=uiLang==='es'?`No hay caudal GloFAS procesado para ${token}. No se ha estimado ningún valor.`:`Não há descarga GloFAS processada para ${token}. Nenhum valor foi estimado.`;
    }
    if(Number.isFinite(temp)){
      tempValue.textContent=`${nf1(temp)}°`;tempUnit.textContent=L('°C · climatologia mensal DynQual 1980–2019','°C · climatología mensual DynQual 1980–2019');if(mapTempValue)mapTempValue.textContent=`${nf1(temp)}°C`;if(mapTempCaption)mapTempCaption.textContent=L('climatologia mensal DynQual','climatología mensual DynQual');temperatureBar.classList.remove('is-unavailable');tempLegend.hidden=false;
    }else{
      tempValue.textContent='—';tempUnit.textContent=L('execute PREPARAR_TEMPERATURA_DYNQUAL.cmd','ejecute PREPARAR_TEMPERATURA_DYNQUAL.cmd');if(mapTempValue)mapTempValue.textContent='—';if(mapTempCaption)mapTempCaption.textContent=L('temperatura ainda não preparada','temperatura aún no preparada');temperatureBar.classList.add('is-unavailable');tempLegend.hidden=true;
    }
    timelineMode.textContent=state.archiveIndex?L(`consulta diária · reprodução mensal · ${nf0(state.archiveIndex.date_count)} dias`,`consulta diaria · reproducción mensual · ${nf0(state.archiveIndex.date_count)} días`):L('consulta diária · reprodução mensal','consulta diaria · reproducción mensual');
    scienceNotice.classList.remove('notice--test');scienceNotice.querySelector('strong').textContent=L('Leitura integrada','Lectura integrada');scienceNotice.querySelector('p').textContent=uiLang==='es'?`Ríos visibles: PIN MS / IMASUL. Grosor: caudal GloFAS v4 transferido cartográficamente desde la red LISFLOOD. Color: ${Number.isFinite(temp)?'climatología mensual DynQual 1980–2019':'temperatura aún no preparada'}. ${Number.isFinite(total)?nf0(total):'—'} celdas fluviales GloFAS en el resumen del día${Number.isFinite(zero)?`, ${nf1(zero*100)}% con caudal cero`:''}.`:`Rios visíveis: PIN MS / IMASUL. Espessura: descarga GloFAS v4 transferida cartograficamente da rede LISFLOOD. Cor: ${Number.isFinite(temp)?'climatologia mensal DynQual 1980–2019':'temperatura ainda não preparada'}. ${Number.isFinite(total)?nf0(total):'—'} células fluviais GloFAS no resumo do dia${Number.isFinite(zero)?`, ${nf1(zero*100)}% com descarga zero`:''}.`;
    updateOutflow(date);updateStatus();$$('#quickDates button').forEach(b=>b.classList.toggle('active',b.dataset.date===token));scheduleRender();
  }

  function updateStatus(){
    geometryStatus.textContent=state.pinRivers?.features?.length?'PIN MS / IMASUL':L('hidrografia ausente','hidrografía ausente');pulseStatus.textContent=state.archiveIndex?.date_count?`GloFAS v4 · ${nf0(state.archiveIndex.date_count)} ${L('dias','días')}`:L('GloFAS não preparado','GloFAS no preparado');
    riverLayerCaption.textContent=state.pinRivers?.features?.length?L('Geometria original · valores GloFAS transferidos','Geometría original · valores GloFAS transferidos'):L('Arquivo rivers.geojson não encontrado','Archivo rivers.geojson no encontrado');boundaryLayerCaption.textContent=state.boundary?.features?.length?L('Limite local carregado','Límite local cargado'):L('Limite não encontrado','Límite no encontrado');
  }

  function buildDatePos(){state.datePos=new Map(state.availableDates.map((d,i)=>[d,i]));state.monthDates=new Map();for(const d of state.availableDates){const k=d.slice(0,7);if(!state.monthDates.has(k))state.monthDates.set(k,[]);state.monthDates.get(k).push(d);}state.availableMonths=[...state.monthDates.keys()].sort();}
  async function loadDateIndex(){
    try{const idx=await json('./data/pulse-v8/index.json');if(idx?.format==='pulso-v8-f32'&&idx?.network==='glofas_lisflood_v4'&&Array.isArray(idx.dates)&&idx.dates.length){state.archiveIndex=idx;state.availableDates=idx.dates.slice().sort();buildDatePos();dateInput.min=idx.start||'';dateInput.max=idx.end||'';return;}}catch(_){state.archiveIndex=null;}
    try{const idx=await json('./data/pulse/index.json');if(idx?.network==='glofas_lisflood_v4'&&Array.isArray(idx.dates)){state.availableDates=idx.dates.slice().sort();buildDatePos();}}catch(_){state.availableDates=[];buildDatePos();}
  }
  async function probeDates(){
    const ready=new Set(state.availableDates);QUICK_DATES.forEach(d=>{const ok=ready.has(d),b=$(`.quick-dates button[data-date="${d}"]`);if(b)b.classList.toggle('real-ready',ok);});
    if(realFilesStatus)realFilesStatus.textContent=state.archiveIndex?.date_count?`${nf0(state.archiveIndex.date_count)} ${L('dias','días')} · ${state.archiveIndex.month_count} ${L('meses','meses')}`:`${state.availableDates.length} ${L('datas disponíveis','fechas disponibles')}`;
  }
  async function loadTemperature(){state.tempClimate=await firstJson(['./data/temperature-climatology.json']);updateStatus();}
  async function loadGeometry(){
    const [realBoundary,realPin,native]=await Promise.all([firstJson(['./data/boundary.geojson']),firstJson(['./data/rivers.geojson']),firstJson(['./data/glofas_network.geojson'])]);
    state.boundary=realBoundary;state.pinRivers=realPin;state.glofasRivers=native;if(!state.pinRivers?.features?.length)throw new Error(L('docs/data/rivers.geojson não encontrado','docs/data/rivers.geojson no encontrado'));if(!state.glofasRivers?.features?.length)throw new Error(L('docs/data/glofas_network.geojson não encontrado','docs/data/glofas_network.geojson no encontrado'));buildPinGlofasMapping();updateStatus();fitMS();
  }

  function applyLanguage(){
    document.documentElement.lang=uiLang==='es'?'es':'pt-BR';
    $$('[data-pt][data-es]').forEach(el=>{el.textContent=uiLang==='es'?el.dataset.es:el.dataset.pt;});
    $$('[data-lang-block]').forEach(el=>{el.hidden=el.dataset.langBlock!==uiLang;});
    if(langPt)langPt.classList.toggle('active',uiLang==='pt');if(langEs)langEs.classList.toggle('active',uiLang==='es');
    const current=dateInput.value?parseDate(dateInput.value):null;if(current){dateLabel.textContent=fmtDate(current);sideDateLabel.textContent=fmtDate(current);}
    updatePlayButton();updateStatus();online();
    if(current&&state.availableDates.length)updateForDate(current);else if(current)updateOutflow(current);
  }
  function toggleLanguage(){uiLang=uiLang==='pt'?'es':'pt';localStorage.setItem('pulso-ms-lang',uiLang);applyLanguage();}

  function sheetTitle(name){const labels={layers:[L('Camadas','Capas')],data:[L('Dados e fontes','Datos y fuentes')],help:[L('Como funciona','Cómo funciona')]};return labels[name]?.[0]||'Pulso';}
  function closeMobileSheet(){if(!window.matchMedia('(max-width:720px)').matches)return;if(appShell){appShell.dataset.sheetOpen='false';appShell.dataset.mobileTab='pulse';}if(mobileSheetBackdrop)mobileSheetBackdrop.hidden=true;$$('.mobile-nav-item').forEach(b=>b.classList.toggle('active',b.dataset.mobileTab==='pulse'));}
  function setTab(name){
    const mobile=window.matchMedia('(max-width:720px)').matches;if(appShell)appShell.dataset.mobileTab=name;
    $$('.panel-tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));$$('.tab-page').forEach(p=>p.classList.toggle('active',p.dataset.page===name));$$('.mobile-nav-item').forEach(b=>b.classList.toggle('active',b.dataset.mobileTab===name));
    if(mobile){if(name==='pulse'){closeMobileSheet();return;}if(mobileSheetTitle)mobileSheetTitle.textContent=sheetTitle(name);appShell.dataset.sheetOpen='true';if(mobileSheetBackdrop)mobileSheetBackdrop.hidden=false;return;}
  }
  function updatePlayButton(){playBtn.classList.toggle('playing',state.playing);playBtn.querySelector('span').textContent=state.playing?'❚❚':'▶';playBtn.querySelector('em').textContent=state.playing?L('Pausar','Pausar'):L('Reproduzir · mensal','Reproducir · mensual');playBtn.setAttribute('aria-label',state.playing?L('Pausar reprodução mensal','Pausar reproducción mensual'):L('Reproduzir mês a mês','Reproducir mes a mes'));}
  function stopPlayback(){state.playing=false;if(state.timer){clearTimeout(state.timer);state.timer=null;}updatePlayButton();}
  async function playbackTick(){if(!state.playing)return;try{await realMonthStep(1);}finally{if(state.playing)state.timer=setTimeout(playbackTick,1100);}}

  $$('.panel-tab').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));$$('.mobile-nav-item').forEach(b=>b.onclick=()=>{const name=b.dataset.mobileTab;if(window.matchMedia('(max-width:720px)').matches&&name!=='pulse'&&appShell?.dataset.sheetOpen==='true'&&appShell.dataset.mobileTab===name){closeMobileSheet();return;}setTab(name);});
  if(mobileSheetClose)mobileSheetClose.onclick=closeMobileSheet;if(mobileSheetBackdrop)mobileSheetBackdrop.onclick=closeMobileSheet;
  if(mobileSheetHead){mobileSheetHead.addEventListener('pointerdown',e=>{if(!window.matchMedia('(max-width:720px)').matches||e.target===mobileSheetClose)return;state.sheetDrag={id:e.pointerId,startY:e.clientY,dy:0};try{mobileSheetHead.setPointerCapture(e.pointerId);}catch(_){};});mobileSheetHead.addEventListener('pointermove',e=>{if(!state.sheetDrag||state.sheetDrag.id!==e.pointerId)return;const dy=Math.max(0,e.clientY-state.sheetDrag.startY);state.sheetDrag.dy=dy;if(mobileSheet)mobileSheet.style.transform=`translateY(${dy}px)`;});const finishSheet=()=>{if(!state.sheetDrag)return;const close=state.sheetDrag.dy>86;state.sheetDrag=null;if(mobileSheet)mobileSheet.style.transform='';if(close)closeMobileSheet();};mobileSheetHead.addEventListener('pointerup',finishSheet);mobileSheetHead.addEventListener('pointercancel',finishSheet);}
  if(outflowChartWrap){outflowChartWrap.addEventListener('pointerdown',e=>{e.preventDefault();try{outflowChartWrap.setPointerCapture(e.pointerId);}catch(_){};selectOutflowAtEvent(e);},{passive:false});outflowChartWrap.addEventListener('pointermove',e=>{if(outflowChartWrap.hasPointerCapture?.(e.pointerId)){e.preventDefault();selectOutflowAtEvent(e);}},{passive:false});}
  $$('#quickDates button').forEach(b=>b.onclick=()=>{stopPlayback();setDate(parseDate(b.dataset.date));});
  $('#prevDay').onclick=()=>{stopPlayback();realDateStep(-1);};$('#nextDay').onclick=()=>{stopPlayback();realDateStep(1);};
  $('#dateButton').onclick=()=>{stopPlayback();if(dateInput.showPicker)dateInput.showPicker();else dateInput.click();};dateInput.onchange=()=>{stopPlayback();setDate(parseDate(dateInput.value));};daySlider.oninput=()=>{stopPlayback();sliderDate(daySlider.value);};
  $('#zoomInBtn').onclick=()=>zoom(1);$('#zoomOutBtn').onclick=()=>zoom(-1);$('#resetMapBtn').onclick=fitMS;
  $('#riverToggle').onchange=e=>{state.riverOn=e.target.checked;scheduleRender();};$('#boundaryToggle').onchange=e=>{state.boundaryOn=e.target.checked;scheduleRender();};
  const tempToggle=$('#tempToggle');tempToggle.onchange=e=>{state.tempOn=e.target.checked;scheduleRender();};$('#flowToggle').onchange=e=>{state.flowOn=e.target.checked;scheduleRender();};
  $$('input[name=basemap]').forEach(r=>{r.checked=r.value===state.baseKey;r.onchange=()=>{if(r.checked){state.baseKey=r.value;localStorage.setItem('pulso-ms-basemap',r.value);scheduleRender();}};});
  playBtn.onclick=()=>{if(state.playing){stopPlayback();return;}state.playing=true;updatePlayButton();state.timer=setTimeout(playbackTick,500);};

  function localPoint(e){const r=mapEl.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top,clientX:e.clientX,clientY:e.clientY};}
  function pointerPair(){return [...state.mapPointers.values()].slice(0,2);}
  function pairMetrics(a,b){return{mid:{x:(a.x+b.x)/2,y:(a.y+b.y)/2},distance:Math.hypot(a.x-b.x,a.y-b.y)};}
  function startSingleDrag(p){state.dragging=true;state.dragStart={x:p.x,y:p.y};state.centerStart=project(state.center.lon,state.center.lat);state.gesture=null;}
  mapEl.addEventListener('pointerdown',e=>{if(e.pointerType==='touch')e.preventDefault();const p=localPoint(e);try{mapEl.setPointerCapture(e.pointerId);}catch(_){}state.mapPointers.set(e.pointerId,p);state.lastPointerDown={id:e.pointerId,x:p.x,y:p.y,time:Date.now(),type:e.pointerType};if(state.mapPointers.size===1){startSingleDrag(p);}else if(state.mapPointers.size>=2){state.dragging=false;const [a,b]=pointerPair(),m=pairMetrics(a,b);state.gesture={startDistance:Math.max(8,m.distance),startZoom:state.zoom,anchor:geoAtScreenLocal(m.mid.x,m.mid.y),moved:false};}},{passive:false});
  mapEl.addEventListener('pointermove',e=>{if(!state.mapPointers.has(e.pointerId))return;const p=localPoint(e);state.mapPointers.set(e.pointerId,p);if(state.mapPointers.size>=2&&state.gesture){e.preventDefault();const [a,b]=pointerPair(),m=pairMetrics(a,b),ratio=Math.max(.25,Math.min(4,m.distance/state.gesture.startDistance)),target=Math.max(4,Math.min(12,Math.round(state.gesture.startZoom+Math.log2(ratio))));state.zoom=target;state.center=centerForAnchor(state.gesture.anchor,m.mid.x,m.mid.y,target);state.gesture.moved=true;scheduleRender();return;}if(state.dragging&&state.mapPointers.size===1){const dx=p.x-state.dragStart.x,dy=p.y-state.dragStart.y;if(Math.hypot(dx,dy)>4&&state.lastPointerDown)state.lastPointerDown.moved=true;const c=unproject(state.centerStart.x-dx,state.centerStart.y-dy);state.center={lon:c.lon,lat:c.lat};scheduleRender();}},{passive:false});
  function finishPointer(e){const p=state.mapPointers.get(e.pointerId)||localPoint(e);state.mapPointers.delete(e.pointerId);if(state.mapPointers.size===1){startSingleDrag([...state.mapPointers.values()][0]);}else if(state.mapPointers.size===0){state.dragging=false;state.gesture=null;}const d=state.lastPointerDown;if(e.type==='pointerup'&&d&&d.id===e.pointerId&&d.type==='touch'&&!d.moved&&Date.now()-d.time<330){const now=Date.now();if(now-state.lastTapAt<320&&state.lastTapPoint&&Math.hypot(p.x-state.lastTapPoint.x,p.y-state.lastTapPoint.y)<28){setZoomAt(state.zoom+1,p.x,p.y);state.lastTapAt=0;state.lastTapPoint=null;}else{state.lastTapAt=now;state.lastTapPoint={x:p.x,y:p.y};}}}
  mapEl.addEventListener('pointerup',finishPointer);mapEl.addEventListener('pointercancel',finishPointer);mapEl.addEventListener('pointerleave',e=>{if(e.pointerType==='mouse'&&state.mapPointers.has(e.pointerId))finishPointer(e);});mapEl.addEventListener('wheel',e=>{e.preventDefault();const p=localPoint(e);setZoomAt(state.zoom+(e.deltaY<0?1:-1),p.x,p.y);},{passive:false});mapEl.addEventListener('dblclick',e=>{e.preventDefault();const p=localPoint(e);setZoomAt(state.zoom+1,p.x,p.y);});

  function openDialog(dialog){if(dialog&&typeof dialog.showModal==='function'&&!dialog.open)dialog.showModal();}
  if(helpHeaderBtn)helpHeaderBtn.onclick=()=>openDialog(helpDialog);if(infoHeaderBtn)infoHeaderBtn.onclick=()=>openDialog(infoDialog);if(langToggle)langToggle.onclick=toggleLanguage;$$('[data-open-help]').forEach(b=>b.onclick=()=>openDialog(helpDialog));$$('[data-close-dialog]').forEach(b=>b.onclick=()=>b.closest('dialog')?.close());[helpDialog,infoDialog].filter(Boolean).forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close();}));
  function online(){const el=$('#onlineState');el.textContent=navigator.onLine?L('online','en línea'):L('offline','sin conexión');el.style.background=navigator.onLine?'#dcebe3':'#eee0c6';el.style.color=navigator.onLine?'#24664f':'#8a5c22';}window.addEventListener('online',online);window.addEventListener('offline',online);
  let deferred=null;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferred=e;$('#installBtn').hidden=false;});$('#installBtn').onclick=async()=>{if(!deferred)return;deferred.prompt();await deferred.userChoice;deferred=null;$('#installBtn').hidden=true;};
  if('serviceWorker'in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js?v=866').catch(()=>{}));let lastMapWidth=0;new ResizeObserver(()=>{const w=mapEl.clientWidth;if(lastMapWidth&&Math.abs(w-lastMapWidth)>48){fitMS();}else{scheduleRender();}lastMapWidth=w;const d=dateInput.value?parseDate(dateInput.value):null;if(d)drawOutflowChart(d);}).observe(mapEl);if(outflowChartWrap)new ResizeObserver(()=>{const d=dateInput.value?parseDate(dateInput.value):null;if(d)drawOutflowChart(d);}).observe(outflowChartWrap);window.addEventListener('orientationchange',()=>setTimeout(()=>{fitMS();const d=dateInput.value?parseDate(dateInput.value):null;if(d)drawOutflowChart(d);},220));

  async function init(){
    applyLanguage();updatePlayButton();await loadDateIndex();await probeDates();await Promise.all([loadGeometry(),loadTemperature(),loadOutflow()]);
    if(appShell){appShell.dataset.sheetOpen='false';appShell.dataset.mobileTab='pulse';}
    const target=state.availableDates.includes('2025-02-08')?'2025-02-08':state.availableDates[state.availableDates.length-1]||'2025-02-08';await setDate(parseDate(target));
  }
  init().catch(e=>{console.error(e);mapNote.textContent=L(`Falha ao carregar os dados locais: ${e.message}`,`Fallo al cargar los datos locales: ${e.message}`);});
})();
