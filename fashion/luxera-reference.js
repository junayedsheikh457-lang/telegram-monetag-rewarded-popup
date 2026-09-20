/* LUXÉRA homepage hero manager
   Admin workflow: create/edit a product named __LUXERA_HERO__ from admin.html,
   upload the image from the phone gallery, and save it. The product is hidden
   from the storefront while its cover image is used as the homepage hero. */
(function(){
  'use strict';
  var API='https://telegram-monetag.onrender.com';
  var HERO_NAMES=['__LUXERA_HERO__','HOMEPAGE HERO','HERO IMAGE'];
  function isHero(p){
    var n=String((p&&p.name)||'').trim().toUpperCase();
    return HERO_NAMES.indexOf(n)>=0;
  }
  function hideHeroCards(){
    document.querySelectorAll('.card').forEach(function(card){
      var name=card.querySelector('.name');
      if(name && HERO_NAMES.indexOf(name.textContent.trim().toUpperCase())>=0){
        card.style.display='none';
      }
    });
  }
  function applyHero(p){
    if(!p)return;
    var src=p.image_url||p.image||((Array.isArray(p.gallery)&&p.gallery[0])||'');
    if(!src)return;
    var img=document.getElementById('heroImg');
    if(img){img.src=src;img.setAttribute('data-admin-hero','true');}
    hideHeroCards();
  }
  function loadHero(){
    fetch(API+'/api/fashion/products',{cache:'no-store'})
      .then(function(r){return r.ok?r.json():Promise.reject(new Error('hero request failed'));})
      .then(function(data){
        var items=Array.isArray(data.items)?data.items:[];
        var hero=items.find(isHero);
        if(hero)applyHero(hero);
        hideHeroCards();
      })
      .catch(function(){hideHeroCards();});
  }
  function boot(){
    loadHero();
    setTimeout(loadHero,900);
    setTimeout(hideHeroCards,1400);
    setTimeout(hideHeroCards,2600);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
