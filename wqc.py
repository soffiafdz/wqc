#! /usr/bin/env python3

import cherrypy
from cherrypy import process

import argparse
import os
import traceback
import tempfile
import shutil
import csv
import datetime
import sys
import atexit
import socket

minc_supported=False
try:
    from ipl.minc_tools import mincTools,mincError
    from ipl.minc_qc    import qc,qc_field_contour
    minc_supported=True
except:
    pass

from io import StringIO


class SaveInfo(process.plugins.SimplePlugin):
    def __init__(self, bus, objs):
        self.servings = []
        process.plugins.SimplePlugin.__init__(self, bus)
        self.objs=objs

    def start(self):
        pass
    start.priority = 80

    def stop(self):
        for i in self.objs:
            i.save_data()
            i.cleanup()


class dumb_object(object):
    def __init__(self):
        pass

    @cherrypy.expose
    def index(self):
        return "<!DOCTYPE html><html><body>Something will be here</body></html>"


@cherrypy.popargs('name')
class Img(object):
    def __init__(self,qc_files):
        self.qc_files=qc_files
        self.tempdir = tempfile.mkdtemp(prefix='QC',dir=os.environ.get('TMPDIR',None))
        pass

    def save_data(self):
        pass

    @cherrypy.expose
    def index(self,name=None):
        if name is None:
            return "<!DOCTYPE html><html><body>Images will be here</body></html>"
        else:
            try:
                #(img_name,img_ext)=name.rsplit('.',1)
                finfo=self.qc_files[int(name)]

                if finfo[3]=='png':
                    cherrypy.response.headers['Content-Type']= 'image/png'
                    return open(finfo[0],'r')
                elif finfo[3]=='jpg':
                    cherrypy.response.headers['Content-Type']= 'image/jpeg'
                    return open(finfo[0],'r')
                elif (finfo[3]=='mnc' or finfo[3]=='minc') and minc_supported:
                    # dynamically render minc here
                    img_file=self.tempdir+name+'.png'
                    if not os.path.exists(img_file):
                        qc(finfo[0],img_file,format='png')
                    cherrypy.response.headers['Content-Type']= 'image/png'#svg+xml
                    return open(img_file,'r')
                else:
                    cherrypy.response.status = 503
                    return "Unsupprted image file format:{}".format(finfo[0])

            except:
                print("Exception in index:{}".format(sys.exc_info()[0]))
                traceback.print_exc(file=sys.stdout)
                return "<!DOCTYPE html><html><body>Image {} not found!</body></html>".format(name)

    def cleanup(self):
        if os.path.exists(self.tempdir):
            #print("Cleaning up tempdir:{}".format(self.tempdir))
            shutil.rmtree(self.tempdir)

@cherrypy.popargs('name')
class QC(object):
    def __init__(self,qc_files,csv):
        # TODO: init here?
        self.qc_files=qc_files
        self.csv=csv

    def save_data(self):
        if self.csv is not None:
            temp_csv=self.csv

            if os.path.exists(self.csv):
                # let's save to a separate csv file, and then update
                temp_csv=self.csv+'.save'

            with open(temp_csv, 'wb') as csvfile:
                qcwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

                for f in self.qc_files:
                    qcwriter.writerow([f[0],f[4],f[5]])

            # move filem, if it was properly saved
            if temp_csv!=self.csv:
                shutil.move(temp_csv,self.csv)

    @cherrypy.expose
    def index(self, name=None,q=None,item=None):
        if name is None:
            #print("User wants to know about {}".format(name))
            _name='0'
        else:
            _name=name
        img_id=int(_name)

        if q is not None and (name is not None or item is not None):
            # user assigned a label
            item_id=img_id
            if item is not None:
                item_id=int(item)

            self.qc_files[item_id][4]=q
            print("{} - {}".format(self.qc_files[img_id][0],q))

        prev_id=""
        prev_str=""
        next_id=""
        next_str=""
        img='/img/'+str(img_id)
        next_img=None


        if img_id>0:
            prev_id=img_id-1
            prev_str="<A href=\"/{}\" rel=\"prev\">Prev</A>".format(prev_id)
        else:
            prev_id=img_id

        if img_id<(len(self.qc_files)-1):
            next_id=img_id+1
            next_str="<A href=\"/{}\" rel=\"next\">Next</A>".format(next_id)
            next_img='/img/'+str(next_id)
        else:
            next_id=img_id

        prefetch=""
        # try to prefetch next page
        if next_img is not None:
            prefetch+="<link rel=\"prefetch\" href=\"{img}\"><link rel=\"prefetch\" href=\"/{next_id}\">".format(img=next_img,next_id=next_id)

        return """<!DOCTYPE html>
<script type="text/javascript" src="/js/mousetrap.min.js"></script>
<html>
    <head>
<meta http-equiv="cache-control" content="max-age=0" />
<meta http-equiv="cache-control" content="no-cache" />
<meta http-equiv="expires" content="0" />
<meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
<meta http-equiv="pragma" content="no-cache" />
<script type="text/javascript">
(function () {{
            Mousetrap.bind('1', function() {{ window.location.href=\"{url_pass}\"; }});
            Mousetrap.bind('2', function() {{ window.location.href=\"{url_fail}\"; }});
            Mousetrap.bind(['left','backspace'], function() {{ window.location.href=\"{url_prev}\"; }});
            Mousetrap.bind(['right','space'], function()    {{ window.location.href=\"{url_next}\"; }});
            }}) ();
</script>
    </head>
    <body>
    <table>
    <tr>
    <td></td><td align="Center">{title}</td><td></td>
    </tr>
    <tr>
    <td>{prev_str}</td>
    <td><img src=\"{img}\"></td>
    <td>{next_str}{prefetch}</td>
    </tr>
    <tr><td><A href=\"{url_pass}\">(1)Pass</A></td><td align="Center">{label}</td><td><A href=\"{url_fail}\">(2)Fail</A></td></tr>
    </table>
<h3>Shortcuts:</h3>
    <p>
    <ul>
    <li> <b>&lt;-</b> or <b>bksp</b> previous </li>
    <li> <b>-&gt;</b> or <b>space</b> next </li>
    <li> <b>1</b> - pass+next</li>
    <li> <b>2</b> - fail+next</li>
    </ul>
    </p>
    </body>
</html>
        """.format(img=img,
                prev_str=prev_str,
                next_str=next_str,
                title=self.qc_files[img_id][2],
                label=self.qc_files[img_id][4],
                url_pass="/"+str(next_id)+'?q=pass&item='+_name,
                url_fail="/"+str(next_id)+'?q=fail&item='+_name,
                url_prev='/'+str(prev_id),
                url_next='/'+str(next_id),
                prefetch=prefetch
            )

    def cleanup(self):
        pass



