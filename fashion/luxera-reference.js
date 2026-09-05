(function(){
  function arrange(){
    var grid=document.querySelector('.grid');
    if(!grid) return false;
    var cards=[].slice.call(grid.querySelectorAll(':scope > .card'));
    if(cards.length<4) return false;
    var order=['Embroidered A-Line Dress','Lace Detail Co-ord Set','Printed Oversized Shirt','Floral Midi Dress'];
    function name(c){var e=c.querySelector('.name');return e?e.textContent.replace(/\s+/g,' ').trim():''}
    cards.sort(function(a,b){
      var ai=order.indexOf(name(a)),bi=order.indexOf(name(b));
      ai=ai<0?999:ai;bi=bi<0?999:bi;
      return ai-bi;
    });
    var first=cards.slice(0,4),rest=cards.slice(4);
    first.forEach(function(c){grid.appendChild(c)});
    var offer=document.querySelector('.offer');
    if(!offer) return true;
    var more=document.getElementById('luxeraMoreProducts');
    if(!more){
      more=document.createElement('section');
      more.id='luxeraMoreProducts';
      more.className='luxera-more';
      more.innerHTML='<div class="head"><h2>More Products</h2><span class="view">View All</span></div><div class="grid luxera-more-grid"></div>';
      offer.parentNode.insertBefore(more,offer.nextSibling);
    }
    var mg=more.querySelector('.luxera-more-grid');
    rest.forEach(function(c){mg.appendChild(c)});
    return true;
  }

  function addRelatedProducts(modal,currentId){
    if(!modal || modal.querySelector('.detail-related')) return;
    var box=modal.querySelector('.box');
    if(!box) return;
    var all=[].slice.call(document.querySelectorAll('#grid .card, #luxeraMoreProducts .card'));
    var related=all.filter(function(c){
      var m=(c.getAttribute('onclick')||'').match(/detail\((\d+)\)/);
      return m && Number(m[1])!==Number(currentId);
    }).slice(0,8);
    if(!related.length) return;
    var sec=document.createElement('section');
    sec.className='detail-related';
    sec.innerHTML='<div class="head"><h2>You May Also Like</h2><span class="view">More</span></div><div class="detail-related-grid"></div>';
    var rg=sec.querySelector('.detail-related-grid');
    related.forEach(function(originalCard){
      var card=originalCard.cloneNode(true);
      card.classList.add('detail-related-card');
      card.removeAttribute('onclick');
      card.addEventListener('click',function(e){
        if(e.target.closest('.heart,.add')) return;
        var m=(originalCard.getAttribute('onclick')||'').match(/detail\((\d+)\)/);
        if(m && typeof window.detail==='function') window.detail(Number(m[1]));
      });
      var addBtn=card.querySelector('.add');
      if(addBtn){
        addBtn.removeAttribute('onclick');
        addBtn.addEventListener('click',function(e){
          e.stopPropagation();
          var m=(originalCard.innerHTML.match(/add\((\d+)\)/)||[])[1];
          if(m && typeof window.add==='function') window.add(Number(m));
        });
      }
      var heart=card.querySelector('.heart');
      if(heart){
        heart.removeAttribute('onclick');
        heart.addEventListener('click',function(e){
          e.stopPropagation();
          var m=(originalCard.innerHTML.match(/toggleWish\((\d+)\)/)||[])[1];
          if(m && typeof window.toggleWish==='function') window.toggleWish(Number(m));
        });
      }
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
        var modal=document.querySelector('.modal.show:last-of-type') || document.querySelector('.modal.show');
        addRelatedProducts(modal,id);
      },80);
    };
    window.__luxeraDetailHooked=true;
    return true;
  }

  function start(){
    arrange();
    hookDetail();
    setTimeout(arrange,500);
    setTimeout(arrange,1500);
    setTimeout(hookDetail,500);
    setTimeout(hookDetail,1500);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
