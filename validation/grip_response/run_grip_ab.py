from pathlib import Path
import sys, json, shutil, subprocess, zipfile, argparse, time, faulthandler, hashlib


ROOT=None
SCRIPT=Path(__file__).resolve().parent
from beamngpy import BeamNGpy,Scenario,Vehicle

HOME=None
SLIPLINE_ZIP=None
REDUX_ZIP=None
SPECS=[('BX_track','bx','vehicles/bx/track_M.pc','RWD'),('ETK_drift','etki','vehicles/etki/drift.pc','RWD'),('Vivace_track','vivace','vehicles/vivace/trackday_M.pc','FWD'),('Sunburst_RS','sunburst2','vehicles/sunburst2/sport_RS_M.pc','AWD')]
INSPECT="""local w={};for id,x in pairs(wheels.wheelRotators) do w[#w+1]={name=x.name,rays=x.rayCount,radius=x.radius,friction=(v.data.wheels[id] or {}).frictionCoefMiddle};end;return jsonEncode({wheels=w,slipline=rawget(_G,'automaticTyresGrip')~=nil,redux=rawget(_G,'luukstyrethermalsandwear')~=nil,diag=rawget(_G,'automaticTyresGrip') and automaticTyresGrip.getDiagnostics(),parts=v.data.activeParts,esc=electrics.values.esc,abs=electrics.values.abs,position={obj:getPosition().x,obj:getPosition().y,obj:getPosition().z}})"""

