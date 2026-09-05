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

  function addRelatedProducts(modal,currentId){
    if(!modal || modal.querySelector('.detail-related')) return;
    var box=modal.querySelector('.box');
    if(!box || !Array.isArray(window.products)) return;
    var related=window.products.filter(function(p){return Number(p.id)!==Number(currentId)}).slice(0,8);
    if(!related.length) return;
    var sec=document.createElement('section');
    sec.className='detail-related';
    sec.innerHTML='<div class="head"><h2>You May Also Like</h2><span class="view">More</span></div><div class="detail-related-grid"></div>';
    var rg=sec.querySelector('.detail-related-grid');
    related.forEach(function(p){
      var off=p.old_price>p.price?Math.round((1-p.price/p.old_price)*100):0;
      var card=document.createElement('article');
      card.className='card detail-related-card';
      card.innerHTML='<div class="photo"><img src="'+p.image+'"><span class="tag">'+(off?'-'+off+'%':'NEW')+'</span></div><div class="info"><div class="name">'+String(p.name||'').replace(/[&<>\"']/g,function(x){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[x]})+'</div><span class="price">৳'+Number(p.price||0).toLocaleString()+'</span>'+(p.old_price?'<span class="old">৳'+Number(p.old_price).toLocaleString()+'</span>':'')+'<button class="add">🛒 Add to Cart</button></div>';
      card.addEventListener('click',function(){window.detail(Number(p.id))});
      card.querySelector('.add').addEventListener('click',function(e){e.stopPropagation();window.add(Number(p.id))});
      rg.appendChild(card);
    });
    box.appendChild(sec);
  }

  function hookDetail(){
    if(typeof window.detail!=='function') return false;
    if(window.__luxeraDetailHooked) return true;
    var original=window.detail;
    window.detail=function(id){
      original(id);
      setTimeout(function(){
        var modals=[].slice.call(document.querySelectorAll('.modal.show'));
        var modal=modals[modals.length-1];
        addRelatedProducts(modal,id);
      },0);
    };
    window.__luxeraDetailHooked=true;
    return true;
  }

  function start(){
    var tries=0, t=setInterval(function(){
      tries++;
      var arranged=arrange();
      var hooked=hookDetail();
      if((arranged||hooked)&&tries>2 || tries>30)clearInterval(t);
    },250);
    var obs=new MutationObserver(function(){arrange()});
    var root=document.querySelector('.grid')||document.body;
    obs.observe(root,{childList:true,subtree:true});
    setTimeout(function(){obs.disconnect()},12000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
