"""Build a deterministic, installable BeamNG ZIP using only original files."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('lua', 'scripts', 'ui')
SUFFIXES = {'.lua', '.js', '.html', '.css', '.json', '.png'}

def build(output):
    version = json.loads((ROOT / 'ui/modules/apps/automaticTyresMonitor/app.json').read_text(encoding='utf-8'))['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid release version')
    files = [ROOT / 'README.md', ROOT / 'LICENSE.txt', ROOT / 'CHANGELOG.md']
    for directory in DIRECTORIES:
        for path in (ROOT / directory).rglob('*'):
            if path.is_symlink():
                raise ValueError('Symlinks are not allowed in the release')
            if path.is_file():
                if path.suffix not in SUFFIXES:
                    raise ValueError('Unexpected release file: ' + path.relative_to(ROOT).as_posix())
                files.append(path)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / ('slipline_beamng_039_v' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
        for path in sorted(files):
            entry = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 10, 3, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            handle.writestr(entry, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as handle:
        if handle.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        assert 'scripts/automaticTyres/modScript.lua' in handle.namelist()
        assert len(handle.namelist()) == len(set(handle.namelist()))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(digest + '  ' + archive.name + '\n', encoding='utf-8')
    print(archive.name + ': ' + str(len(files)) + ' files, SHA256 ' + digest)
    return archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    build(parser.parse_args().output.resolve())
