const tracosPato=[[169,0],[143,10],[156,10],[169,10],[182,10],[195,10],[130,20],[143,20],[156,20],[169,20],[182,20],[195,20],[208,20],[130,30],[143,30],[156,30],[169,30],[182,30],[195,30],[208,30],[221,30],[117,40],[130,40],[143,40],[156,40],[169,40],[182,40],[195,40],[208,40],[221,40],[117,50],[130,50],[143,50],[156,50],[169,50],[182,50],[195,50],[208,50],[221,50],[117,60],[130,60],[143,60],[156,60],[169,60],[182,60],[195,60],[208,60],[221,60],[234,60],[247,60],[117,70],[130,70],[143,70],[156,70],[169,70],[182,70],[195,70],[208,70],[221,70],[234,70],[247,70],[260,70],[117,80],[130,80],[143,80],[156,80],[169,80],[182,80],[195,80],[208,80],[221,80],[234,80],[247,80],[130,90],[143,90],[156,90],[169,90],[182,90],[195,90],[208,90],[221,90],[130,100],[143,100],[156,100],[169,100],[182,100],[195,100],[208,100],[13,110],[26,110],[104,110],[117,110],[130,110],[143,110],[156,110],[169,110],[182,110],[195,110],[208,110],[13,120],[26,120],[39,120],[52,120],[65,120],[78,120],[91,120],[104,120],[117,120],[130,120],[143,120],[156,120],[169,120],[182,120],[195,120],[208,120],[221,120],[13,130],[26,130],[39,130],[52,130],[65,130],[78,130],[91,130],[104,130],[117,130],[130,130],[143,130],[156,130],[169,130],[182,130],[195,130],[208,130],[221,130],[0,140],[13,140],[26,140],[39,140],[52,140],[65,140],[78,140],[91,140],[104,140],[117,140],[130,140],[143,140],[156,140],[169,140],[182,140],[195,140],[208,140],[221,140],[234,140],[13,150],[26,150],[39,150],[52,150],[65,150],[78,150],[91,150],[104,150],[117,150],[130,150],[143,150],[156,150],[169,150],[182,150],[195,150],[208,150],[221,150],[234,150],[13,160],[26,160],[39,160],[52,160],[65,160],[78,160],[91,160],[104,160],[117,160],[130,160],[143,160],[156,160],[169,160],[182,160],[195,160],[208,160],[221,160],[234,160],[13,170],[26,170],[39,170],[52,170],[65,170],[78,170],[91,170],[104,170],[117,170],[130,170],[143,170],[156,170],[169,170],[182,170],[195,170],[208,170],[221,170],[234,170],[13,180],[26,180],[39,180],[52,180],[65,180],[78,180],[91,180],[104,180],[117,180],[130,180],[143,180],[156,180],[169,180],[182,180],[195,180],[208,180],[221,180],[234,180],[26,190],[39,190],[52,190],[65,190],[78,190],[91,190],[104,190],[117,190],[130,190],[143,190],[156,190],[169,190],[182,190],[195,190],[208,190],[221,190],[234,190],[26,200],[39,200],[52,200],[65,200],[78,200],[91,200],[104,200],[117,200],[130,200],[143,200],[156,200],[169,200],[182,200],[195,200],[208,200],[221,200],[39,210],[52,210],[65,210],[78,210],[91,210],[104,210],[117,210],[130,210],[143,210],[156,210],[169,210],[182,210],[195,210],[208,210],[221,210],[52,220],[65,220],[78,220],[91,220],[104,220],[117,220],[130,220],[143,220],[156,220],[169,220],[182,220],[195,220],[208,220],[78,230],[91,230],[104,230],[117,230],[130,230],[143,230],[156,230],[169,230],[182,230],[195,230]];

function cssVar(name){
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function drawPato(canvas, color){
  if(!canvas){ return; }
  color=color||'var(--brand)';
  var cssSize=parseFloat(getComputedStyle(canvas).width)||canvas.clientWidth||Number(canvas.getAttribute('width'))||260;
  var dpr=window.devicePixelRatio||1;
  canvas.width=Math.round(cssSize*dpr);
  canvas.height=Math.round(cssSize*dpr);
  var ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,cssSize,cssSize);
  var base=cssSize/260;
  var SC=0.88, OX=(260-263*SC)/2, OY=(260-240*SC)/2;
  var minGap=cssSize<70?2.4:1;
  var dashW=cssSize<70?2:Math.max(2,6*base);
  var lineW=cssSize<70?1.8:Math.max(1.8,2.4*base);
  var used={};
  tracosPato.forEach(function(p){
    var x=(p[0]*SC+OX)*base, y=(p[1]*SC+OY)*base;
    var key=Math.round(x/minGap)+','+Math.round(y/minGap);
    if(used[key]){ return; }
    used[key]=true;
    strokePatoDash(ctx,x,y,dashW,1,1,lineW);
  });
}

