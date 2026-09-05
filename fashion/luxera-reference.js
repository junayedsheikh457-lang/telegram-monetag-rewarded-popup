(function(){
  function arrange(){
    var grid=document.querySelector('.grid');
    if(!grid) return false;
    var cards=[].slice.call(grid.querySelectorAll('.card'));
    if(cards.length<4) return false;
    var order=['Embroidered A-Line Dress','Lace Detail Co-ord Set','Printed Oversized Shirt','Floral Midi Dress'];
    function name(c){var e=c.querySelector('.name');return e?e.textContent.replace(/\s+/g,' ').trim():''}
    cards.sort(function(a,b){var ai=order.indexOf(name(a)),bi=order.indexOf(name(b));ai=ai<0?999:ai;bi=bi<0?999:bi;return ai-bi});
    cards.forEach(function(c){grid.appendChild(c)});
    var first=cards.slice(0,4), rest=cards.slice(4);
    var offer=document.querySelector('.offer');
    if(!offer) return true;
    var more=document.getElementById('luxeraMoreProducts');
    if(!more){
      more=document.createElement('section');more.id='luxeraMoreProducts';more.className='luxera-more';
      more.innerHTML='<div class="head"><h2>More Products</h2><span class="view">View All</span></div><div class="grid luxera-more-grid"></div>';
      offer.parentNode.insertBefore(more,offer.nextSibling);
    }
    var mg=more.querySelector('.luxera-more-grid');
    first.forEach(function(c){grid.appendChild(c)});
    rest.forEach(function(c){mg.appendChild(c)});
    grid.style.display='grid';
    return true;
  }
  function start(){
    var tries=0, t=setInterval(function(){tries++;if(arrange()||tries>30)clearInterval(t)},250);
    var obs=new MutationObserver(function(){if(arrange()){} });
    var root=document.querySelector('.grid')||document.body;obs.observe(root,{childList:true,subtree:true});
    setTimeout(function(){obs.disconnect()},12000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();