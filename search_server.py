
from http.server import HTTPServer, BaseHTTPRequestHandler

import json, time

from PIL import Image
import base64, io

from logger import log

import numpy as np

global_params = {}

# Given input type and output type, yields searcher
searchers = None
# Give
encoders = None

hostname = '127.0.0.1'
port = 8000

def set_param(key, value):
    global_params[key] = value

def run_server():
    log('Running with params:')
    for k in global_params:
        print(k, ':', global_params[k])
    
    global searchers, encoders
    searchers = global_params['searchers']
    encoders = global_params['encoders']
    
    # Every searcher should have an encoder available
    assert all(k in encoders for k in searchers)

    httpd = HTTPServer((hostname, port), SearchServer)
    log('SearchServer running on port', port)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log('SearchServer shutting down due to keyboard interrupt')
    except Exception as err:
        log(f'SearchServer shutting down due to unexpected exception:\r\n{err}')
    
    httpd.server_close()
    log('SearchServer has shut down successfully')

def b2img(bs):
    stream = io.BytesIO(bs)
    return Image.open(stream)

class SearchServer(BaseHTTPRequestHandler):
    def write_http_header(self, status, content_type='text/html'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        f = self.rfile.read(content_length)
        
        try:
            # Pull out the parameters
            params = json.loads(f)
            log('Successfully extracted JSON')
            
            # Determine the input type as validation
            input_type = None
            output_type = 'image'
            for i, o in searchers:
                if i in params:
                    input_type = i
                    output_type = o
                    searcher = searchers[i,o]
                    encoder = encoders[i,o]
                    break

            if input_type is None:
                raise Exception("Input type not known")
            if output_type is None:
                raise Exception("Output type not known")
            else:
                log('Will search for', output_type,
                    'using', input_type)

            ct = params['count']
            data = params[input_type]

            # Configure input data based on expected type
            if input_type == 'image':
                # Searching based on image
                data = base64.b64decode(data)
                log('Successfully extracted JSON contents')

                # Extract the image
                img = b2img(data).convert('RGB').resize((32, 32), Image.ANTIALIAS)
                data = np.array(img)

        except Exception as err:
            log(f'Exception thrown during data extraction:\n{err}')
            self.write_http_header(400)
            self.wfile.write(b'400 Bad Request')
            log('Sent', 400, 'result')
            return
        
        try:
            data = encoder.encode(data)
            log('User query was successfully encoded')

            urls = searcher.search(data, ct)
            n_urls = len(urls)
            log('Search was successful')
            
            result = {
                'count' : n_urls,
                'files' : [{'url' : u, 'type' : 'image'} for u in urls]
            }

            # Respond
            response = json.dumps(result)

            self.write_http_header(200, content_type='application/json')
            self.wfile.write(response.encode())
            log('Sent', 200, 'result')
        except Exception as err:
            log('Exception thrown during response phase:', err)
            self.write_http_header(500)
            self.wfile.write(b'500 Internal Server Error')
            log('Sent', 500, 'result')

