document.addEventListener('DOMContentLoaded',()=>{
  const body=document.body,drawer=document.getElementById('mobile-navigation');
  const open=()=>{body.classList.add('menu-open');drawer?.setAttribute('aria-hidden','false')};
  const close=()=>{body.classList.remove('menu-open');drawer?.setAttribute('aria-hidden','true')};
  document.querySelectorAll('[data-menu-open]').forEach(x=>x.addEventListener('click',open));
  document.querySelectorAll('[data-menu-close]').forEach(x=>x.addEventListener('click',close));
  drawer?.querySelectorAll('a').forEach(x=>x.addEventListener('click',close));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
  document.querySelectorAll('.top-menu,.account-menu').forEach(menu=>document.addEventListener('click',e=>{if(!menu.contains(e.target))menu.removeAttribute('open')}));
});
