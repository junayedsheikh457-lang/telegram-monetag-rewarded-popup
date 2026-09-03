/* Fashion Store multi-image gallery helpers */
window.FashionGallery = {
  parse(p){
    let imgs=[];
    try{ if(Array.isArray(p.gallery)) imgs=p.gallery; else if(p.gallery) imgs=JSON.parse(p.gallery); }catch(e){}
    if(!imgs.length && p.image) imgs=[p.image];
    if(p.image && imgs[0]!==p.image) imgs.unshift(p.image);
    return imgs.filter(Boolean).slice(0,6);
  },
  open(product){
    const imgs=this.parse(product); if(!imgs.length)return;
    const modal=document.createElement('div'); modal.className='gallery-modal';
    modal.innerHTML=`<div class="gallery-backdrop"></div><div class="gallery-box"><button class="gallery-close">×</button><div class="gallery-main"><img id="galleryMain" src="${this.safe(imgs[0])}"></div><div class="gallery-thumbs">${imgs.map((x,i)=>`<button class="gallery-thumb ${i===0?'active':''}" data-i="${i}"><img src="${this.safe(x)}"></button>`).join('')}</div></div>`;
    document.body.appendChild(modal);
    const main=modal.querySelector('#galleryMain'); modal.querySelectorAll('.gallery-thumb').forEach((b,i)=>b.onclick=()=>{main.src=imgs[i];modal.querySelectorAll('.gallery-thumb').forEach(x=>x.classList.remove('active'));b.classList.add('active')});
    const close=()=>modal.remove(); modal.querySelector('.gallery-close').onclick=close; modal.querySelector('.gallery-backdrop').onclick=close;
  },
  safe(s){return String(s||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
};
