(function(){
  function readCart(){
    try{
      var raw=JSON.parse(localStorage.getItem('luxCart')||'[]');
      if(!Array.isArray(raw))raw=[];
      return raw.filter(function(x){return x&&x.id!=null&&Number(x.qty)>0}).map(function(x){return Object.assign({},x,{id:Number(x.id),qty:Number(x.qty)||1,price:Number(x.price)||0})});
    }catch(e){return []}
  }
  function syncCart(){
    var fresh=readCart();
    try{cart=fresh;localStorage.setItem('luxCart',JSON.stringify(fresh));}catch(e){}
    if(typeof counts==='function')counts();
    return fresh;
  }
  function compactCartStyle(){
    if(document.getElementById('luxera-cart-fix'))return;
    var s=document.createElement('style');s.id='luxera-cart-fix';s.textContent=`
      #cart .box{width:min(460px,calc(100vw - 20px));max-height:calc(100vh - 20px);overflow:hidden;padding:12px;border-radius:16px}
      #cart .box>h2{font-size:20px;margin:2px 0 8px;padding-right:35px}
      #cart #cartBody{max-height:calc(100vh - 115px);overflow-y:auto;overflow-x:hidden;padding-right:2px}
      #cart .cartrow{grid-template-columns:48px minmax(0,1fr) auto;gap:7px;padding:6px 0}
      #cart .cartrow img{width:48px;height:56px;border-radius:6px}
      #cart .cartrow>div{min-width:0;font-size:11px;line-height:1.25}
      #cart .cartrow>div:first-of-type{overflow:hidden}
      #cart .cartrow>div:first-of-type br+span{font-size:10px}
      #cart .qty{margin-top:3px;white-space:nowrap;font-size:10px}
      #cart .qty button{width:21px;height:21px;font-size:12px;padding:0}
      #cart .cartrow>b{font-size:10px;white-space:nowrap}
      #cart .total{padding:8px 0;font-size:12px;position:sticky;bottom:0;background:#0d0d0d}
      #cart #cartBody>.cta{display:block;width:100%;padding:9px;font-size:10px;position:sticky;bottom:0}
      #cart .empty{padding:18px 8px;font-size:12px}
      @media(max-width:700px){#cart .box{width:calc(100vw - 16px);max-height:calc(100vh - 16px);padding:10px}#cart #cartBody{max-height:calc(100vh - 100px)}#cart .cartrow{grid-template-columns:44px minmax(0,1fr) auto}#cart .cartrow img{width:44px;height:52px}}
    `;document.head.appendChild(s);
  }
  function arrange(){
    var grid=document.querySelector('.grid');if(!grid)return false;
    var cards=[].slice.call(grid.querySelectorAll(':scope > .card'));if(cards.length<4)return false;
    var order=['Embroidered A-Line Dress','Lace Detail Co-ord Set','Printed Oversized Shirt','Floral Midi Dress'];
    function name(c){var e=c.querySelector('.name');return e?e.textContent.replace(/\s+/g,' ').trim():''}
    cards.sort(function(a,b){var ai=order.indexOf(name(a)),bi=order.indexOf(name(b));ai=ai<0?999:ai;bi=bi<0?999:bi;return ai-bi});
    var first=cards.slice(0,4),rest=cards.slice(4);first.forEach(function(c){grid.appendChild(c)});
    var offer=document.querySelector('.offer');if(!offer)return true;
    var more=document.getElementById('luxeraMoreProducts');
    if(!more){more=document.createElement('section');more.id='luxeraMoreProducts';more.className='luxera-more';more.innerHTML='<div class="head"><h2>More Products</h2><span class="view">View All</span></div><div class="grid luxera-more-grid"></div>';offer.parentNode.insertBefore(more,offer.nextSibling)}
    var mg=more.querySelector('.luxera-more-grid');rest.forEach(function(c){mg.appendChild(c)});return true;
  }
  function addRelatedProducts(modal,currentId){
    if(!modal||modal.querySelector('.detail-related'))return;var box=modal.querySelector('.box');if(!box)return;
    var all=[].slice.call(document.querySelectorAll('#grid .card,#luxeraMoreProducts .card'));
    var related=all.filter(function(c){var m=(c.getAttribute('onclick')||'').match(/detail\((\d+)\)/);return m&&Number(m[1])!==Number(currentId)}).slice(0,8);if(!related.length)return;
    var sec=document.createElement('section');sec.className='detail-related';sec.innerHTML='<div class="head"><h2>You May Also Like</h2><span class="view">More</span></div><div class="detail-related-grid"></div>';var rg=sec.querySelector('.detail-related-grid');
    related.forEach(function(originalCard){var card=originalCard.cloneNode(true);card.classList.add('detail-related-card');card.removeAttribute('onclick');
      card.addEventListener('click',function(e){if(e.target.closest('.heart,.add'))return;var m=(originalCard.getAttribute('onclick')||'').match(/detail\((\d+)\)/);if(m&&typeof window.detail==='function')window.detail(Number(m[1]))});
      var addBtn=card.querySelector('.add');if(addBtn){addBtn.removeAttribute('onclick');addBtn.addEventListener('click',function(e){e.stopPropagation();var m=(originalCard.innerHTML.match(/add\((\d+)\)/)||[])[1];if(m&&typeof window.add==='function')window.add(Number(m))})}
      var heart=card.querySelector('.heart');if(heart){heart.removeAttribute('onclick');heart.addEventListener('click',function(e){e.stopPropagation();var m=(originalCard.innerHTML.match(/toggleWish\((\d+)\)/)||[])[1];if(m&&typeof window.toggleWish==='function')window.toggleWish(Number(m))})}rg.appendChild(card);
    });box.appendChild(sec);
  }
  function hookDetail(){if(typeof window.detail!=='function'||window.__luxeraDetailHooked)return !!window.__luxeraDetailHooked;var original=window.detail;window.detail=function(id){original(id);setTimeout(function(){addRelatedProducts(document.querySelector('.modal.show'),id)},120)};window.__luxeraDetailHooked=true;return true}
  function fixOrder(){
    if(typeof window.order!=='function'||window.__luxeraOrderFixed)return !!window.__luxeraOrderFixed;
    window.order=function(){
      var fresh=syncCart();
      var customer=(document.getElementById('customer')?.value||'').trim(),phone=(document.getElementById('phone')?.value||'').trim(),address=(document.getElementById('address')?.value||'').trim();
      var msg=document.getElementById('msg');if(!customer||!phone||!address){if(msg)msg.textContent='সব তথ্য পূরণ করুন।';return}
      if(!fresh.length){if(msg)msg.textContent='Cart খালি।';return}
      if(msg)msg.textContent='Order পাঠানো হচ্ছে...';
      var items=fresh.map(function(x){return{id:Number(x.id),name:x.name||'Product',category:x.category||'',price:Number(x.price||0),qty:Number(x.qty||1),image:x.image||x.image_url||''}});
      var total=items.reduce(function(s,x){return s+x.price*x.qty},0);
      fetch('https://telegram-monetag.onrender.com/api/fashion/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer_name:customer,customer:customer,name:customer,phone:phone,address:address,items:items,total:total})})
      .then(function(r){return r.json().then(function(j){if(!r.ok)throw Error(j.error||'Order failed');return j})})
      .then(function(j){localStorage.luxAcc=JSON.stringify({name:customer,phone:phone,address:address});cart=[];localStorage.setItem('luxCart','[]');if(typeof counts==='function')counts();if(msg)msg.textContent='✅ Order সফল! Order ID: #'+j.order_id;setTimeout(function(){closeM('checkout')},1800)})
      .catch(function(e){if(msg)msg.textContent='❌ '+e.message});
    };
    window.__luxeraOrderFixed=true;return true;
  }
  function fixCart(){syncCart();compactCartStyle()}
  function start(){compactCartStyle();arrange();hookDetail();fixOrder();fixCart();setTimeout(arrange,700);setTimeout(hookDetail,700);setTimeout(fixOrder,700);setTimeout(fixCart,700);setTimeout(arrange,1700);setTimeout(hookDetail,1700);setTimeout(fixOrder,1700);setTimeout(fixCart,1700)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
