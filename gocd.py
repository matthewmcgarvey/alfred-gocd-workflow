# encoding: utf-8
import sys
from workflow import Workflow3, ICON_WEB, web, ICON_WARNING, ICON_ERROR

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
        wf.add_item("You must supply a password", icon=ICON_ERROR)
        wf.send_feedback()
        sys.exit(1)

def save_password(wf, pw):
    wf.save_password("alfred-gocd-pw", pw)

def get_username(config):
    username = config.get('username')
    if username is None:
        wf.add_item("You must supply a username", icon=ICON_ERROR)
        wf.send_feedback()
        sys.exit(1)
    else:
        return username

def get_base_url(config):
    base_url = config.get('base_url')
    if base_url is None:
        wf.add_item("You must supply a base url", icon=ICON_ERROR)
        wf.send_feedback()
        sys.exit(1)
    else:
        return base_url

def load_pipelines(wf, config):
    stored_pipelines = wf.stored_data("pipelines") # ["spring-extensions", "skybridge"]
    if stored_pipelines is not None and len(stored_pipelines):
        return stored_pipelines
    base_url = get_base_url(config)
    url = "%s/go/api/config/pipeline_groups" % base_url
    username = get_username(config)
    password = get_password(wf)

    r = web.get(url, auth=(username, password))
    r.raise_for_status()
    data = r.json()
    pipelines = [pipeline['name']
                    for group in data
                    for pipeline in group['pipelines']]
    wf.store_data('pipelines', pipelines)
    return pipelines

def add_item(wf, pipeline, base_url):
    pipeline_url = "%s/go/tab/pipeline/history/%s" % (base_url, pipeline)
    wf.add_item(title=pipeline,
                subtitle=pipeline_url,
                arg=pipeline_url,
                uid=pipeline_url,
                valid=True)

def add_items(wf, pipelines, base_url):
    for pipeline in pipelines:
        add_item(wf, pipeline, base_url)

def main(wf):
    args = wf.args
    config = get_config(wf)
    if not args:
        pipelines = load_pipelines(wf, config)
        add_items(wf, pipelines, get_base_url(config))
        wf.send_feedback()
        return

    keyword_arg = args[0]
    
    if keyword_arg == '--auth-un':
        username = args[1]
        config['username'] = username
        save_config(wf, config)
        return
    elif keyword_arg == '--auth-pw':
        pw = " ".join(args[1:])
        save_password(wf, pw)
        return
    elif keyword_arg == '--baseurl':
        base_url = args[1]
        config['base_url'] = base_url
        save_config(wf, config)
        return
    elif keyword_arg == "--refresh":
        wf.clear_data(lambda f: "pipelines" in f)
        load_pipelines(wf, config)
        return
    else:
        query = keyword_arg
        pipelines = load_pipelines(wf, config)
        items = wf.filter(query, pipelines)
        if not items:
            wf.add_item('No matches', icon=ICON_WARNING)
        else:
            add_items(wf, items, get_base_url(config))
        wf.send_feedback()



if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))