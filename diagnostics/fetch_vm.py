"""Use pinned, unmodified official Violentmonkey releases in a disposable profile."""
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request
import zipfile

assets = {
    'vm2': ('Violentmonkey-mv2-v2.50.0.crx', '9a2553d7e3deb66c63c3649232f0d5e79bdeb03f2848ed49ce3f7646eaab2357'),
    'vm3': ('Violentmonkey-mv3-v2.50.0.zip', '72f1de5a2edc4bc3cd3b3ca06c2b3631cdde4f06f8ed9e8b2b565bf77258b36c'),
}
for directory, (asset, expected) in assets.items():
    url = 'https://github.com/violentmonkey/violentmonkey/releases/download/v2.50.0/' + asset
    data = urllib.request.urlopen(url, timeout=60).read()
    assert hashlib.sha256(data).hexdigest() == expected, asset
    if data[:4] == b'Cr24':
        version, length = struct.unpack_from('<II', data, 4)
        assert version == 3
        data = data[12 + length:]
    root = Path('diagnostics-output') / directory
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            name = Path(item.filename)
            assert not name.is_absolute() and '..' not in name.parts
        archive.extractall(root)
    print(directory, expected, json.loads((root/'manifest.json').read_text())['version'])
