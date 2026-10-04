"""Original visible test harness; no game or third-party mod source is bundled."""
from pathlib import Path
import sys,subprocess,zipfile,shutil,json,time,os
from beamngpy import BeamNGpy,Scenario,Vehicle
import argparse
parser=argparse.ArgumentParser(description='Visible DX11 tyre audio comparison; never headless.')
parser.add_argument('--game',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True,help='New private test directory, outside your normal BeamNG profile')
parser.add_argument('--redux',type=Path,help='Optional Redux ZIP, copied only into the private profile')
parser.add_argument('--um',type=Path,help='Optional Universal Modder module directory for game-only video/audio capture')
args=parser.parse_args()
if args.um:
    sys.path.insert(0,str(args.um));from um.win import Recorder,shot
ROOT=args.output.resolve()
if ROOT.exists():raise RuntimeError('Use a new output directory to preserve previous results and profiles')
ROOT.mkdir(parents=True)
HOME=args.game.resolve()
SOURCE=Path(__file__).resolve().parents[1]
DRIVER=Path(__file__).with_name('visible_audio_driver.lua')
USER=ROOT/'profile';USER.mkdir(exist_ok=True)
cloud=USER/'current/settings/cloud/settings.json';cloud.parent.mkdir(parents=True,exist_ok=True)
cloud.write_text(json.dumps({'GraphicDisplayModes':'Window','GraphicDisplayResolutions':'1280 720','GraphicWindowPlacement':'','GraphicVSync':False,'onlineFeatures':'disable','telemetry':'disable'}))
candidate=ROOT/'candidate.zip'
with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
    for p in SOURCE.rglob('*'):
        if p.is_file() and p.relative_to(SOURCE).parts[0] in ('lua','scripts','ui'):z.write(p,p.relative_to(SOURCE).as_posix())
test=ROOT/'audio_recorder.zip'
old=subprocess.check_output(['git','-C',str(SOURCE),'show','d0d430e:lua/vehicle/extensions/auto/automaticTyresFeedback.lua'])
with zipfile.ZipFile(test,'w',zipfile.ZIP_DEFLATED) as z:
    z.write(DRIVER,'lua/vehicle/extensions/sliplineAudioDriver.lua')
    z.writestr('lua/vehicle/extensions/sliplineLegacyAudio.lua',old)
for folder in (USER/'mods',USER/'current/mods'):
    folder.mkdir(parents=True,exist_ok=True)
    shutil.copy2(candidate,folder);shutil.copy2(test,folder)
    if args.redux:shutil.copy2(args.redux,folder)
bng=BeamNGpy('localhost',64289,home=str(HOME),user=str(USER),quit_on_close=False)
cmd=bng._prepare_call(str(HOME/'Bin64/BeamNG.drive.x64.exe'),None,'-tcom-listen-ip','127.0.0.1','-gfx','dx11')
cmd=[s for s in cmd if s!='-console']
assert '-headless' not in cmd and 'null' not in cmd
proc=subprocess.Popen(cmd,cwd=HOME,creationflags=subprocess.CREATE_NO_WINDOW)
(ROOT/'owned_process.json').write_text(json.dumps({'pid':proc.pid,'profile':str(USER),'visible':True,'redux':bool(args.redux)}))
specs=[('BX_race','bx','vehicles/bx/track_M.pc'),('BX_sport','bx','vehicles/bx/200bx_gtz_M.pc'),('ETK_drift','etki','vehicles/etki/drift.pc'),('Vivace_race','vivace','vehicles/vivace/trackday_M.pc')]
results=[];rec=None
try:
    bng.open(launch=False);print('Connected visible game',proc.pid,flush=True)
    bng.settings.set_deterministic(steps_per_second=50,speed_factor=1)
    bng.control.queue_lua_command("settings.setValue('fpsLimitBackgroundEnabled',false)",True)
    scene=Scenario('smallgrid','slipline_audio');cars=[]
    for i,(name,model,config) in enumerate(specs):
        car=Vehicle('audio_'+name,model=model,part_config=config);scene.add_vehicle(car,pos=(i*600,0,.5),rot_quat=(0,0,0,1));cars.append(car)
    scene.make(bng);bng.scenario.load(scene);bng.scenario.start();bng.control.pause();bng.vehicles.switch(cars[0])
    bng.control.queue_lua_command("extensions.ui_router.navigate('play')",True)
    autoload=[json.loads(car.queue_lua_command("return jsonEncode({loaded=automaticTyresFeedback~=nil,diag=automaticTyresFeedback and automaticTyresFeedback.getDiagnostics()})",True)) for car in cars]
    (ROOT/'autoload.json').write_text(json.dumps(autoload))
    assert all(x['loaded'] for x in autoload),'Automatic loading failed'
    for mode in ('native','legacy','candidate'):
        if results:bng.scenario.restart();bng.control.pause()
        bng.vehicles.switch(cars[0])
        for car in cars:
            car.set_shift_mode('arcade');car.set_esc_mode('off')
            car.queue_lua_command("extensions.unload('automaticTyresFeedback');extensions.unload('sliplineLegacyAudio')",True)
            if mode=='legacy':car.queue_lua_command("extensions.load('sliplineLegacyAudio')",True)
            if mode=='candidate':car.queue_lua_command("assert(select(2,extensions.loadAtRoot('lua/vehicle/extensions/auto/automaticTyresFeedback','')))",True)
            car.queue_lua_command("extensions.load('sliplineAudioDriver');sliplineAudioDriver.start()",True)
        print('Running',mode,flush=True)
        # Capture only this game process and window. No desktop/system audio.
        rec=Recorder(exe='BeamNG.drive.x64.exe',out=str(ROOT/('take_'+mode)),pid=proc.pid,fps=30).start() if args.um else None
        bng.control.resume();started=time.time();captured=False
        while True:
            time.sleep(.5)
            status=json.loads(cars[0].queue_lua_command('return jsonEncode(sliplineAudioDriver.status())',True))
            if not captured and status['t']>15:
                if args.um:shot(str(ROOT/('visible_'+mode+'.png')),exe='BeamNG.drive.x64.exe',scale=.33)
                captured=True
            if not status['active']:break
            if time.time()-started>100:raise RuntimeError('Visible audio test timed out: '+str(status))
        if rec:rec.stop()
        rec=None;bng.control.pause()
        for spec,car in zip(specs,cars):
            data=json.loads(car.queue_lua_command('return jsonEncode(sliplineAudioDriver.result())',True))
            results.append({'mode':mode,'car':spec[0],**data})
            print(mode,spec[0],len(data['samples']),'samples',flush=True)
        (ROOT/'results.json').write_text(json.dumps(results))
        if mode=='candidate':
            restored=json.loads(cars[0].queue_lua_command("extensions.unload('automaticTyresFeedback');local function up(f) for i=1,64 do local n,x=debug.getupvalue(f,i);if n=='wheelsSounds' then return x end;if not n then break end end end;local d={};for id,s in pairs(up(sounds.updateGFX) or {}) do d[#d+1]={name=wheels.wheels[id].name,ownMethod=rawget(s.rigidSkid,'setVolumePitch')~=nil} end;return jsonEncode(d)",True))
            (ROOT/'unload.json').write_text(json.dumps(restored))
    bng.control.quit_beamng();proc.wait(timeout=25)
finally:
    if rec:rec.stop()
    bng.disconnect()
    if proc.poll() is None:proc.terminate();proc.wait(timeout=25)
print('Visible audio runs finished',flush=True)
