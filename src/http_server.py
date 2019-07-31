# Our main wifi-connect application, which is based around an HTTP server.

import os, getopt, sys, json, atexit, base64, ssl
import paho.mqtt.client as mqtt
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from io import BytesIO
from avahi.service import AvahiService

# Local modules
import netman

# Defaults
INTERFACE = 'eth0'
ADDRESS = ''
PORT = 443
UI_PATH = '../ui'
CERTFILE_PATH = "../lighttpd.pem"
MQTT_BROKER = "mosquitto"

key = ''
ipsettings = None

#------------------------------------------------------------------------------
# called at exit
def cleanup():
    print("Cleaning up prior to exit.")

#------------------------------------------------------------------------------
# A custom http server class in which we can set the default path it serves
# when it gets a GET request.
class MyHTTPServer(HTTPServer):
    def __init__(self, base_path, server_address, RequestHandlerClass):
        self.base_path = base_path
        HTTPServer.__init__(self, server_address, RequestHandlerClass)


#------------------------------------------------------------------------------
# A custom http request handler class factory.
# Handle the GET and POST requests from the UI form and JS.
# The class factory allows us to pass custom arguments to the handler.
def RequestHandlerClassFactory(address, interface, mqttclient):

    class MyHTTPReqHandler(SimpleHTTPRequestHandler):

        def __init__(self, *args, **kwargs):
            # We must set our custom class properties first, since __init__() of
            # our super class will call do_GET().
            self.address = address
            self.interface = interface
            self.mqttClient = mqttclient
            super(MyHTTPReqHandler, self).__init__(*args, **kwargs)


        def do_HEAD(self):
            print(f'do_HEAD {self.path}')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_AUTHHEAD(self):
            print(f'do_AUTHHEAD {self.path}')
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm=\"Sabre II BACnet Gateway\"')
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        # See if this is a specific request, otherwise let the server handle it.
        def do_GET(self):
            global key
            global ipsettings
            response = BytesIO()

            print(f'do_GET {self.path}')

            if self.headers['Authorization'] == None:
                self.do_AUTHHEAD()
                self.wfile.write(b'No Auth Header received')

            elif self.headers['Authorization'] == 'Basic '+str(key, 'utf-8'):
                if '/ipsettings' == self.path:
                        self.send_response(200)
                        self.end_headers()
                        response = BytesIO()
                        response.write(json.dumps(ipsettings).encode('utf-8'))
                        print(f'GET {self.path} returning: {response.getvalue()}')
                        self.wfile.write(response.getvalue())
                        return

                # All other requests are handled by the server which vends files
                # from the ui_path we were initialized with.
                super().do_GET()
            else:
                #print(f'{self.headers["Authorization"]} != Basic {str(key, "utf-8")}')
                self.do_AUTHHEAD()
                #self.send_header(self.headers['Authorization'])
                #self.wfile.write(self.headers['Authorization'])
                self.wfile.write(b'Not Authenticated')


        # test with: curl localhost:5000 -d "{'name':'value'}"
        def do_POST(self):
            global key
            global ipsettings

            if self.headers['Authorization'] == None or self.headers['Authorization'] != 'Basic '+str(key, 'utf-8'):
                print('POST Not Authenticated')
                self.send_response(401)
                return

            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            fields = parse_qs(body.decode('utf-8'))
            print(f'POST received: {fields}')

            # Parse the form post
            FORM_MODE = 'mode'
            FORM_IP_ADDRESS = 'ip-address'
            FORM_NETMASK = 'netmask'
            FORM_GATEWAY = 'gateway'

            if FORM_MODE not in fields:
                print(f'Error: POST is missing {FORM_MODE} field.')
                return

            mode = fields[FORM_MODE][0]
            ipaddress = None
            netmask = None
            gateway = ''
            if FORM_IP_ADDRESS in fields: 
                ipaddress = fields[FORM_IP_ADDRESS][0]
            if FORM_NETMASK in fields: 
                netmask = fields[FORM_NETMASK][0] 
            if FORM_GATEWAY in fields: 
                gateway = fields[FORM_GATEWAY][0] 

            # Connect to the user's selected AP
            success = netman.update_ethernet_settings(mode=mode, ipaddress=ipaddress, \
                    netmask=netmask, gateway=gateway, dev_name=interface)

            if success:
                response.write(b'OK\n')
                ipsettings = netman.get_ethernet_settings(interface)
                self.mqttClient.publish("ip-changed")
            else:
                response.write(b'ERROR\n')
            self.wfile.write(response.getvalue())

            # Handle success or failure of the new connection
            if success:
                print(f'Settings updated!')
            else:
                print(f'Update failed.')


    return  MyHTTPReqHandler # the class our factory just created.

