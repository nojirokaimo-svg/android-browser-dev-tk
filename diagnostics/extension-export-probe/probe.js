const log = document.querySelector('#log');
function report(value) { log.textContent += JSON.stringify(value) + '\n'; }
window.addEventListener('error', e => report({error:e.message}));
window.addEventListener('unhandledrejection', e => report({rejection:String(e.reason)}));
const zip = () => new Blob([new Uint8Array([80,75,5,6,...new Array(18).fill(0)])], {type:'application/zip'});
function anchor(name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(zip()); a.download = name; a.click();
  report({clicked:name, active:navigator.userActivation.isActive});
  setTimeout(() => URL.revokeObjectURL(a.href), 60000);
}
document.querySelector('#anchor').onclick = () => anchor('probe-anchor.zip');
document.querySelector('#async').onclick = async () => {
  await new Promise(resolve => setTimeout(resolve, 200)); anchor('probe-async.zip');
};
document.querySelector('#api').onclick = () => {
  const url = URL.createObjectURL(zip());
  chrome.downloads.download({url,filename:'probe-api.zip'}, id => {
    report({downloadId:id,error:chrome.runtime.lastError?.message});
    setTimeout(() => URL.revokeObjectURL(url),60000);
  });
};
chrome.downloads.onChanged.addListener(change => report(change));
report({origin:location.origin,userAgent:navigator.userAgent});
