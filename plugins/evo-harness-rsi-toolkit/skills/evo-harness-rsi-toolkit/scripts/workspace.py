"""Data-only native Workspace continuation, retaining the original Solver Session.

An evaluator grades the already completed training execution; this module never
executes a Target, calls a model, reads a rubric or chooses the next phase.
"""
import json
import shlex
import re
import shutil
import os
from pathlib import Path
import evo
import benchmarks


def prepare_profile(req):
    plan,contract,budget=benchmarks.frozen_plan(req)
    evo.require(contract['adapter']=='native-cases-v1' and contract['capabilities']['complete_live_rsi'],
                'this backend cannot continue an original Solver')
    evo.require(contract.get('test_package') and contract.get('test_cases'), 'missing held-out roster')
    token=evo.digest(str(Path(req['output']).resolve()).encode())[:12]
    root=Path(req['output']).parent/('workspace-learning-'+token)
    target=req.get('test_agent_id','evo-'+token+'-target')
    state=Path(plan['project'])/'agents'/target/'agent_state'
    missing=[]
    config_path=state/'system_config.yaml'
    if not config_path.is_file():missing.append('initialized Target State')
    else:
        import yaml
        configuration=yaml.safe_load(config_path.read_text())
        if configuration.get('model',{}).get('thinking_level')!=plan['runtime']['thinking_level']:
            missing.append('Target model.thinking_level must match frozen runtime')
    if missing:return {'ready':False,'proposed_target_id':target,'target_state':str(state),'missing_configuration':missing,'model_calls':0}
    version=configuration.get('version',1)
    evo.require(type(version) is int and version>0,'invalid native State version')
    members=[{'case_id':c['case_id'],'task_id':c['case_id'] if evo.IDENT.fullmatch(c['case_id']) else 'task-'+evo.digest((contract['benchmark']+'/'+c['case_id']).encode())[:24]}for c in contract['cases']]
    value={'protocol':'evo-native-workspace-v1','method_version':'2026.10.28.2','learning_version':'2026.10.23.6',
           'source_commit':plan['source_commit'],'parent_plan':req['plan'],'parent_plan_sha256':req['plan_sha256'],
           'project':plan['project'],'contract':contract,'runtime':plan['runtime'],'budget_usd':budget,
           'budget_scope':plan['budget_scope'],'authorized_total_usd':plan['authorized_total_usd'],
           'members':members,'train_ids':[m['task_id']for m in members],
           'test_case_ids':[c['case_id']for c in contract['test_cases']],
           'test_agent_id':target,'target_state':str(state),'expected_version':version,'h0_files':state_files(state),'limits':plan['algorithm']['limits'],
           'max_bytes':plan['algorithm']['max_bytes'],'general_storage':plan['algorithm']['general_storage'],
           'test_repeats':plan['algorithm']['test_repeats'],'context_transport':'agents-md-v1',
           'controller_workspace':str(Path(req.get('workspace',os.getcwd())).resolve()),
           'public_files':{c['case_id']:evo.filemap(Path(c['statement']).parent)for c in contract['cases']},
           'private_learning':str(root),'library':str(root/'compiled-library.json'),'skill_output':str(root/'exported-skill')}
    evo.write_once(req['output'],evo.encoded(value))
    return {'ready':True,'profile':req['output'],'sha256':benchmarks.sha(req['output']),'model_calls':0,'dispatches':0}


def prepare_export(req):
    evo.require(benchmarks.sha(req['profile'])==req['profile_sha256'],'frozen Workspace profile changed')
    p=evo.read(req['profile'])
    evo.require(p['protocol']=='evo-native-workspace-v1' and p['general_storage']=='description-only', 'loading policy differs')
    operation={'op':'export','library':p['library'],'output':p['skill_output'],
               'limits':p['limits'],'max_bytes':p['max_bytes'],'general_storage':p['general_storage']}
    evo.write_once(req['output'],evo.encoded(operation))
    return {'request':req['output'],'sha256':benchmarks.sha(req['output']),
            'command':shlex.join(['python3','-B',str(Path(evo.__file__).resolve()),req['output']]),
            'model_calls':0,'dispatches':0}


