from http.cookiejar import MozillaCookieJar
import mimetypes
import requests
import requests.auth
from hyper.contrib import HTTP20Adapter
import socket
from urllib.parse import urlparse

class RequestBuilder():
    def __init__(self,
        url,
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
        http2=False):

        if url[:4] != "http":
            url = "http://" + url

        url_parts = urlparse(url)
        params = url_parts.params
        hostname = url_parts.netloc.split(':')[0]
        host_ip = socket.gethostbyname(hostname)
        url_with_ip = url.replace(hostname, host_ip)

        if not isinstance(headers, dict):
            raise Exception('Headers must be in dict form')
        if not 'user-agent' in headers:
            headers['user-agent'] = user_agent
        if nokeepalive:
            headers['connection'] = 'close'

        authobj = None
        if auth:
            if auth_type not in ('basic','digest'):
                raise Exception('Auth type must be one of: basic, digest')

            auth = auth.split(':',1)
            if len(auth) == 1:
                raise Exception('Credentials must be in username:password format')

            if auth_type == "digest":
                authobj = requests.auth.HTTPDigestAuth(auth)
            else:
                authobj = requests.auth.HTTPBasicAuth(auth)

        try:
            cj = MozillaCookieJar()
            if cookiejarfile is not None:
                cj.load(cookiejarfile)
                cookiejar = cj
            else:
                cookiejar = None
        except Exception as e:
            raise Exception(f'Unable to load cookie jar: {e}')

        if not isinstance(insecure, bool):
            raise Exception('Insecure flag must be a boolean')

        upload = []
        for file_data in files:
            i = file_data.split(':')
            file_var = i[0]
            file_path = i[1]
            upload.append((file_var, file_path))

        if upload:
            method = "POST"

        self.method = method.upper()
        self.ipurl = url_with_ip
        self.url = url
        self.params = params
        self.data = data
        self.headers = headers
        self.files = upload
        self.auth = authobj
        self.cookies = cookiejar
        self.verify = not insecure
        self.http2 = http2 # sess.mount('https://', HTTP20Adapter())

if __name__ == "__main__":
    req = RequestBuilder(
        'google.com',
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

    sess = requests.session()
    if req.http2:
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
    print(f'status code: {resp.status_code} size: {len(resp.content)}')
