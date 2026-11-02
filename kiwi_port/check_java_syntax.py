"""Parse every audited Java source before starting an expensive Android build."""
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
source = Path(sys.argv[1]).resolve()
manifest = json.loads((here / 'manifest.json').read_text())
paths = [str(source / name) for name in manifest['files'] if name.endswith('.java')]
java = sys.argv[2] if len(sys.argv) > 2 else str(source / 'third_party/jdk/current/bin/java')
subprocess.run([java, str(here / 'ParseJavaSources.java'), *paths], check=True)
