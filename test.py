from request_generator import request_generator
from request_generator import request_builder
import requests
from hyper.contrib import HTTP20Adapter

def api_call(driver_id, thread_id, args):

    req = args['req']

    sess = requests.session()
    if req.http2:
        from hyper.contrib import HTTP20Adapter
        sess.mount('https://', HTTP20Adapter())

    resp = sess.request(
        req.method,
        req.url,
        params=req.params,
        data=req.data,
        headers=req.headers,
        files=req.files,
        auth=req.auth,
        cookies=req.cookies,
        verify=req.verify
    )
    resp.raise_for_status()

    return request_generator.Result(req.url, resp.status_code, len(resp.content))

rps = 1
duration = 10
req = request_builder.RequestBuilder(
        'https://jsonplaceholder.typicode.com/todos/1',
        params={},
        data=None,
        cookiejarfile=None,
        auth=None,
        method='GET',
        user_agent='reqgen',
        auth_type='basic',
        headers={},
        files=[],
        insecure=False,
        nokeepalive=False,
        http2=False
    )
args = {'req': req}

reqgen = request_generator.RequestGenerator(rps, duration, api_call, args)
num_requests = reqgen.run()
print(f'num_requests: {num_requests}')
