"""Bind one short H3 API graph. Writes a request, never contacts/submits to ComfyUI."""
from pathlib import Path, PurePosixPath
import argparse, json, uuid
from doctor import load_config

def input_name(value):
    p=PurePosixPath(value.replace('\\','/'))
    if p.is_absolute() or '..' in p.parts or ':' in value or not p.parts:raise ValueError('Image/audio must be relative names inside ComfyUI input')
    return str(p)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ('config','prompt','image','audio','out'):ap.add_argument('--'+arg,required=True)
    args=ap.parse_args();cfg,_=load_config(args.config);h=cfg['h3']
    if (h['width'],h['height'],h['frames'],h['fps'])!=(1024,576,124,24):raise ValueError('This binder implements the validated 1024x576/124frame/24fps profile only; adapt/test other profiles separately')
    if h['steps'] not in (4,6,8):raise ValueError('Turbo baseline accepts actual sampling steps 4,6 or8')
    prompt=Path(args.prompt).read_text(encoding='utf-8-sig').strip()
    for token in ('subject_definitions:','summary:','retention_analysis:','detailed_description:','overall_soundscape:','non_diegetic_music:','<Picture 1>','<Audio 1>','<d>','</d>'):
        if token not in prompt:raise ValueError('Missing source-audio prompt field: '+token)
    g=json.loads((Path(__file__).resolve().parents[1]/'assets/h3-one-window.api.template.json').read_text(encoding='utf8'))
    for node,key in [('1','unet'),('3','text_encoder'),('4','video_vae'),('5','audio_vae'),('2','lora')]:
        field={'1':'unet_name','3':'clip_name','4':'vae_name','5':'vae_name','2':'lora_name'}[node];g[node]['inputs'][field]=h[key]
    g['2']['inputs'].update(strength=h['lora_strength'],low_vram=h['low_vram'])
    g['6']['inputs'].update(chain_id='explainer_'+uuid.uuid4().hex,total_duration_seconds=h['frames']/h['fps'],segment_prompts_json=json.dumps([{'prompt':prompt}],ensure_ascii=False),base_seed=h['seed'],steps=h['steps'])
    g['19']['inputs']['image']=input_name(args.image);g['21']['inputs']['audio']=input_name(args.audio)
    g['13']['inputs']['model_id']='ziru_explainer_one_window'
    assert g['16']['inputs']['accept_candidate'] is False
    for node in g.values():
        for v in node['inputs'].values():
            if isinstance(v,list) and len(v)==2 and isinstance(v[0],str):assert v[0] in g
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf8') as f:json.dump(g,f,ensure_ascii=False,indent=2)
    print('REQUEST_WRITTEN_NOT_SUBMITTED',output)

if __name__=='__main__':main()