function drawPatoSolid(canvas, color){
  if(!canvas){ return; }
  var cssSize=parseFloat(getComputedStyle(canvas).width)||canvas.clientWidth||Number(canvas.getAttribute('width'))||260;
  var dpr=window.devicePixelRatio||1;
  canvas.width=Math.round(cssSize*dpr);
  canvas.height=Math.round(cssSize*dpr);
  var ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,cssSize,cssSize);
  var base=cssSize/260;
  var SC=0.88, OX=(260-263*SC)/2, OY=(260-240*SC)/2;
  var rowH=15*SC*base;
  var padX=8*SC*base;
  var rows={};
  ctx.fillStyle=color||cssVar('--brand');
  tracosPato.forEach(function(p){
    rows[p[1]]=rows[p[1]]||[];
    rows[p[1]].push(p[0]);
  });
  Object.keys(rows).forEach(function(y){
    rows[y].sort(function(a,b){ return a-b; });
    var runStart=rows[y][0], last=rows[y][0];
    function fillRun(){
      var x1=(runStart*SC+OX)*base-padX;
      var x2=(last*SC+OX)*base+padX;
      var yy=(Number(y)*SC+OY)*base-rowH/2;
      ctx.fillRect(x1, yy, x2-x1, rowH);
    }
    for(var i=1;i<rows[y].length;i++){
      if(rows[y][i]-last>16){
        fillRun();
        runStart=rows[y][i];
      }
      last=rows[y][i];
    }
    fillRun();
  });
}

function strokePatoDash(ctx,x,y,w,alpha,glowBoost,lineWidth){
  glowBoost=glowBoost||1;
  var main=lineWidth||2.4;
  ctx.save();
  ctx.lineCap='butt';
  ctx.lineWidth=main+.9;
  ctx.strokeStyle=cssVar('--brand');
  ctx.globalAlpha=alpha*.12*glowBoost;
  ctx.beginPath(); ctx.moveTo(x-w/2,y); ctx.lineTo(x+w/2,y); ctx.stroke();
  ctx.restore();

  ctx.save();
  ctx.lineCap='butt';
  ctx.lineWidth=main;
  ctx.strokeStyle=cssVar('--brand');
  ctx.globalAlpha=alpha;
  ctx.beginPath(); ctx.moveTo(x-w/2,y); ctx.lineTo(x+w/2,y); ctx.stroke();
  ctx.restore();
}

function animatePatoResolve(onComplete){
  var ov=document.createElement('div');
  ov.style.cssText=[
    'position:fixed','inset:0','z-index:9998',
    'background:var(--bg)',
    'display:flex','flex-direction:column','align-items:center','justify-content:center','gap:28px',
    'opacity:0','transition:opacity .45s cubic-bezier(.4,0,.2,1)',
    'pointer-events:none','cursor:default'
  ].join(';');

  var cv=document.createElement('canvas');
  cv.width=260; cv.height=260;
  cv.className='resolve-pato';
  cv.style.cssText='width:min(34vw,280px);height:min(34vw,280px)';
  var label=document.createElement('div');
  label.textContent='CHAMADO RESOLVIDO';
  label.style.cssText='font-family:"Schibsted Grotesk",sans-serif;font-size:22px;letter-spacing:.08em;font-weight:700;color:#3F8F5F;opacity:0;transition:opacity .7s ease;text-transform:uppercase';
  ov.appendChild(cv); ov.appendChild(label);
  document.body.appendChild(ov);
  setTimeout(function(){ ov.style.opacity='1'; ov.style.pointerEvents='auto'; },10);

  var ctx=cv.getContext('2d');
  var SC=0.88, OX=(260-263*SC)/2, OY=(260-240*SC)/2;
  var pts=tracosPato.map(function(p){ return [p[0]*SC+OX,p[1]*SC+OY]; });
  var order=pts.map(function(p,i){ return i; }).sort(function(a,b){
    var dy=tracosPato[b][1]-tracosPato[a][1]; return dy!==0?dy:tracosPato[a][0]-tracosPato[b][0];
  });
  var TOTAL=pts.length, DASH_W=6, STAGGER=5, FULL=STAGGER*TOTAL+100;
  ctx.lineCap='butt'; ctx.lineWidth=2.4;
  var drift=pts.map(function(){ return { vy:-(50+Math.random()*100), vx:(Math.random()-.5)*50, delay:Math.random()*200 }; });
  var t0=null, phase='build', holdStart=0, dStart=0;

  function frame(ts){
    if(!t0) t0=ts;
    var ms=ts-t0;
    ctx.clearRect(0,0,260,260);
    if(phase==='build'){
      var shown=Math.min(Math.floor(ms/STAGGER),TOTAL);
      for(var k=0;k<shown;k++){
        var i=order[k], x=pts[i][0], y=pts[i][1];
        strokePatoDash(ctx,x,y,DASH_W,Math.min((ms-k*STAGGER)/80,1),.9);
      }
      ctx.globalAlpha=1;
      if(ms>=FULL){ phase='hold'; holdStart=ts; setTimeout(function(){ label.style.opacity='1'; },100); }
      requestAnimationFrame(frame);
    } else if(phase==='hold'){
      pts.forEach(function(p){ strokePatoDash(ctx,p[0],p[1],DASH_W,1,1.25); });
      if(ts-holdStart>=1200){ phase='dissolve'; dStart=ts; }
      requestAnimationFrame(frame);
    } else {
      var d=ts-dStart, gone=true;
      pts.forEach(function(p,i){
        var t=Math.max((d-drift[i].delay)/800,0);
        var op=Math.max(1-t*1.4,0);
        if(op>0) gone=false;
        var nx=p[0]+drift[i].vx*t, ny=p[1]+drift[i].vy*t;
        strokePatoDash(ctx,nx,ny,DASH_W,op,.7);
      });
      ctx.globalAlpha=1;
      if(!gone && d<1500){ requestAnimationFrame(frame); }
      else { ov.style.opacity='0'; ov.style.pointerEvents='none'; setTimeout(function(){ ov.remove(); if(onComplete) onComplete(); },500); }
    }
  }
  setTimeout(function(){ requestAnimationFrame(frame); },450);
}

