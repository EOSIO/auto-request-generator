from request_generator import request_generator
from request_generator import request_builder
import requests
from hyper.contrib import HTTP20Adapter

# This file serves as an example of how to use the request generator classes.

# A function that performs a single request, called by the generator.
def api_call(args):

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

if __name__ == '__main__':

    # An example of how to drive the function above
    rps = 1000
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