def run(condition,repeats,pilot):
    user=ROOT/'profiles'/condition
    user.mkdir(parents=True,exist_ok=True)
    expected={'grip_ab_recorder.zip'}
    if 'slipline' in condition:expected.add(SLIPLINE_ZIP.name)
    if 'redux' in condition:expected.add(REDUX_ZIP.name)
    for folder in (user/'mods',user/'current/mods'):
        unexpected=[p for p in folder.rglob('*.zip') if p.name not in expected] if folder.exists() else []
        if unexpected:raise RuntimeError('Unexpected mod in isolated profile: '+str(unexpected))
    cloud=user/'current/settings/cloud/settings.json'
    cloud.parent.mkdir(parents=True,exist_ok=True)
    settings=json.loads(cloud.read_text()) if cloud.exists() else {}
    settings.update({'GraphicDisplayModes':'Window','GraphicDisplayResolutions':'1280 720','GraphicWindowPlacement':'','GraphicVSync':False,'onlineFeatures':'disable','telemetry':'disable'})
    cloud.write_text(json.dumps(settings),encoding='utf-8')
    testzip=ROOT/'grip_ab_recorder.zip'
    with zipfile.ZipFile(testzip,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.write(SCRIPT/'slipline_ab_recorder.lua','lua/vehicle/extensions/sliplineABRecorder.lua')
    for mods in (user/'mods',user/'current/mods'):
        mods.mkdir(parents=True,exist_ok=True)
        shutil.copy2(testzip,mods)
        if 'slipline' in condition:shutil.copy2(SLIPLINE_ZIP,mods)
        if 'redux' in condition:shutil.copy2(REDUX_ZIP,mods)
    bng=BeamNGpy('localhost',64275,home=str(HOME),user=str(user),quit_on_close=False)
    cmd=bng._prepare_call(str(HOME/'Bin64/BeamNG.drive.x64.exe'),None,'-tcom-listen-ip','127.0.0.1','-gfx','dx11')
    cmd=[s for s in cmd if s!='-console']
    proc=subprocess.Popen(cmd,cwd=str(HOME),creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT/'owned_process.json').write_text(json.dumps({'pid':proc.pid,'condition':condition,'profile':str(user)}))
    result={'condition':condition,'sliplineVersion':VERSION,'sliplineSHA256':DIGEST,'game':'0.39.4.0','track':'smallgrid','runs':[],'started':time.time()}
    results=ROOT/'results';results.mkdir(exist_ok=True)
    try:
        bng.open(launch=False)
        print('Connected',condition,flush=True)
        bng.settings.set_deterministic(steps_per_second=20,speed_factor=1)
        bng.control.queue_lua_command("settings.setValue('fpsLimitBackgroundEnabled',false)",True)
        scene=Scenario('smallgrid','grip_ab_'+condition)
        cars=[]
        for i,(name,model,config,drive) in enumerate(SPECS):
            car=Vehicle('ab_'+name,model=model,part_config=config)
            scene.add_vehicle(car,pos=((i-1.5)*600,0,.5),rot_quat=(0,0,0,1));cars.append(car)
        scene.make(bng);print('Loading four-car scene',flush=True)
        bng.scenario.load(scene);print('Loaded',flush=True)
        bng.scenario.start();bng.control.pause();bng.vehicles.switch(cars[0]);bng.control.queue_lua_command("extensions.ui_router.navigate('play')",True);print('Visible game paused and ready',flush=True)
        for repeat in range(repeats):
            for maneuver in (args.maneuvers or (['corner'] if pilot else ['corner','steering','brake','drift'])):
                if result['runs']:bng.scenario.restart();bng.control.pause()
                for car in cars:
                    print('Configure',car.vid,flush=True)
                    car.set_shift_mode('arcade')
                    car.set_esc_mode('off')
                    car.queue_lua_command("extensions.load('sliplineABRecorder')",True)
                    target=27.777777778 if maneuver=='brake' else 18 if maneuver=='drift' else 20
                    car.queue_lua_command("sliplineABRecorder.start("+json.dumps(maneuver)+","+str(target)+")",True)
                print('Running',repeat,maneuver,flush=True)
                chunks=0
                while True:
                    # BeamNG's step count advances rendered simulation frames.
                    # With this profile each frame carries a measured 50 ms of physics.
                    bng.control.step(40,wait=True);chunks+=1
                    status=[json.loads(car.queue_lua_command('return jsonEncode(sliplineABRecorder.status())',True)) for car in cars]
                    if pilot:print('Clock',status,flush=True)
                    if all(not state['active'] for state in status):break
                    if chunks>30:raise RuntimeError('Recorder did not finish: '+str(status))
                for spec,car in zip(SPECS,cars):
                    data=json.loads(car.queue_lua_command('return jsonEncode(sliplineABRecorder.result())',True))
                    metadata=json.loads(car.queue_lua_command(INSPECT,True))
                    metadata['driveMode']=car.get_esc_mode()
                    assert metadata['slipline']==('slipline' in condition),metadata
                    assert metadata['redux']==('redux' in condition),metadata
                    assert len(metadata['wheels'])==4
                    entry={'car':spec[0],'model':spec[1],'config':spec[2],'drive':spec[3],'repeat':repeat,'metadata':metadata,**data}
                    result['runs'].append(entry)
                    measuring=[s for s in data['samples'] if s['phase']=='measure']
                    print(condition,repeat,maneuver,spec[0], 'samples',len(data['samples']), 'dt',round(data['clock']['dtMin'],4),round(data['clock']['dtMax'],4),'entry',round(measuring[0]['speed'],2) if measuring else None,'peakBeta',round(max((abs(s['beta']) for s in measuring),default=0),1),flush=True)
                (results/(condition+('_pilot' if pilot else '')+'.json')).write_text(json.dumps(result),encoding='utf-8')
        result['wallSeconds']=time.time()-result['started']
        (results/(condition+('_pilot' if pilot else '')+'.json')).write_text(json.dumps(result),encoding='utf-8')
        bng.control.quit_beamng();proc.wait(timeout=25)
    finally:
        bng.disconnect()
        if proc.poll() is None:proc.terminate();proc.wait(timeout=25)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--cars',nargs='+',choices=[s[0] for s in SPECS],help='Limit the factory cars; omitted means all')
    parser.add_argument('--maneuvers',nargs='+',choices=['corner', 'steering', 'brake', 'drift'],help='Limit inputs; omitted means the original protocol')
    parser.add_argument('--condition',choices=['stock','slipline','redux','redux_slipline'],required=True)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--suite',action='store_true')
    parser.add_argument('--game-home',type=Path,required=True,help='BeamNG installation root')
    parser.add_argument('--workspace',type=Path,required=True,help='A dedicated test directory; never the normal BeamNG user folder')
    parser.add_argument('--slipline-zip',type=Path,help='The exact release ZIP to compare')
    parser.add_argument('--redux-zip',type=Path,help='Redux 0.20 ZIP, supplied separately by its author')
    args=parser.parse_args()
    HOME=args.game_home.resolve();ROOT=args.workspace.resolve()
    SLIPLINE_ZIP=args.slipline_zip.resolve() if args.slipline_zip else None
    REDUX_ZIP=args.redux_zip.resolve() if args.redux_zip else None
    conditions=['stock','slipline','redux','redux_slipline'] if args.suite else [args.condition]
    if any('slipline' in c for c in conditions) and (not SLIPLINE_ZIP or not SLIPLINE_ZIP.is_file()):parser.error('--slipline-zip is required for these conditions')
    if any('redux' in c for c in conditions) and (not REDUX_ZIP or not REDUX_ZIP.is_file()):parser.error('--redux-zip is required for these conditions')
    if not (HOME/'Bin64/BeamNG.drive.x64.exe').is_file():parser.error('BeamNG executable not found')
    if args.repeats!=3 and args.suite:parser.error('The documented full comparison uses three repeats')
    VERSION=None;DIGEST=None
    if SLIPLINE_ZIP:
        with zipfile.ZipFile(SLIPLINE_ZIP) as archive:
            VERSION=json.loads(archive.read('ui/modules/apps/automaticTyresMonitor/app.json'))['version']
        DIGEST=hashlib.sha256(SLIPLINE_ZIP.read_bytes()).hexdigest()
    if args.cars:SPECS=[s for s in SPECS if s[0] in args.cars]
    ROOT.mkdir(parents=True,exist_ok=True)
    for condition in (['stock','slipline','redux','redux_slipline'] if args.suite else [args.condition]):
        run(condition,args.repeats,args.pilot)
