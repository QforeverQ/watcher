import requests
import json
import time
import re
import sys


def raise_alert(config=None, title=None, alert_type=None, context=None):
    """
    向apiserver发送一个报警请求
    """
    body = {
                'mentioned_list': ','.join(config.mentioned_list),
                'group': config.group,
                'title': title,
                'alert_type': alert_type,
                'context': json.dumps(context)
            }
    result = requests.post(config.api_url, data=body)
    time.sleep(config.alert_interval)
    return result.text

def get_time():
    """
    获取当前系统时间
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

class Regex():
    def __init__(self, config_dict=None):
        self.error = re.compile(config_dict['regex']['error'])
        self.warning = re.compile(config_dict['regex']['warning'])
        self.title = re.compile(config_dict['regex']['title'])
        self.failed = re.compile(config_dict['regex']['failed'])

class Config():
    def __init__(self, config_path=None):
        with open(config_path, 'r') as config_file:
            config_dict = json.load(config_file)
            self.api_url = config_dict['api_url']
            self.mentioned_list = config_dict['mentioned_list']
            self.group = config_dict['group']
            self.log_file = config_dict['log_file']
            self.check_interval = config_dict['check_interval']
            self.alert_interval = config_dict['alert_interval']
            self.regex = Regex(config_dict)
            
def watch_log_update(config=None, cursor=None):

    with open(config.log_file, encoding='utf-8') as log:
        log.seek(cursor)
        lines = log.readlines()
        if lines is not None:
            for line in lines:
                error = re.search(config.regex.error, line)
                if error:
                    alert_type = 'Error'
                    context = {
                                    'timestamp': get_time(),
                                    'message': line
                    }
                    raise_alert(config, title, alert_type, context)
                warning = re.search(config.regex.warning, line)
                if warning:
                    alert_type = 'Warning'
                    context = {
                                    'timestamp': get_time(),
                                    'message': line
                    }
                    raise_alert(config, title, alert_type, context)
                failed = re.search(config.regex.failed, line)
                if failed:
                    alert_type = 'Failed'
                    context = {
                                    'timestamp': get_time(),
                                    'message': line
                    }
                    raise_alert(config, title, alert_type, context)
                
        return log.tell()
                    

if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print('Usage: ' + sys.argv[0] + ' config.json')
        exit(0)

    config = Config(sys.argv[1])
    
    title = "Unknown title"
    flag = True
    while flag:
        
        with open(config.log_file, encoding='utf-8') as log:
            line = log.readline()

            while line:
                result = re.search(config.regex.title, line)
                print(result)
                if result is not None:
                    title = result.group(0)
                    flag = False
                    break
                line = log.readline()

            log_cursor = log.tell()
            
        time.sleep(0.5)
        

    while True:
        log_cursor = watch_log_update(config, log_cursor)
        time.sleep(config.check_interval)
