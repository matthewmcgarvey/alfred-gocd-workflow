# encoding: utf-8
import sys
from workflow import Workflow3, ICON_WEB, web

def get_config(wf):
    config = wf.stored_data('config')
    if config is None:
        return {}
    return config

def save_config(wf, config):
    wf.store_data('config', config)

def get_password(wf):
    try:
        return wf.get_password("alfred-gocd-pw")
    except:
        return None

def save_password(wf, pw):
    wf.save_password("alfred-gocd-pw", pw)

def configured(wf):
    return (not (not get_config(wf))) and (get_password(wf) is not None)

def warn_if_not_configured(wf):
    if not configured(wf):
        wf.add_item("You must configure the workflow before using it.", icon=ICON_WARNING)
        wf.send_feedback()
        sys.exit(1)

def load_pipelines(wf):
    data = wf.stored_data("pipelines")
    if data is not None and len(data):
        wf._items = data
        return
    config = get_config(wf)
    base_url = config["base_url"]
    url = "%s/go/api/config/pipeline_groups" % base_url
    username = config["username"]
    password = get_password(wf)

    r = web.get(url, auth=(username, password))
    r.raise_for_status()
    data = r.json()
    pipelines = [pipeline['name']
                    for group in data
                    for pipeline in group['pipelines']]
    items = []
    for pipeline in pipelines:
        pipeline_url = "%s/go/tab/pipeline/history/%s" % (base_url, pipeline)
        item = wf.add_item(title=pipeline,
                            subtitle=pipeline_url,
                            arg=pipeline_url,
                            uid=pipeline_url,
                            valid=True)
        items.append(item)
    wf.store_data('pipelines', items)


def main(wf):
    args = wf.args
    if not args:
        warn_if_not_configured(wf)
        load_pipelines(wf)
        wf.send_feedback()
        return

    keyword_arg = args[0]
    
    if keyword_arg == '--auth-un':
        username = args[1]
        config = get_config(wf)
        config['username'] = username
        save_config(wf, config)
        return
    elif keyword_arg == '--auth-pw':
        pw = " ".join(args[1:])
        save_password(wf, pw)
        return
    elif keyword_arg == '--baseurl':
        base_url = args[1]
        config = get_config(wf)
        config['base_url'] = base_url
        save_config(wf, config)
        return
    elif keyword_arg == "--refresh":
        warn_if_not_configured(wf)
        wf.clear_data(lambda f: "pipelines" in f)
        load_pipelines(wf)
        return
    else:
        query = keyword_arg
        pipelines = wf.stored_data("pipelines")
        items = wf.filter(query, pipelines)
        if not items:
            wf.add_item('No matches', icon=ICON_WARNING)
        for item in items:
            wf.add_item(title=item['title'], subtitle=item['subtitle'], arg=item['arg'], uid=item['uid'], valid=True)
        wf.send_feedback()



if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))