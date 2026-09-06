#!/usr/bin/env python3
"""Validate and import Grok research. Collection is performed by the Codex heartbeat."""
import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X_URL = re.compile(r'https://x\.com/([A-Za-z0-9_]+)/status/(\d+)$')
SECTIONS = {'opportunities': 'cards', 'updates': 'updates', 'discussions': 'discussions'}

def stamp(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('Timestamps must include UTC offset')
    return t.astimezone(timezone.utc)

def read(path, fallback=None):
    return json.loads(path.read_text()) if path.exists() else fallback

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.grok-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def validate(payload):
    start, end = stamp(payload['window_start']), stamp(payload['window_end'])
    if not timedelta(0) < end-start <= timedelta(hours=49):
        raise ValueError('Expected a rolling window of at most 48 hours (+1h tolerance)')
    if end > datetime.now(timezone.utc)+timedelta(minutes=5):
        raise ValueError('Future collection window')
    if payload.get('status') not in ('success', 'partial'):
        raise ValueError('Use fail command for unsuccessful runs')
    posts = {}
    for p in payload['posts']:
        m = X_URL.fullmatch(p['url'])
        if not m:
            raise ValueError('Invalid X post URL')
        if p['author_handle'].lstrip('@').lower() != m[1].lower():
            raise ValueError('Author / URL mismatch')
        posted = stamp(p['posted_at'])
        if not start <= posted <= end:
            raise ValueError('Post outside collection window')
        snowflake = datetime.fromtimestamp(((int(m[2]) >> 22)+1288834974657)/1000, timezone.utc)
        if abs((posted-snowflake).total_seconds()) > 2:
            raise ValueError('Post ID / timestamp mismatch')
        if not isinstance(p.get('summary_ar'), str) or not p['summary_ar'].strip():
            raise ValueError('Post needs a summary, not an invented original text')
        metrics = p.get('public_metrics')
        if metrics is not None:
            if not isinstance(metrics, dict):
                raise ValueError('Metrics must be an object or null')
            for value in metrics.values():
                if value is not None and (isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0):
                    raise ValueError('Invalid observed metric')
        posts[p['url']] = p
    signals=[]
    seen=set()
    for c in payload['signals']:
        if c.get('section') not in SECTIONS:
            raise ValueError('Unknown section')
        if c.get('audience_fit') != 'general' or c.get('editorial_status') != 'approved':
            raise ValueError('Require a reviewed card useful to general readers')
        if c.get('benefit_type') not in ('income','time','decision','everyday'):
            raise ValueError('Specify a practical reader benefit')
        limits={'title_ar':12,'what_happened_ar':45,'why_it_matters_ar':35,'audience_ar':15,'opportunity_ar':35,'example_ar':30,'caveat_ar':40}
        for field,limit in limits.items():
            if len(str(c.get(field,'')).split()) > limit:
                raise ValueError('Shorten editorial field '+field)
        key=c.get('story_key','')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,100}',key):
            raise ValueError('Need stable topic story_key')
        if key in seen:
            raise ValueError('Duplicate story; merge before import')
        seen.add(key)
        for field in ['title_ar','what_happened_ar','why_it_matters_ar','audience_ar','opportunity_ar','example_ar','caveat_ar']:
            if not isinstance(c.get(field),str) or not c[field].strip():
                raise ValueError('Missing editorial field '+field)
        if not isinstance(c.get('first_steps_ar'),list) or len(c['first_steps_ar']) != 3 or not all(isinstance(x,str) and x.strip() for x in c['first_steps_ar']):
            raise ValueError('Need three clear steps')
        if any(len(x.split()) > 15 for x in c['first_steps_ar']):
            raise ValueError('Shorten trial steps')
        urls=c.get('source_urls')
        if not isinstance(urls,list) or not urls or not all(u in posts for u in urls):
            raise ValueError('Signal citation absent from this run research')
        c=dict(c)
        c.update(id='grok:'+key, content_kind='grok_editorial_proposal',
                 verification_status='needs_verification',
                 source_posted_at=max(posts[u]['posted_at'] for u in urls),
                 evidence_label_ar='ملخص منشور؛ الاستخدام المقترح استنتاج تحريري',
                 collection_window_start=payload['window_start'], collection_window_end=payload['window_end'])
        for field in ['confidence','confidence_score','profit','revenue','importance_score']:
            c.pop(field,None)
        signals.append(c)
    coverage=payload.get('coverage',[])
    if not isinstance(coverage,list) or not coverage:
        raise ValueError('Coverage is required, including searched accounts without results')
    for c in coverage:
        if not re.fullmatch(r'@?[A-Za-z0-9_]{1,15}',c.get('handle','')) or c.get('status') not in ('found','no_results','failed'):
            raise ValueError('Invalid account coverage row')
    return posts,signals


