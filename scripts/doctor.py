"""Read-only path/node inspection. No model import, GPU query, download or inference."""
from pathlib import Path
import argparse, importlib.util, json, shutil, subprocess, urllib.request, urllib.parse

def load_config(path):
    path=Path(path).resolve()
    return json.loads(path.read_text(encoding='utf-8-sig')),path.parent

def resolve(base,value):
    p=Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (base/p).resolve()

def executable(base,value):
    return shutil.which(value) or (str(resolve(base,value)) if resolve(base,value).is_file() else None)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',required=True);ap.add_argument('--check-comfy',action='store_true');args=ap.parse_args()
    cfg,base=load_config(args.config);paths=cfg['paths'];checks=[]
    for tool in ('ffmpeg','ffprobe'):
        exe=executable(base,paths[tool]);ok=False
        if exe:
            try:ok=subprocess.run([exe,'-version'],capture_output=True,timeout=10).returncode==0
            except (OSError,subprocess.TimeoutExpired):pass
        checks.append({'item':tool,'ok':ok})
    root=resolve(base,paths['model_root'])
    for key,folder in [('unet','diffusion_models'),('text_encoder','text_encoders'),('video_vae','vae'),('audio_vae','vae'),('lora','loras')]:
        p=root/folder/Path(cfg['h3'][key].replace('\\','/'));checks.append({'item':key,'ok':p.is_file(),'size_GiB':round(p.stat().st_size/1024**3,3) if p.is_file() else None})
    for folder in ('comfy_root','comfy_input'):
        checks.append({'item':folder,'ok':resolve(base,paths[folder]).is_dir()})
    modules={m:importlib.util.find_spec(m) is not None for m in ('PIL','numpy','cv2')}
    required=sorted({x['class_type'] for x in json.loads((Path(__file__).resolve().parents[1]/'assets/h3-one-window.api.template.json').read_text(encoding='utf8')).values()})
    missing_nodes=None
    if args.check_comfy:
        parsed=urllib.parse.urlparse(cfg['comfy_url'])
        if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1','::1') or parsed.username or parsed.password:raise ValueError('Only unauthenticated loopback HTTP inspection is supported')
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(cfg['comfy_url'].rstrip('/')+'/object_info',timeout=15) as response:available=json.load(response)
            missing_nodes=sorted(set(required)-set(available));checks.append({'item':'ComfyUI node classes','ok':not missing_nodes})
        except (OSError,ValueError) as exc:checks.append({'item':'ComfyUI node endpoint','ok':False,'error_type':type(exc).__name__})
    result={'status':'path_checks_passed' if all(x['ok'] for x in checks) else 'missing_setup','checks':checks,'cpu_graphics_modules':modules,'missing_nodes':missing_nodes,'limits':'No GPU/model execution or ASR/TTS environment validation; class presence does not validate input schemas or output quality.'}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if all(x['ok'] for x in checks) else 2

if __name__=='__main__':raise SystemExit(main())
