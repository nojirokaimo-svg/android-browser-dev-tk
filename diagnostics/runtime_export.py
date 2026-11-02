"""Observe the real Android browser and extension blob downloads over DevTools."""
import json, pathlib, subprocess, time, urllib.request
import websocket

out = pathlib.Path('diagnostics-output')
def adb(*args):
    return subprocess.check_output(['adb', *args], text=True)
def get(path):
    return json.load(urllib.request.urlopen('http://127.0.0.1:9222' + path, timeout=3))
for attempt in range(80):
    sockets = adb('shell', 'cat', '/proc/net/unix')
    (out/'devtools-sockets.txt').write_text(sockets)
    matches = [line.split('@')[-1] for line in sockets.splitlines()
               if '@' in line and 'chrome_devtools_remote' in line and 'stetho' not in line]
    endpoints = ['localabstract:' + name for name in matches] + ['tcp:9222']
    connected = False
    for endpoint in endpoints:
        adb('forward', 'tcp:9222', endpoint)
        try:
            version=get('/json/version')
            if 'webSocketDebuggerUrl' not in version: continue
            connected=True
            break
        except Exception:
            continue
    if connected: break
    time.sleep(1)
else:
    raise RuntimeError('No responding Chrome DevTools endpoint after launch')
for attempt in range(20):
    targets = get('/json')
    if any(t['url'].endswith('/probe.html') for t in targets): break
    time.sleep(1)
(out/'devtools-targets.json').write_text(json.dumps(targets, indent=2))
(out/'devtools-version.json').write_text(json.dumps(get('/json/version'), indent=2))
browser = websocket.create_connection(get('/json/version')['webSocketDebuggerUrl'], timeout=20)
browser.send(json.dumps({'id':1,'method':'Browser.setDownloadBehavior','params':{'behavior':'default','eventsEnabled':True}}))
(out/'download-behavior.json').write_text(browser.recv())
probe = next((t for t in targets if t['url'].endswith('/probe.html')), None)
if probe is None:
    # The extension may have loaded without a page; collect browser internals for diagnosis.
    target = next(t for t in targets if t['type']=='page')
    ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=20)
    ws.send(json.dumps({'id':2,'method':'Page.navigate','params':{'url':'chrome://extensions'}}))
    time.sleep(2)
    ws.send(json.dumps({'id':3,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText','returnByValue':True}}))
    rows=[]
    while True:
        msg=json.loads(ws.recv()); rows.append(msg)
        if msg.get('id')==3: break
    (out/'extensions-page.json').write_text(json.dumps(rows,indent=2))
    raise RuntimeError('Probe extension has no inspectable target; export test not performed')
(out/'probe-target.json').write_text(json.dumps(probe,indent=2))

ws = websocket.create_connection(probe['webSocketDebuggerUrl'], timeout=20)
seq = 10
messages=[]
def call(method,params):
    global seq
    seq += 1
    ws.send(json.dumps({'id':seq,'method':method,'params':params}))
    while True:
        msg=json.loads(ws.recv()); messages.append(msg)
        if msg.get('id')==seq:
            if 'error' in msg: raise RuntimeError(msg['error'])
            return msg.get('result',{})
call('Runtime.enable',{})
call('Page.enable',{})
for button in ('anchor','async','api'):
    xy=call('Runtime.evaluate',{'expression':f"JSON.stringify((()=>{{let r=document.querySelector('#{button}').getBoundingClientRect();return {{x:r.x+r.width/2,y:r.y+r.height/2}}}})())",'returnByValue':True})
    xy=json.loads(xy['result']['value'])
    call('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**xy})
    call('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**xy})
    time.sleep(4)
    (out/f'downloads-after-{button}.txt').write_text(adb('shell','ls','-la','/sdcard/Download'))
    call('Runtime.evaluate',{'expression':"document.querySelector('#log').innerText",'returnByValue':True})
(out/'probe-cdp.json').write_text(json.dumps(messages,indent=2))
extensions = call('Runtime.evaluate',{'expression':'new Promise(resolve=>chrome.management.getAll(resolve))','awaitPromise':True,'returnByValue':True})['result']['value']
(out/'installed-extensions.json').write_text(json.dumps(extensions,indent=2))
for ext in extensions:
    if 'Violentmonkey' not in ext['name']: continue
    call('Page.navigate',{'url':f"chrome-extension://{ext['id']}/options/index.html#settings"})
    time.sleep(3)
    call('Runtime.evaluate',{'expression':"addEventListener('unhandledrejection', e=>console.error('EXPORT_REJECTION',String(e.reason))); addEventListener('error',e=>console.error('EXPORT_ERROR',e.message))"})
    code = '// ==UserScript==\n// @name ZIP export diagnostic\n// @namespace diagnostic-only\n// @version 1.0\n// @match https://example.invalid/*\n// @grant none\n// ==/UserScript==\nconsole.log("diagnostic");'
    expression = 'chrome.runtime.sendMessage(' + json.dumps({'cmd':'ParseScript','data':{'code':code,'isNew':True}}) + ')'
    call('Runtime.evaluate',{'expression':expression,'awaitPromise':True,'returnByValue':True})
    call('Page.reload',{})
    time.sleep(3)
    call('Runtime.evaluate',{'expression':"addEventListener('unhandledrejection', e=>console.error('EXPORT_REJECTION',String(e.reason))); addEventListener('error',e=>console.error('EXPORT_ERROR',e.message)); document.body.innerText",'returnByValue':True})
    button = call('Runtime.evaluate',{'expression':"JSON.stringify((()=>{const b=[...document.querySelectorAll('button')].find(b=>/export.*zip/i.test(b.innerText));if(!b)return null;b.scrollIntoView();let r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,text:b.innerText}})())",'returnByValue':True})['result']['value']
    if button != 'null':
        xy=json.loads(button); xy.pop('text',None)
        call('Input.dispatchMouseEvent',{'type':'mousePressed','button':'left','clickCount':1,**xy})
        call('Input.dispatchMouseEvent',{'type':'mouseReleased','button':'left','clickCount':1,**xy})
        time.sleep(5)
    (out/f"downloads-after-{ext['id']}.txt").write_text(adb('shell','ls','-la','/sdcard/Download'))
    (out/f"vm-{ext['id']}-cdp.json").write_text(json.dumps(messages,indent=2))
adb('pull','/sdcard/Download',str(out/'downloaded-zips'))