def state_files(state):
    return {k:v for k,v in evo.filemap(state).items() if k.split('/')[0] not in ('.vault.toml','memory','schedule')}


def bound_request(req, check_state=False):
    evo.require(req.get('profile') and req.get('profile_sha256'),'frozen Workspace profile required')
    evo.require(benchmarks.sha(req['profile'])==req['profile_sha256'],'Workspace profile changed')
    p=evo.read(req['profile'])
    evo.require(p['protocol']=='evo-native-workspace-v1','wrong Workspace profile')
    member=[m for m in p['members']if m['case_id']==req['case_id']]
    evo.require(len(member)==1,'Case is not in frozen training roster')
    task=member[0]['task_id']
    public=Path(p['controller_workspace'])/('evo-public-'+evo.digest(str(Path(req['profile']).resolve()).encode())[:12])/task
    outputs=Path(p['private_learning'])/task
    expected={'task_id':task,'train_ids':p['train_ids'],'runtime':p['runtime'],'test_agent_id':p['test_agent_id'],
              'answer':str(outputs/'answer.txt'),'candidate':str(outputs/'candidates.json'),
              'inputs':[str(public/name)for name in p['public_files'][req['case_id']]]}
    for key,value in expected.items():
        evo.require(key not in req or req[key]==value,'request differs from frozen Workspace '+key)
    if check_state:evo.require(state_files(p['target_state'])==p['h0_files'],'training State changed from frozen H0')
    return {**req,**expected},p


def prepare_solver(req):
    req,profile=bound_request(req,check_state=True)
    public=Path(req['inputs'][0]).parent
    # Public package files only. Source rubric/test material is never staged.
    entry=next(c for c in profile['contract']['cases']if c['case_id']==req['case_id'])
    source=Path(entry['statement']).parent
    task_public=Path(profile['controller_workspace'])/('evo-public-'+evo.digest(str(Path(req['profile']).resolve()).encode())[:12])/req['task_id']
    if not task_public.exists():
        task_public.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(source,task_public,symlinks=True)
    evo.require(evo.filemap(task_public)==profile['public_files'][req['case_id']], 'public training staging differs from frozen source')
    Path(req['answer']).parent.mkdir(parents=True,exist_ok=True)
    evo.require(req["split"] == "train" and req["task_id"] in req["train_ids"], "training only")
    roles=(Path(evo.__file__).parent.parent/"references/roles.md").read_text()
    common=roles.split("For ordinary RSI",1)[0]
    reflection="## In-session reflection"+roles.split("## In-session reflection",1)[1].split("## Evolver",1)[0]
    grant={"evo_workspace_task":{**{k:req[k]for k in("task_id","attempt_id","answer","candidate")},"profile_sha256":req["profile_sha256"]}}
    prompt=(common+"\nNative Workspace Solver: read only these public inputs, solve once and write the assigned answer. "
            "Return without grading. Your original Session will receive one actual feedback continuation; "
            "keep history and do not generate candidates before it. The following .6 reflection section "
            "applies only after that feedback. This is unguarded RSI: use the supplied fixed digest seal, "
            "not the continuous-container API or seal-role-output entry.\n"
            +json.dumps({"public_inputs":req["inputs"]},ensure_ascii=False)+"\n"+json.dumps(grant,ensure_ascii=False)+"\n"+reflection
            +"\n"+json.dumps(evo.candidate_contract(req["task_id"],req["attempt_id"],req["inputs"],req["candidate"]),ensure_ascii=False))
    evo.write_once(req["output"],prompt.encode())
    return {"scope":req,"call":{"agent_id":req["test_agent_id"],"description":"Evo original Workspace Solver "+req["task_id"],
                    "prompt_file":req["output"],"prompt_sha256":evo.digest(prompt.encode()),
                    **{k:req["runtime"][k]for k in("provider","model_id","thinking_level")},"run_in_background":True},
            "model_calls":0,"dispatches":0}


