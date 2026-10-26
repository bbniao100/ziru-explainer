"""Complete decode + loudness + picture flags. Does not perform ASR or manual review."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
from doctor import load_config, executable

def run(exe,args):
    p=subprocess.run([exe,'-hide_banner','-nostdin',*map(str,args)],capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf8','replace')[-2500:])
    return p.stderr.decode('utf8','replace')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',required=True);ap.add_argument('--video',required=True);ap.add_argument('--report',required=True)
    ap.add_argument('--width',type=int);ap.add_argument('--height',type=int);args=ap.parse_args()
    cfg,base=load_config(args.config);target=cfg['delivery'];ff=executable(base,cfg['paths']['ffmpeg']);fp=executable(base,cfg['paths']['ffprobe'])
    if not ff or not fp:raise RuntimeError('Install/configure ffmpeg and ffprobe first')
    video=Path(args.video).resolve();out=Path(args.report)
    if out.exists():raise FileExistsError('Preserve previous evidence; choose a new report name')
    metadata=json.loads(subprocess.run([fp,'-v','error','-show_format','-show_streams','-of','json',str(video)],capture_output=True,check=True).stdout)
    vs=[s for s in metadata['streams'] if s['codec_type']=='video'];aus=[s for s in metadata['streams'] if s['codec_type']=='audio']
    errors=[]
    if len(vs)!=1 or len(aus)!=1:errors.append('Expected one video and one final audio track')
    level=None;flags='';decoded=False
    if vs and aus:
        run(ff,['-v','error','-threads','2','-i',video,'-f','null','-']);decoded=True
        v=vs[0];a=aus[0];fps_num,fps_den=map(int,v['avg_frame_rate'].split('/'))
        if (int(v['width']),int(v['height']))!=(args.width or target['width'],args.height or target['height']):errors.append('Unexpected video dimensions')
        if abs(fps_num/fps_den-target['fps'])>.001:errors.append('Unexpected frame rate')
        if v.get('pix_fmt')!='yuv420p':errors.append('Expected browser-compatible yuv420p')
        if int(a.get('sample_rate',0))!=48000 or a.get('channels')!=2:errors.append('Expected 48kHz stereo final audio')
        log=run(ff,['-v','info','-threads','2','-i',video,'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'])
        level=json.loads(re.findall(r'\{\s*"input_i".*?\}',log,re.S)[-1])
        if abs(float(level['input_i'])-target['program_lufs'])>target['lufs_tolerance']:errors.append('Program loudness outside target')
        if float(level['input_tp'])>target['true_peak_limit']:errors.append('True peak above limit')
        flags=run(ff,['-v','info','-threads','2','-i',video,'-an','-vf','blackdetect=d=0.08:pix_th=0.03:pic_th=0.98,freezedetect=n=-55dB:d=1.5','-f','null','-'])
    black=[{'start':float(x),'end':float(y),'duration':float(z)} for x,y,z in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',flags)]
    if black:errors.append('Black picture events require explicit review')
    holds=[{'kind':k,'seconds':float(v)} for k,v in re.findall(r'freeze_(start|duration|end): ([\d.]+)',flags)]
    digest=hashlib.sha256()
    with video.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
    report={'status':'file_machine_checks_passed' if not errors else 'failed','errors':errors,'full_decode_passed':decoded,'loudness':level,'black_events':black,'freeze_markers_to_review':holds,'sha256':digest.hexdigest(),'metadata':metadata,'asr_checked':False,'manual_reviewed':False,'limits':'Not full production acceptance: final ASR, subtitles, every freeze flag and subjective audiovisual review remain separate.'}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(report['status'],out);return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(main())
