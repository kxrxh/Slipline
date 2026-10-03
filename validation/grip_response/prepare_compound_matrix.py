"""Generate only test profiles and driving code; factory assets remain in the installation."""
from pathlib import Path
import zipfile,json,re,hashlib
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--game-home',type=Path,required=True)
parser.add_argument('--workspace',type=Path,required=True)
args=parser.parse_args()
GAME=args.game_home.resolve()/'content/vehicles'
workspace=args.workspace.resolve();workspace.mkdir(parents=True,exist_ok=True)
SPECIFICATIONS=[
 ('Covet_race','covet','race.pc','FWD',['standard','sport'],'15x7','195_60_15','15x7','195_60_15'),
 ('ETK800_track','etk800','844_track_M.pc','RWD',['sport','race','drift'],'17x9','245_35_17','17x9','245_35_17'),
 ('SBR4_S_AWD','sbr','S_AWD_M.pc','AWD',['sport','race'],'18x8','225_40_18','18x11','295_30_18')]
def read_factory(model,filename):
    with zipfile.ZipFile(GAME/(model+'.zip')) as z:raw=z.read('vehicles/'+model+'/'+filename)
    text=raw.decode('utf-8-sig')
    # Some legacy native .pc files omit commas. Parts and vars are flat maps.
    try:cfg=json.loads(text)
    except json.JSONDecodeError:
        parts=re.search(r'"parts"\s*:\s*\{(.*?)\}',text,re.S).group(1)
        variables=re.search(r'"vars"\s*:\s*\{(.*?)\}',text,re.S)
        cfg={'parts':dict(re.findall(r'"([^"\n]+)"\s*:\s*"([^"\n]*)"',parts)),
         'vars':{k:float(v) for k,v in re.findall(r'"([^"\n]+)"\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)',variables.group(1))} if variables else {}}
    cfg.update({'format':2,'model':model,'mainPartName':model})
    return cfg,hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(GAME/'common.zip') as z:
    available=set()
    for n in z.namelist():
        if '/tires/' in n and n.endswith('.jbeam'):
            available.update(re.findall(r'^\s*"(tire_[^"]+)"\s*:\s*\{',z.read(n).decode('utf-8-sig'),re.M))
cases=[]
for car,model,filename,drive,compounds,frontslot,frontsize,rearslot,rearsize in SPECIFICATIONS:
    factory,digest=read_factory(model,filename)
    for compound in compounds:
        changes={'tire_F_'+frontslot:'tire_F_'+frontsize+'_'+compound,'tire_R_'+rearslot:'tire_R_'+rearsize+'_'+compound}
        assert set(changes.values())<=available,changes
        cfg=json.loads(json.dumps(factory));cfg['parts'].update(changes)
        cfg.setdefault('vars',{}).update({'$tirepressure_F':28,'$tirepressure_R':28})
        cases.append({'car':car+'_'+compound,'family':car,'model':model,'compound':compound,'drive':drive,
         'factoryConfig':'vehicles/'+model+'/'+filename,'factorySha256':digest,
         'config':'vehicles/'+model+'/_slipline_matrix_'+compound+'.pc','tyreParts':changes,'configuration':cfg})
(workspace/'compound_matrix_manifest.json').write_text(json.dumps(cases,indent=2))