def original_handle(req, view):
    paths=req.get("parent_traces",[req["binding"]["parent_trace"]])
    rows=[json.loads(line) for p in paths for line in evo.regular(p).read_bytes().splitlines()]
    metas=[r["payload"] for r in rows if r.get("type")=="session_meta" and not r.get("origin")]
    evo.require(metas and len({m["session_id"]for m in metas})==1,"one original parent required")
    binding={k:metas[0][k]for k in("session_id","source","provider","model_id","workspace","agent_state")}
    evo.require(binding["agent_state"]!=req["binding"]["agent_state"],"Solver must be separate from the controller")
    evo.require(req["evaluator_binding"]["agent_state"]==binding["agent_state"],"evaluator must use the native controller State")
    parent=evo.trace_view(paths,binding)
    prompts=[m["payload"]["text"]for m in view["messages"] if m["payload"].get("type")=="text"
             and m["payload"].get("role")=="user" and m["payload"].get("sender")=="parent_agent"]
    evo.require(prompts,"Solver lacks its initial native parent prompt")
    matches=[]
    for pair in parent["pairs"]:
        call=pair["call"]["payload"]
        output=pair["observation"]["payload"]
        if call.get("name")!="run_subagent" or evo.tool_status(output)!="completed":continue
        args=json.loads(call["arguments"])
        if evo.native_prompt(args)!=prompts[0]:continue
        evo.require(args.get('agent_id')==req['test_agent_id'] and all(args.get(k)==req['runtime'][k]for k in('provider','model_id','thinking_level')), 'actual Solver dispatch differs from frozen runtime/Agent')
        found=re.findall(r"\bsubagent_id ([A-Za-z0-9_-]+);",output["output"])
        if len(found)==1:matches.append(found[0])
    evo.require(matches==[req["subagent_id"]],"handle is not the original native Solver dispatch")
    return matches[0]


