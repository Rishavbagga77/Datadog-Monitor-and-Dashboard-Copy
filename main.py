from docopt import docopt
import json
import os
import glob
import requests
from datadog import initialize, api

def _init_options(action):
    config_file = "config.json"
    try:
        with open(config_file) as f:
            config = json.load(f)
    except IOError:
        exit("No configuration file named: {} could be found.".format(config_file))

    options = {}
    if action == "pull":
        options = {
            'api_key': config["source_api_key"],
            'app_key': config["source_app_key"],
            'api_host': config["source_api_host"]
        }
    elif action == "push":
            options = {
                'api_key': config["dest_api_key"],
                'app_key': config["dest_app_key"],
                'api_host': config["dest_api_host"]
            }

    initialize(**options)
    return options

def _ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def _json_to_file(path, fileName, data):
    filePathNameWExt = './' + path + '/' + fileName + '.json'
    _ensure_directory(path)
    with open(filePathNameWExt, 'w') as fp:
        json.dump(data, fp, sort_keys = True, indent = 4)
    return filePathNameWExt

def _files_to_json(type):
    files = glob.glob('{}/*.json'.format(type))
    return files



def pull_monitors(tag):
    path = False
    count = 0
    good_keys = ['tags', 'deleted', 'query', 'message', 'matching_downtimes', 'multi', 'name', 'type', 'options', 'id']
    tags = [] if not tag else tag
    monitors = api.Monitor.get_all()

    for monitor in monitors:
        if monitor["type"] == "synthetics alert":
                print("Skipping \"{}\" as this is a monitor belonging to a synthetic test. Synthetic monitors will be automatically re-created when you push synthetic tests.".format(monitor["name"].encode('utf8')))
                continue
        all_tags_found = True
        for tag in tags:
            if not tag in monitor["tags"]:
                all_tags_found = False
                print("Tag: {} not found in monitor: \"{}\" with tags {}".format(tag, monitor["name"].encode('utf8'), monitor["tags"]))
                break

        if all_tags_found == False:
            print("Skipping \"{}\" because its tags do not match the filter.".format(monitor["name"].encode('utf8')))

        if all_tags_found == True:
            count = count + 1

            new_monitor = {}
            for k, v in monitor.items():
                if k in good_keys:
                    new_monitor[k] = v
            if not arguments["--dry-run"]:
                path = _json_to_file('monitors', str(new_monitor["id"]), new_monitor)
            print("Pulling monitor: \"{}\" with id: {}, writing to file: {}".format(new_monitor["name"].encode('utf8'), new_monitor["id"], path))
    print("Retrieved '{}' monitors.".format(count))







def push_monitors():
    count = 0
    err_count = 0
    ids = {}
    monitors = _files_to_json("monitors")
    if not monitors:
        exit("No monitors are locally available. Consider pulling monitors first.")

    # first loop to import non composite monitors
    for monitor in monitors:
        with open(monitor) as f:
            data = json.load(f)
            if not data["type"] == "composite":
                old_id = str(data["id"])
                print("Pushing monitors:", data["id"], data["name"].encode('utf8'))
                if not arguments["--dry-run"]:
                    result = api.Monitor.create(type=data['type'],
                                        query=data['query'],
                                        name=data['name'],
                                        message=data['message'],
                                        tags=data['tags'],
                                        options=data['options'])
                    if 'errors' in result:
                        print('Error pushing monitor:',data["id"],json.dumps(result, indent=4, sort_keys=True))
                        err_count=err_count+1

                    else:
                        count = count + 1
                        new_id= result['id']
                        api.Monitor.mute(new_id)
                        print("New monitor ", str(new_id)," has been muted.")
                        ids[old_id] = str(new_id)
                else:
                    # Fake new id for dry-run purpose
                    ids[old_id] = old_id[:3] + "xxx"


    # Second loop to import composite monitors
    for monitor in monitors:
        with open(monitor) as f:
            data = json.load(f)
            if data["type"] == "composite":
                new_query = data["query"]
                for old_id, new_id in ids.items():
                    new_query=new_query.replace(old_id, new_id)
                print("Pushing composite monitors:", data["id"], data["name"].encode('utf8')," with query ", new_query.encode('utf8'))

                if not arguments["--dry-run"]:
                    result = api.Monitor.create(type=data['type'],
                                        query=new_query,
                                        name=data['name'],
                                        message=data['message'],
                                        tags=data['tags'],
                                        options=data['options'])
                    if 'errors' in result:
                        print('Error pushing monitor:',data["id"],json.dumps(result, indent=4, sort_keys=True))
                        err_count=err_count+1

                    else:
                        count = count + 1
                        new_id= result['id']
                        api.Monitor.mute(new_id)
                        print("New monitor ", str(new_id)," has been muted.")

    if count > 0:
        print("Pushed '{}' monitors in muted status, navigate to Monitors -> Manage downtime to unmute.".format(count))
    if err_count > 0:
        print("Error pushing '{}' monitors, please check !".format(err_count))




if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.1.1rc')

    if arguments["--dry-run"]:
        print("You are running in dry-mode. No changes will be commmited to your Datadog account(s).")

    if arguments["pull"]:
        _init_options("pull")
        if arguments['<type>'] == 'monitors':
            pull_monitors(arguments["--tag"])
    elif arguments["push"]:
        _init_options("push")
        if arguments['<type>'] == 'monitors':
            push_monitors()