def cycle_status(payload, snapshot, posts, signals, digest):
    return {'status':payload['status'],'last_attempt_at':datetime.now(timezone.utc).isoformat(),
            'last_success_at':snapshot['generated_at'],'window_end':payload['window_end'],
            'run_id':digest,'run_kind':payload.get('run_kind','scheduled_collection'),'posts':len(posts),'signals':len(signals),
            'counts':{k:len(snapshot[v]) for k,v in SECTIONS.items()},
            'coverage_count':len(payload['coverage']),
            'metrics_available':sum(p.get('public_metrics') is not None for p in posts.values())}


def ingest(root,payload):
    posts,signals=validate(payload)
    expected={h.lstrip('@').lower() for h in read(root/'data/grok/config.json',{}).get('accounts',[])}
    covered={c['handle'].lstrip('@').lower() for c in payload['coverage']}
    if expected-covered:
        raise ValueError('Coverage missing configured accounts; include failed rows for incomplete batches')
    if payload['status']=='success' and any(c['status']=='failed' for c in payload['coverage']):
        raise ValueError('Failed account searches require partial status')
    folder=root/'data/grok'
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'.cycle.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=root/'data/radar/grok_opportunities.json'
        prior=read(path,{})
        if prior.get('window_end') and stamp(payload['window_end']) < stamp(prior['window_end']):
            raise ValueError('Refusing to replace a newer snapshot')
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
        if prior.get('run_id') == digest:
            atomic(folder/'status.json',cycle_status(payload,prior,posts,signals,digest))
            return {'status':'unchanged','run_id':digest}
        new_keys={c['id'] for c in signals}
        new_sources={tuple(sorted(c['source_urls'])) for c in signals}
        snapshot={k:v for k,v in prior.items() if k not in SECTIONS.values()}
        for section,dest in SECTIONS.items():
            # Keep recent previous cards on partial/empty results, prune only by source time.
            old=[c for c in prior.get(dest,[]) if c.get('id') not in new_keys and not (not c.get('story_key') and tuple(sorted(c.get('source_urls',[]))) in new_sources) and c.get('source_posted_at') and stamp(c['source_posted_at'])>=stamp(payload['window_start'])]
            snapshot[dest]=[c for c in signals if c['section']==section]+old
        snapshot.update(schema_version='grok-radar-cycle-v1',source='Grok web / X Search',
                        generated_at=datetime.now(timezone.utc).isoformat(),window_start=payload['window_start'],
                        window_end=payload['window_end'],run_id=digest,exhaustive=False,
                        automatic_publication_ready=False,coverage=payload['coverage'],
                        card_count=len(snapshot['cards']))
        snapshot['run_status']=payload['status']
        # Archive both input and previous good snapshot before swapping the UI feed.
        atomic(folder/'runs'/f'{digest}.json',payload)
        if prior:
            atomic(folder/'snapshots'/f'{digest}-previous.json',prior)
        atomic(path,snapshot)
        status=cycle_status(payload,snapshot,posts,signals,digest)
        atomic(folder/'status.json',status)
        return status

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='cmd',required=True)
    for name in ('validate','import'):
        sub.add_parser(name).add_argument('input',type=Path)
    sub.add_parser('fail').add_argument('reason')
    sub.add_parser('plan')
    args=parser.parse_args()
    if args.cmd=='plan':
        now=datetime.now(timezone.utc)
        cfg=read(ROOT/'data/grok/config.json',{})
        priority={h.lower():i for i,h in enumerate(cfg.get('account_priority',[]))}
        accounts=sorted(cfg.get('accounts',[]),key=lambda h:priority.get(h.lower(),len(priority)))
        print(json.dumps({'window_start':(now-timedelta(hours=48)).isoformat(),'window_end':now.isoformat(),
                          'accounts':accounts,'batch_size':10,'runbook':'docs/grok-radar-workflow.md'},ensure_ascii=False))
    elif args.cmd=='fail':
        p=ROOT/'data/grok/status.json'; status=read(p,{})
        status.update(status='failed',last_attempt_at=datetime.now(timezone.utc).isoformat(),error=args.reason)
        atomic(p,status);print(json.dumps(status,ensure_ascii=False))
    else:
        data=read(args.input)
        if args.cmd=='validate':
            posts,signals=validate(data);print(json.dumps({'valid':True,'posts':len(posts),'signals':len(signals)}))
        else:
            print(json.dumps(ingest(ROOT,data),ensure_ascii=False))

if __name__=='__main__':
    main()