def prepare_feedback(req):
    req,profile=bound_request(req,check_state=True)
    evo.require(req['split'] == 'train' and req['task_id'] in req['train_ids'], 'training only')
    view = evo.trace_view(req['traces'], req['binding'])
    evo.require(req['binding']['source'] == req['evaluator_binding']['source'] == 'subagent', 'native Solver and evaluator leaves required')
    original_handle(req, view)
    result = evo.read(req['evaluation'])
    evo.require(result['status'] == 'ok', 'failed scoring is not negative feedback')
    evo.finite(result['score'], high=100)
    for key in ('session_id', 'provider', 'model_id'):
        evo.require(result[key] == req['binding'][key], 'evaluator and original Solver differ')
    evo.require(result['case_id'] == req['case_id'] and result['run'] == 1,
                'evaluation belongs to another task/attempt')
    evo.require(req['evaluator_binding']['session_id'] != req['binding']['session_id'], 'Solver cannot grade itself')
    evo.require(req['binding']['agent_state']==profile['target_state'], 'Solver State differs from frozen profile')
    evo.require(req['binding']['workspace']==profile['controller_workspace'],'Solver did not inherit frozen parent Workspace')
    evo.require(result['expected_version']==profile['expected_version'] and result['thinking_level']==profile['runtime']['thinking_level'], 'evaluation State/thinking differs')
    evo.require(all(req['binding'][k]==profile['runtime'][k]for k in('provider','model_id')), 'Solver model differs from frozen profile')
    evo.require(result['agent_id'] == Path(req['binding']['agent_state']).parent.name, 'evaluation belongs to another Agent')
    evaluator = evo.trace_view(req['evaluator_traces'], req['evaluator_binding'])
    replies = [m['payload']['text'] for m in evaluator['messages']
               if m['payload'].get('type') == 'text' and m['payload'].get('role') == 'assistant']
    # Native protocol permits YAML; compare parsed values, never copy rubric text.
    import yaml
    matched = False
    for text in replies:
        try:
            matched = matched or yaml.safe_load(text) == result
        except yaml.YAMLError:
            pass
    evo.require(matched, 'evaluation is not an actual native worker reply')
    answer = evo.regular(req['answer']).read_bytes()
    grant = {'evo_workspace_task': {'task_id': req['task_id'], 'attempt_id': req['attempt_id'],
                                  'answer': req['answer'], 'candidate': req['candidate'], 'profile_sha256':req['profile_sha256']}}
    evo.require(any(evo.contains_json(m['payload'].get('text', ''), grant)
                    for m in view['messages'] if m['payload'].get('role') == 'user'),
                'original Solver never received this task/answer grant')
    evo.verify_workspace_inputs(view, req['inputs'], req['binding']['workspace'], strict=True)
    negative = result['score'] < 100
    feedback = {'source': 'penguin-evaluation', 'task_id': req['task_id'],
                'attempt_id': req['attempt_id'], 'status': 'ok',
                'answer_sha256': evo.digest(answer), 'score': result['score'] / 100,
                'correct': not negative, 'raw_response': json.dumps(result, ensure_ascii=False)}
    seal_path = str(Path(req['candidate']).parent / 'seal-request.json')
    seal_request = {'op': 'file-digest', 'path': req['candidate']}
    seal_command = shlex.join(['python3', '-B', str(Path(evo.__file__).resolve()), seal_path])
    message = {'evo_workspace_feedback': feedback}
    prompt = ('Your answer is frozen. This is the one actual authorized training feedback; '
              'do not query more task data, change the answer or request another score.\n'
              + json.dumps(message, ensure_ascii=False))
    if negative:
        prompt += ('\nReflect in this SAME Solver conversation using the already supplied .6 '
                   'In-session reflection guidance. Write candidate memories, retaining evidence '
                   'and scope, to your assigned output. A justified [] is allowed.\n'
                   + json.dumps(evo.candidate_contract(req['task_id'], req['attempt_id'],
                                                      req['inputs'], req['candidate']), ensure_ascii=False)
                   + '\nFixed unguarded-RSI seal: write ' + seal_path + ' as ' + json.dumps(seal_request)
                   + '; then execute exactly: ' + seal_command)
    else:
        prompt += '\nSuccessful execution: acknowledge the complete feedback; do not generate candidates.'
    record = {'schema': 'evo-workspace-feedback-v1', 'request': req,
              'feedback': feedback, 'prompt': prompt, 'negative': negative,
              'seal_path': seal_path, 'seal_request': seal_request, 'seal_command': seal_command,
              'evaluation_sha256': evo.digest(evo.regular(req['evaluation']).read_bytes()),
              'answer_sha256': evo.digest(answer), 'initial_trace_sources': view['sources']}
    evo.write_once(req['output'], evo.encoded(record))
    return {'call': {'subagent_id': req['subagent_id'], 'prompt': prompt},
            'record': req['output'], 'model_calls': 0, 'dispatches': 0}