#------------------------------------------------------------------------------
# Create the hotspot, start dnsmasq, start the HTTP server.
def main(interface, address, port, ui_path, mqtt_broker):

    global key
    global ipsettings

    # Find the ui directory which is up one from where this file is located.
    web_dir = os.path.join(os.path.dirname(__file__), ui_path)
    print(f'HTTP serving directory: {web_dir} on {address}:{port}')

    # Change to this directory so the HTTPServer returns the index.html in it 
    # by default when it gets a GET.
    os.chdir(web_dir)

    # Host:Port our HTTP server listens on
    server_address = (address, port)

    keystr = os.getenv('BALENA_DEVICE_UUID')
    if keystr == None:
        print("Error: Can't get Device UUID!")
        return
    keystr = keystr[:7] + ':remsdaq'
    key = base64.b64encode(bytearray(keystr.encode('ascii')))

    mqttclient = mqtt.Client("P1")
    mqttclient.loop_start()
    try:
        mqttclient.connect(mqtt_broker)
    except:
        print("mqtt error")

    ipsettings = netman.get_ethernet_settings(interface)

    # Custom request handler class (so we can pass in our own args)
    MyRequestHandlerClass = RequestHandlerClassFactory(address, interface, mqttclient)
    avahi = AvahiService(f"Sabre II BACnet Gateway {keystr[:7]}", "_workstation._tcp", 9)
    avahi = AvahiService(f"Sabre II BACnet Gateway {keystr[:7]}", "_https._tcp", port)

    # Start an HTTP server to serve the content in the ui dir and handle the 
    # POST request in the handler class.
    httpd = MyHTTPServer(web_dir, server_address, MyRequestHandlerClass)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=CERTFILE_PATH, server_side=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


#------------------------------------------------------------------------------
# Util to convert a string to an int, or provide a default.
def string_to_int(s, default):
    try:
        return int(s)
    except ValueError:
        return default


#------------------------------------------------------------------------------
# Entry point and command line argument processing.
if __name__ == "__main__":
    atexit.register(cleanup)

    interface = INTERFACE
    address = ADDRESS
    port = PORT
    ui_path = UI_PATH
    mqtt_broker = MQTT_BROKER
    simulate = False
    delete_connections = False

    usage = ''\
f'Command line args: \n'\
f'  -i <Interface name>          Default: {interface} \n'\
f'  -a <HTTP server address>     Default: {address} \n'\
f'  -p <HTTP server port>        Default: {port} \n'\
f'  -u <UI directory to serve>   Default: "{ui_path}" \n'\
f'  -q <MQTT broker>             Default: "{mqtt_broker}" \n'\
f'  -h Show help.\n'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:a:p:u:dsh")
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(usage)
            sys.exit()

        elif opt in ("-i"):
            interface = arg

        elif opt in ("-a"):
            address = arg

        elif opt in ("-p"):
            port = string_to_int(arg, port)

        elif opt in ("-u"):
            ui_path = arg

        elif opt in ("-q"):
            mqtt_broker = arg

    print(f'Inferface={interface}')
    print(f'Address={address}')
    print(f'Port={port}')
    print(f'UI path={ui_path}')
    print(f'MQTT broker={mqtt_broker}')
    main(interface, address, port, ui_path, mqtt_broker)