function startPatoPageLoader(options){
  options=options||{};
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches){ return; }
  if(sessionStorage.getItem('pato_loader_seen')){ return; }
  sessionStorage.setItem('pato_loader_seen','1');
  if(document.querySelector('.page-loader')){ return; }

  var ov=document.createElement('div');
  ov.className='page-loader';
  ov.innerHTML='\
    <div class="page-loader-inner">\
      <canvas class="page-loader-pato" width="260" height="260" aria-hidden="true"></canvas>\
      <div class="page-loader-brand">pato.do.problema</div>\
    </div>';
  document.body.appendChild(ov);

  var cv=ov.querySelector('canvas');
  var ctx=cv.getContext('2d');
  var SC=0.88, OX=(260-263*SC)/2, OY=(260-240*SC)/2;
  var pts=tracosPato.map(function(p){ return [p[0]*SC+OX,p[1]*SC+OY]; });
  var order=pts.map(function(p,i){ return i; }).sort(function(a,b){
    var dy=tracosPato[b][1]-tracosPato[a][1];
    return dy!==0?dy:tracosPato[a][0]-tracosPato[b][0];
  });
  var drift=pts.map(function(){ return { vy:-(44+Math.random()*76), vx:(Math.random()-.5)*44, delay:Math.random()*160 }; });
  var stagger=options.stagger||4.5;
  var buildMs=stagger*pts.length+120;
  var holdMs=options.hold||360;
  var dissolveMs=options.dissolve||780;
  var start=null, phase='build', phaseStart=0;

  requestAnimationFrame(function(){
    ov.classList.add('is-settled');
  });

  function drawFrame(ts){
    if(!start){ start=ts; phaseStart=ts; }
    var elapsed=ts-phaseStart;
    ctx.clearRect(0,0,260,260);

    if(phase==='build'){
      var shown=Math.min(Math.floor(elapsed/stagger), pts.length);
      for(var k=0;k<shown;k++){
        var i=order[k], p=pts[i];
        strokePatoDash(ctx,p[0],p[1],6,Math.min((elapsed-k*stagger)/90,1),.85);
      }
      if(elapsed>=buildMs){ phase='hold'; phaseStart=ts; }
      requestAnimationFrame(drawFrame);
      return;
    }

    if(phase==='hold'){
      pts.forEach(function(p){ strokePatoDash(ctx,p[0],p[1],6,1,1); });
      if(elapsed>=holdMs){ phase='dissolve'; phaseStart=ts; }
      requestAnimationFrame(drawFrame);
      return;
    }

    var gone=true;
    pts.forEach(function(p,i){
      var t=Math.max((elapsed-drift[i].delay)/dissolveMs,0);
      var op=Math.max(1-t*1.35,0);
      if(op>0){ gone=false; }
      strokePatoDash(ctx,p[0]+drift[i].vx*t,p[1]+drift[i].vy*t,6,op,.55);
    });

    if(!gone && elapsed<dissolveMs+220){
      requestAnimationFrame(drawFrame);
    } else {
      ov.classList.add('is-revealing');
      ov.style.opacity='0';
      ov.style.pointerEvents='none';
      window.setTimeout(function(){ ov.remove(); }, 320);
    }
  }

  requestAnimationFrame(drawFrame);
}

function animateCount(el,target,suffix,duration){
  suffix=suffix||''; duration=duration||1400;
  var start=performance.now(), isFloat=String(target).includes('.');
  (function tick(now){
    var p=Math.min((now-start)/duration,1), e=1-Math.pow(1-p,3);
    el.textContent=(isFloat?(e*target).toFixed(1):Math.round(e*target))+suffix;
    if(p<1) requestAnimationFrame(tick);
  })(start);
}
