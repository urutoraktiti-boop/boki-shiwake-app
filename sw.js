const CACHE_NAME="boki-shiwake-v3.35";
const APP_SHELL=[
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/identity-core.js",
  "./assets/app-icon-192.png",
  "./assets/app-icon-512.png",
  "./help/"
];

self.addEventListener("install",event=>{
  event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()));
});

self.addEventListener("activate",event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});

self.addEventListener("fetch",event=>{
  const request=event.request;
  if(request.method!=="GET")return;
  const url=new URL(request.url);
  if(url.hostname.includes("googleapis.com")||url.hostname.includes("gstatic.com")||url.hostname.includes("firebase"))return;

  if(request.mode==="navigate"){
    event.respondWith(fetch(request).then(response=>{
      const copy=response.clone(); caches.open(CACHE_NAME).then(cache=>cache.put(request,copy)); return response;
    }).catch(async()=>await caches.match(request)||await caches.match("./index.html")));
    return;
  }

  if(url.origin===location.origin){
    event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{
      const copy=response.clone(); caches.open(CACHE_NAME).then(cache=>cache.put(request,copy)); return response;
    })));
  }
});