def verify_continuation(record, view, answer, candidate):
    req,profile=bound_request(record['request'])
    evo.require(view['binding'] == req['binding'], 'reflection must retain the original Solver binding')
    evo.require(evo.digest(answer) == record['answer_sha256'], 'answer changed after scoring')
    observed = [i for i, m in enumerate(view['messages'])
                if m['payload'].get('role') == 'user' and m['payload'].get('sender') == 'parent_agent'
                and m['payload'].get('text') == record['prompt']]
    evo.require(len(observed) == 1, 'complete raw feedback must enter original Solver exactly once')
    boundary = observed[0]
    for source in record.get('initial_trace_sources', []):
        raw=evo.regular(source['path']).read_bytes()
        evo.require(evo.digest(raw[:source['bytes']]) == source['sha256'], 'pre-feedback Solver history changed')
    seal_at, last_write = None, None
    for i, m in enumerate(view['messages'][boundary + 1:], boundary + 1):
        payload = m['payload']
        if payload.get('type') != 'tool_call':
            continue
        if payload['tool_call_id'] in view.get('denied_calls', []):
            continue  # Proven pre-execution refusals are audit, not executed actions.
        args = json.loads(payload['arguments'])
        evo.require(record['negative'], 'successful feedback cannot generate or seal candidates')
        if payload['name'] in ('write_file', 'edit_file'):
            path = args.get('file_path')
            evo.require(path in (req['candidate'], record['seal_path']), 'reflection edited a foreign file')
            pair=next((p for p in view['pairs'] if p['call']['payload']['tool_call_id']==payload['tool_call_id']),None)
            evo.require(pair and evo.tool_status(pair['observation']['payload'])=='completed', 'draft write did not complete')
            if path == req['candidate']:
                evo.require(seal_at is None, 'sealed candidates changed')
                last_write = i
            else:
                evo.require(payload['name'] == 'write_file'
                            and json.loads(args['content']) == record['seal_request'], 'seal request changed')
        elif payload['name'] == 'exec_command':
            evo.require(args.get('cmd', args.get('command')) == record['seal_command']
                        and seal_at is None and last_write is not None, 'only the fixed candidate digest is allowed')
            pair = next((p for p in view['pairs'] if p['call']['payload']['tool_call_id'] == payload['tool_call_id']), None)
            evo.require(pair and evo.tool_status(pair['observation']['payload']) == 'completed', 'candidate seal incomplete')
            output = json.loads(pair['observation']['payload']['output'])
            evo.require(output == {'file_path': req['candidate'], 'sha256': evo.digest(candidate)}, 'candidate seal differs')
            seal_at = i
        else:
            raise ValueError('reflection may not query data, change answers or regrade')
    if record['negative']:
        writes = [m for m in view['messages'][boundary + 1:]
                  if m['payload'].get('type') == 'tool_call']
        evo.require(writes and seal_at is not None, 'missing reflection cannot masquerade as an empty candidate set')
        values = json.loads(candidate)
        evo.require(isinstance(values, list), 'candidate memories must be an array')
    else:
        evo.require(candidate is None, 'success does not generate candidates')
    return {'mode': 'solver-session', 'session_id': req['binding']['session_id'],
            'feedback_observed': True, 'answer_sha256': record['answer_sha256'],
            'candidate_sha256': evo.digest(candidate) if candidate is not None else None}


def capture(req):
    record = evo.read(req['feedback_record'])
    original = record['request']
    evo.require(evo.digest(evo.regular(original['evaluation']).read_bytes()) == record['evaluation_sha256'],
                'original evaluation changed')
    view = evo.trace_view(req['traces'], original['binding'])
    answer = evo.regular(original['answer']).read_bytes()
    candidate = evo.regular(original['candidate']).read_bytes() if record['negative'] else None
    reflection = verify_continuation(record, view, answer, candidate)
    # Capture only the terminal trace, after append-only same-Session reflection.
    result = evo.capture({**original, 'op': 'capture-evaluation', 'traces': req['traces'],
                          'output': req['output'], 'evaluation_case_id':original['case_id'], 'workspace_feedback_record': req['feedback_record'], 'evaluation_identity': {
                              **{k: evo.read(original['evaluation'])[k] for k in ('agent_id', 'expected_version', 'provider', 'model_id', 'thinking_level', 'run')}}})
    return {**result, 'reflection': reflection,
            'feedback_record': req['feedback_record'], 'model_calls': 0, 'dispatches': 0}


if __name__ == '__main__':
    import sys
    request = evo.read(sys.argv[1])
    operation = request['op']
    if operation == 'prepare-profile':
        result = prepare_profile(request)
    elif operation == 'prepare-export':
        result = prepare_export(request)
    elif operation == 'prepare-solver':
        result = prepare_solver(request)
    elif operation == 'prepare-feedback':
        result = prepare_feedback(request)
    elif operation == 'capture':
        result = capture(request)
    else:
        raise ValueError('unknown Workspace operation')
    print(json.dumps(result, ensure_ascii=False))
