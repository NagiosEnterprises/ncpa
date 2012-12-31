import requests

def send_nrdp(url, *args, **kwargs):
    r = requests.post(url, params=kwargs, verify=False)
    return r
