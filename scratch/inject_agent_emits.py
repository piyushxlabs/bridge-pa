import re, os

agents = [
    ('src/agents/criteria_evaluation.py', 'criteria_evaluation_node', 5, 'Criteria Evaluation'),
    ('src/agents/data_entry.py', 'data_entry_node', 7, 'Data Entry'),
    ('src/agents/sla_monitor.py', 'sla_monitor_node', 8, 'SLA Monitor'),
]

IMPORT = 'from src.api.streaming.sse_emitter import sse_emitter'

for filepath, func_name, step_num, step_label in agents:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'sse_emitter' in content:
        print(f'SKIP {filepath}')
        continue
    # Add import after last import line
    lines = content.split('\n')
    last_import = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import = i
    lines.insert(last_import + 1, IMPORT)
    content = '\n'.join(lines)
    # Inject entry emit after docstring
    pattern = re.compile(
        r'(async def ' + func_name + r'\(state: Dict\[str, Any\]\) -> Dict\[str, Any\]:\n    """.*?"""\n)(    # Precondition)',
        re.DOTALL
    )
    repl = (
        r'\g<1>'
        '    case_id: str = state.get("user_intent", {}).get("case_id", "")\n'
        f'    await sse_emitter.emit_step_started(case_id, {step_num}, "{step_label}", "{func_name}")\n\n'
        '    # Precondition'
    )
    new_content = pattern.sub(repl, content, count=1)
    # Add completed emit before return
    return_key = '"' + func_name + '_executed": True'
    emit_line = f'    await sse_emitter.emit_step_completed(case_id, {step_num}, "{step_label}", "{func_name}")\n    return {{'
    new_content = new_content.replace(
        '    return {' + '"' + func_name + '_executed": True',
        f'    await sse_emitter.emit_step_completed(case_id, {step_num}, "{step_label}", "{func_name}")\n    return {{"' + func_name + '_executed": True'
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'OK  {filepath}')

print('Done.')
