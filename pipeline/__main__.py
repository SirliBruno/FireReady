from pathlib import Path
import argparse,json,sys
from pipeline.core import ingest,BBOX

def main():
    parser=argparse.ArgumentParser(prog='python -m pipeline')
    sub=parser.add_subparsers(dest='command',required=True)
    cmd=sub.add_parser('ingest');cmd.add_argument('--config',default='config/maui.json');cmd.add_argument('--mode',required=True,choices=['real','synthetic']);cmd.add_argument('--input');cmd.add_argument('--output')
    pub=sub.add_parser('publish');pub.add_argument('--reviewer',required=True);pub.add_argument('--evidence',required=True);pub.add_argument('--source-url',required=True)
    sub.add_parser('freeze-harmonization');sub.add_parser('harmonize');sub.add_parser('publish-research-preview')
    args=parser.parse_args();root=Path.cwd().resolve()
    if args.command=='publish-research-preview':
        from pipeline.harmonization import publish_research_preview
        result=publish_research_preview(root/'data/processed/real',root/'data/processed/harmonization/real',root/'public/data',root/'data/raw')
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    if args.command in ('freeze-harmonization','harmonize'):
        from pipeline.harmonization import freeze_reference,run_harmonization
        source=root/'data/processed/real';dest=root/'data/processed/harmonization/real'
        result=freeze_reference(source,dest) if args.command=='freeze-harmonization' else run_harmonization(source,dest)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    if args.command=='publish':
        from pipeline.publish import publish
        publish(root/'data/processed/real',root/'public/data',reviewer=args.reviewer,evidence=args.evidence,source_url=args.source_url,raw_root=root/'data/raw')
        print('Reviewed outputs published to public/data; source authenticity remains the reviewer responsibility.')
        return 0
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    if cfg.get('start_utc')!='2013-01-01' or cfg.get('end_utc')!='2023-12-31':parser.error('study period is fixed at 2013–2023 UTC')
    bbox=tuple(cfg.get('bbox',BBOX))
    if len(bbox)!=4 or any(not isinstance(x,(int,float)) for x in bbox) or bbox[0]>=bbox[2] or bbox[1]>=bbox[3]:parser.error('invalid bbox')
    default_input=root/('data/raw' if args.mode=='real' else 'data/fixtures/firms')
    source=Path(args.input).resolve() if args.input else default_input.resolve()
    allowed=default_input.resolve()
    if source!=allowed and allowed not in source.parents:parser.error('input must stay within the selected mode input directory')
    allowed_output=(root/'data/processed'/args.mode).resolve();output=Path(args.output).resolve() if args.output else allowed_output
    if output!=allowed_output and allowed_output not in output.parents:parser.error('output must stay within data/processed/<mode>')
    boundary=cfg.get('boundary_path')
    if boundary is not None and not Path(boundary).is_file():parser.error('configured boundary is missing; explicitly remove boundary_path for provisional bbox-only mode')
    result=ingest(source,output,classification=args.mode,bbox=bbox,boundary_path=boundary)
    print(json.dumps({'output':str(output),'counts':result['counts'],'file_errors':result['file_errors']},ensure_ascii=False,indent=2))
    return 2 if result['file_errors'] else 0
if __name__=='__main__':sys.exit(main())
