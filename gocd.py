# encoding: utf-8
import sys
from workflow import Workflow3, web, ICON_WEB, ICON_WARNING, ICON_ERROR

log = None

def get_config(wf):
    config = wf.stored_data('config')
    if config is None:
        return {}
    return config


def save_config(wf, config):
    wf.store_data('config', config)


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


def load_pipelines(wf, config, password=None, refresh=False):
    if not refresh:
        stored_pipelines = wf.stored_data("pipelines")
        if stored_pipelines is not None and len(stored_pipelines):
            log.debug("Found cached pipelines")
            return stored_pipelines
        log.debug("Did not find cached pipelines, proceeding to load")
    try:
        base_url = get_base_url(config)
        url = "%s/go/api/config/pipeline_groups" % base_url
        username = get_username(config)

        r = web.get(url, auth=(username, password))
        r.raise_for_status()
        data = r.json()
        pipelines = [pipeline['name']
                        for group in data
                        for pipeline in group['pipelines']]
        wf.store_data('pipelines', pipelines)
        return pipelines
    except Exception as e:
        log.exception(e)
        return False


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
    elif keyword_arg == '--baseurl':
        base_url = args[1]
        config['base_url'] = base_url
        save_config(wf, config)
        return
    elif keyword_arg == "--refresh":
        pw = " ".join(args[1:])
        result = load_pipelines(wf, config, pw, refresh=True)
        sys.stdout.write("success" if result else "failure")
        sys.stdout.flush()
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
    log = wf.logger
    sys.exit(wf.run(main))
