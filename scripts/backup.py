"""Consistent SQLite backup, including committed writes; no credential output."""
import argparse, sqlite3, datetime
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
parser=argparse.ArgumentParser();parser.add_argument('--destination',default='backups');args=parser.parse_args()
source=Path(server.DB)
if not source.exists():raise SystemExit('Base absente : démarrez d’abord l’application.')
folder=Path(args.destination);folder.mkdir(parents=True,exist_ok=True)
target=folder/('bazar-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
with sqlite3.connect(source) as src,sqlite3.connect(target) as dst:
    src.backup(dst)
    if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Sauvegarde invalide')
target.chmod(0o600)
print('Sauvegarde vérifiée : '+str(target))
