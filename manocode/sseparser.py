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

def add_json(d, path, value):
    if not path:
        return value
    key = int(path[0]) if path[0].isdigit() else path[0]
    if len(path) == 1:
        if isinstance(d, list):
            if key == '-':
                d.append(value)
            else:
                d.insert(key, value)
            return d
        elif isinstance(d, dict):
            d[key] = value
            return d
    d[key] = add_json(d[key], path[1:], value)
    return d

def write_op(op, p, val, d):
    if op == 'patch':
        for sub_op in val:
            if not {'o', 'p', 'v'}.issubset(sub_op):
                continue
            s_op = sub_op['o']
            s_p = sub_op['p']
            s_val = sub_op['v']
            if s_val != None:
                d = write_op(s_op, s_p, s_val, d)
    elif op == 'append':
        d = append_json(d, p.split('/')[1:], val)
    elif op == 'replace':
        d = replace_json(d, p.split('/')[1:], val)
    elif op == "add":
        d = add_json(d, p.split('/')[1:], val)
    return d

def parse_chatgpt_patch(datas):
    final = {}
    current_op = {}
    token_streaming = False
    for data in datas:
        if not isinstance(data, dict):
            continue
        if data.get('o'):
            current_op['o'] = data.get('o')
        if data.get('p', None) is not None:
            current_op['p'] = data.get('p')
        if data.get('marker') == 'user_visible_token' and data.get('event') == 'first':
            token_streaming = True
        if data.get('marker') == 'last_token':
            token_streaming = False
        if data.get('v'):
            val = data['v']
            final = write_op(current_op['o'], current_op['p'], val, final)
            json.dump(final, open("final.json", 'w'))
    return final

def get_message_chatgpt_patch(resp):
    try:
        return resp['message']['content']['parts'][0]
    except (KeyError, TypeError, IndexError):
        return None