def parse_options():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                description='Web QC tool')

    parser.add_argument('--debug',
                    action="store_true",
                    dest="debug",
                    default=False,
                    help='Print debugging information' )

    parser.add_argument('--accept',
                    action="store_true",
                    dest="accept",
                    default=False,
                    help='Accept remote connections' )

    parser.add_argument('--port',
                    dest="port",
                    default=8080,
                    type=int,
                    help='port to listen to' )

    parser.add_argument('--csv',
                    dest="csv",
                    help='CSV file' )

    parser.add_argument('files',
                    help='Image files', nargs='*')

    options = parser.parse_args()

    return options


if __name__ == '__main__':
    script_dir=os.path.dirname(os.path.abspath(sys.argv[0]))
    options=parse_options()

    qc_files=[]

    if options.csv is None:
        options.csv=os.getcwd()+os.sep+'qc_auto.csv'
        print("Warning: you didn't specify the output csv file, I will try to save output to {}".format(options.csv))

    if options.csv is not None:
        try:
          with open(options.csv, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                l=len(row)
                if l<1 or l>3:
                    print("Unexpected row:{}".format(repr(row)))
                else:
                    qc_file=row[0]
                    status=''
                    note=''
                    if l>1:
                        status=row[1]
                    if l>2:
                        note=row[2]
                    qc_files.append([qc_file,None,None,None,status,note])
        except IOError:
           pass # failed to read form csv file

    if len(options.files)>0:
        # merge list of files with csv
        for i in options.files:
            # check if the file is in there already
            try:
                next(x[0] for x in qc_files if x[0]==i)
            except StopIteration:
                # add new item
                qc_files.append([i,None,None,None,'',''])

    if len(qc_files)==0 :
        print("Refusing to start without input files!")
        print("Launch with --help")
        exit(1)
    else:
        main_conf={
            '/': {
                'tools.expires.on': True,
                'tools.expires.secs':  30,
                'tools.caching.on': False
                    }
            }
        css_conf={
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': script_dir+'/css'
                }
            }
        js_conf={
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': script_dir+'/js'
                }
            }

        img_conf={'/': {
                'tools.expires.on': True,
                'tools.expires.secs':  30
                        }
                    }

        if options.accept:
            cherrypy.config.update( {'server.socket_host': '0.0.0.0'} )

        cherrypy.config.update( {'server.socket_port': options.port } )

        if not options.debug:
            cherrypy.config.update( {'log.screen': False,
                                     'log.access_file': None,
                                     'log.error_file': None} )

        host_ip=cherrypy.config.get('server.socket_host','127.0.0.1')
        port=cherrypy.config.get('server.socket_port','8080')

        if host_ip=='0.0.0.0':
            host_ip=[ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
            print("Starting server on all public addresses:")
            for i in host_ip:
                print("\t{}:{}".format(i,port))
        else:
            print("Starting server on {}:{}".format(host_ip,port))

        for j,i in enumerate( qc_files ):
            b=os.path.basename(i[0])
            (name,ext)=b.rsplit('.',1)
            qc_files[j][1]=b
            qc_files[j][2]=name
            qc_files[j][3]=ext

            if (ext=='mnc' or ext=='minc') and not minc_supported:
                print("Warning: MINC files are not supported now, install ipl.minc_tools and ipl.minc_qc")

        qc_app=QC(qc_files,options.csv)
        img_app=Img(qc_files)

        #atexit.register(file_cleanup,[qc_app,img_app])
        #cherrypy.engine.scratchdb = ScratchDB(cherrypy.engine)
        save_info=SaveInfo(cherrypy.engine,[qc_app,img_app])
        save_info.subscribe()

        cherrypy.tree.mount(qc_app,'/',main_conf)
        cherrypy.tree.mount(img_app,'/img',img_conf)
        cherrypy.tree.mount(dumb_object(),'/css',config=css_conf)
        cherrypy.tree.mount(dumb_object(),'/js',config=js_conf)

        #cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()
        print("Press Ctrl-C to exit and save csv file")
        #userInput = raw_input('Hit enter to quit')
        cherrypy.engine.block()

# kate: space-indent on; indent-width 4; indent-mode python;replace-tabs on;word-wrap-column 80
