"""Portable behavioral acceptance using tiny CPU fixtures; no AI model or network."""
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, tempfile

R=Path(__file__).resolve().parents[1]

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def call(args):return subprocess.run([sys.executable,'-B',*map(str,args)],capture_output=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work-dir',required=True);ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--ffprobe',default='ffprobe');args=ap.parse_args()
    ff=shutil.which(args.ffmpeg);fp=shutil.which(args.ffprobe)
    if not ff or not fp:raise RuntimeError('Provide FFmpeg/ffprobe on PATH or via --ffmpeg/--ffprobe')
    work=Path(args.work_dir).expanduser().resolve();work.mkdir(parents=True,exist_ok=True);v=Path(tempfile.mkdtemp(prefix='ziru-explainer-',dir=work))
    cfg=read(R/'assets/runtime.example.json');cfg['paths'].update(ffmpeg=ff,ffprobe=fp)
    # Explicit missing paths avoid depending on any installed model environment.
    cfg['paths'].update(comfy_root=str(v/'absent-comfy'),comfy_input=str(v/'absent-input'),model_root=str(v/'absent-models'))
    cfg['delivery'].update(width=320,height=180);config=v/'runtime.json';write(config,cfg)
    prompt=v/'prompt.txt';prompt.write_text('subject_definitions:\n<Picture 1> Reference image. <Audio 1> Exact source audio.\nsummary:\nOne 5.167-second shot.\nretention_analysis:\nKeep the inspected identity.\ndetailed_description:\n[Shot 1] <d>[Chinese] 这是一条测试。</d>\noverall_soundscape:\nPreserve source.\nnon_diegetic_music:\nN/A',encoding='utf8')
    rows=[];request=v/'request.json'
    cmd=[R/'scripts/build_h3_request.py','--config',config,'--prompt',prompt,'--image','demo/face.png','--audio','demo/voice.wav','--out',request]
    p=call(cmd);assert p.returncode==0,p.stderr.decode('utf8','replace');g=read(request)
    assert g['6']['inputs']['steps']==8 and g['8']['inputs']['audio_mode']=='lock_source' and g['16']['inputs']['accept_candidate'] is False
    assert g['19']['inputs']['image']=='demo/face.png' and g['2']['inputs']['strength']==1.0
    rows.append({'test':'bind source audio/image and actual eight-step parameters without submission','passed':True})
    p=call(cmd);assert p.returncode!=0 and 'FileExistsError' in p.stderr.decode('utf8','replace');rows.append({'test':'preserve an existing request','passed':True})
    bad=list(cmd);bad[bad.index('demo/face.png')]='../outside.png';bad[-1]=v/'rejected-path.json';p=call(bad)
    assert p.returncode!=0 and not (v/'rejected-path.json').exists();rows.append({'test':'reject path escape','passed':True})
    clip=v/'valid.mp4'
    subprocess.run([ff,'-v','error','-nostdin','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24:duration=2','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2','-filter_complex','[1:a]pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=9[a]','-map','0:v','-map','[a]','-c:v','libx264','-threads','2','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-ar','48000',str(clip)],capture_output=True,check=True)
    cmd=[R/'scripts/verify_delivery.py','--config',config,'--video',clip,'--report',v/'good.json'];p=call(cmd)
    assert p.returncode==0,(p.stdout.decode(),p.stderr.decode());qa=read(v/'good.json');assert qa['full_decode_passed'] and not qa['asr_checked'] and not qa['manual_reviewed']
    rows.append({'test':'decode/loudness on a real fixture without false ASR/manual claims','passed':True})
    p=call(cmd[:-1]+[v/'wrong-size.json','--width','640']);assert p.returncode==2 and 'Unexpected video dimensions' in read(v/'wrong-size.json')['errors'];rows.append({'test':'reject wrong dimensions','passed':True})
    silent=v/'missing-audio.mp4';subprocess.run([ff,'-v','error','-nostdin','-y','-i',str(clip),'-an','-c:v','copy',str(silent)],check=True,capture_output=True)
    p=call([R/'scripts/verify_delivery.py','--config',config,'--video',silent,'--report',v/'no-audio.json']);assert p.returncode==2 and not read(v/'no-audio.json')['full_decode_passed'];rows.append({'test':'reject missing final audio','passed':True})
    p=call([R/'scripts/doctor.py','--config',config]);assert p.returncode==2 and json.loads(p.stdout)['status']=='missing_setup';rows.append({'test':'report missing setup without model inference','passed':True})
    write(v/'acceptance.json',{'status':'passed','tests':rows,'gpu_requests':0,'model_downloads':0,'cross_machine_generation_tested':False})
    print('HELPER_ACCEPTANCE_PASSED',len(rows),'tests; records:',v)

if __name__=='__main__':main()
