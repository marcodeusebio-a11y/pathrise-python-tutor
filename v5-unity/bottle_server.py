import urllib.request
import urllib.error
# Lightweight OPT server that works on both Python 2 and 3

# NOTE that this is meant only for testing and not deployment, since
# there is no sandboxing

# to invoke, run 'python bottle_server.py'
# and visit http://localhost:8080/index.html
#
# external dependencies: bottle
#
# easy_install pip
# pip install bottle

from bottle import route, get, request, run, template, static_file, response
try:
    import StringIO # NB: don't use cStringIO since it doesn't support unicode!!!
except:
    import io as StringIO # py3
import json
import pg_logger
import os


@route('/web_exec_<name:re:.+>.py')
@route('/LIVE_exec_<name:re:.+>.py')
@route('/viz_interaction.py')
@route('/syntax_err_survey.py')
@route('/runtime_err_survey.py')
@route('/eureka_survey.py')
@route('/error_log.py')
def dummy_ok(name=None):
    return 'OK'

@route('/<filepath:path>')
def index(filepath):
    return static_file(filepath, root='.')


# Note that this will run either Python 2 or 3, depending on which
# version of Python you used to start the server, REGARDLESS of which
# route was taken:
@route('/web_exec_py2.py')
@route('/web_exec_py3.py')
@route('/LIVE_exec_py2.py')
@route('/LIVE_exec_py3.py')
def get_py_exec():
  out_s = StringIO.StringIO()

  def json_finalizer(input_code, output_trace):
    ret = dict(code=input_code, trace=output_trace)
    json_output = json.dumps(ret, indent=None)
    out_s.write(json_output)

  options = json.loads(request.query.options_json)

  pg_logger.exec_script_str_local(request.query.user_script,
                                  request.query.raw_input_json,
                                  options['cumulative_mode'],
                                  options['heap_primitives'],
                                  json_finalizer)

  return out_s.getvalue()




def _choose_cokapi_path(base):
    if 'callback' in request.query:
        return base + '_jsonp'
    return base

def _proxy_cokapi(path):
    target = 'http://127.0.0.1:3000/' + path
    if request.query_string:
        target += '?' + request.query_string
    try:
        with urllib.request.urlopen(target, timeout=120) as r:
            upstream_type = r.headers.get('Content-Type', 'text/plain; charset=utf-8')
            response.set_header('Content-Type', upstream_type)
            return r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        response.status = e.code
        response.set_header('Content-Type', e.headers.get('Content-Type', 'text/plain; charset=utf-8'))
        return e.read().decode('utf-8', errors='replace')
    except Exception as e:
        response.status = 502
        response.set_header('Content-Type', 'application/json; charset=utf-8')
        return json.dumps({
            'code': '',
            'trace': [{
                'event': 'uncaught_exception',
                'exception_msg': 'Local C/C++ backend unavailable: ' + str(e)
            }]
        })

@route('/web_exec_c.py')
def web_exec_c():
    return _proxy_cokapi(_choose_cokapi_path('exec_c'))

@route('/web_exec_cpp.py')
def web_exec_cpp():
    return _proxy_cokapi(_choose_cokapi_path('exec_cpp'))


if __name__ == "__main__":
    if os.environ.get('APP_LOCATION')=='heroku':
        run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)), reloader=True)
    else:
        run(host='localhost', port=5000, reloader=False)
