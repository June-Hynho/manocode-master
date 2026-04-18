import json

def custom_parse_sse(raw):
    datas = []
    for line in raw.split('\n\n'):
        if line and (line := line.splitlines()[-1][6:]):
            if line == '[DONE]':
                continue
            datas.append(json.loads(line))
    return datas

def append_json(d, path, value):
    key = int(path[0]) if path[0].isdigit() else path[0]
    if len(path) == 1:
        if isinstance(value, str):
            d[key] += value
            return d
        elif isinstance(value, list):
            d[key].extend(value)
            return d
        elif isinstance(value, dict):
            d[key].update(value)
            return d
        # if none of the above
        return d
    d[key] = append_json(d[key], path[1:], value)
    return d

def replace_json(d, path, value):
    key = int(path[0]) if path[0].isdigit() else path[0]
    if len(path) == 1:
        d[key] = value
        return d
    d[key] = replace_json(d[key], path[1:], value)
    return d

def parse_chatgpt_patch(datas):
    final = {}
    for data in datas:
        if not isinstance(data, dict):
            continue
        if data.get('v') and data['v'].get('message') and data['v']['message'].get('author') and data['v']['message']['author'].get('role') == 'assistant':
            final['message'] = data['v']['message']
            break
    if not final:
        return
    patch = False
    for data in datas:
        if not isinstance(data, dict):
            continue
        if data.get('o') == 'patch':
            patch = True
        if patch:
            for op in data.get('v', []):
                if op['o'] == "append":
                    final = append_json(final, op['p'].split('/')[1:], op['v'])
                elif op['o'] == "replace":
                    final = replace_json(final, op['p'].split('/')[1:], op['v'])
                elif op['o'] == "add":
                    pass
    return final

def get_message_chatgpt_patch(resp):
    try:
        return resp['message']['content']['parts'][0]
    except (KeyError, TypeError, IndexError):
        return None
