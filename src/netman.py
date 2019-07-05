# You must use https://developer.gnome.org/NetworkManager/1.2/spec.html
# to see the DBUS API that the python-NetworkManager module is communicating
# over (the module documentation is scant).

import NetworkManager
import uuid, os, sys, time, socket

DEFAULT_DEV_NAME = 'eth0'

#------------------------------------------------------------------------------
# Return ipv4 settings or error
def get_ethernet_settings(dev_name=DEFAULT_DEV_NAME):
    devices = NetworkManager.NetworkManager.GetDevices();
    for dev in devices:
        if dev.Interface != dev_name:
            continue
        if dev.ActiveConnection == None:
            continue
        return dev.ActiveConnection.Connection.GetSettings()['ipv4']
    return None

def update_ethernet_settings(mode, ipaddress, netmask, gateway, dev_name=DEFAULT_DEV_NAME):
    devices = NetworkManager.NetworkManager.GetDevices();
    for dev in devices:
        if dev.Interface != dev_name:
            continue
        if dev.ActiveConnection == None:
            continue

        break

    conn = dev.ActiveConnection.Connection
    settings = conn.GetSettings()
    
    if mode == 'manual':
        settings['ipv4']['address-data'] = [{'address': ipaddress, 'prefix': netmask}]
        settings['ipv4']['gateway'] = gateway

    settings['ipv4']['method'] = mode
    print(f'{settings}')

    try:
        conn.Update(settings)
        dev.Reapply({}, 0, 0) #cver[1], 0)

        # Wait for ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready
        print(f'Waiting for connection to become active...')
        loop_count = 0
        while dev.State != NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            #print(f'dev.State={dev.State}')
            time.sleep(1)
            loop_count += 1
            if loop_count > 30: # only wait 30 seconds max
                break

        if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            print(f'Connection active.')
            return True

    except Exception as e:
        print(f'Connection error {e}')

    print(f'Connection failed.')
    return False



#------------------------------------------------------------------------------
# Returns True if we are connected to the internet, False otherwise.
def have_active_internet_connection(host="8.8.8.8", port=53, timeout=2):
   """
   Host: 8.8.8.8 (google-public-dns-a.google.com)
   OpenPort: 53/tcp
   Service: domain (DNS/TCP)
   """
   try:
     socket.setdefaulttimeout(timeout)
     socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
     return True
   except Exception as e:
     #print(f"Exception: {e}")
     return False


# #------------------------------------------------------------------------------
# # Generic connection stopper / deleter.
# def stop_connection(conn_name=GENERIC_CONNECTION_NAME):
#     # Find the hotspot connection
#     try:
#         connections = NetworkManager.Settings.ListConnections()
#         connections = dict([(x.GetSettings()['connection']['id'], x) for x in connections])
#         conn = connections[conn_name]
#         conn.Delete()
#     except Exception as e:
#         #print(f'stop_hotspot error {e}')
#         return False
#     time.sleep(2)
#     return True

# #------------------------------------------------------------------------------
# # Generic connect to the user selected AP function.
# # Returns True for success, or False.
# def connect_to_AP(conn_type=None, conn_name=GENERIC_CONNECTION_NAME, \
#         ssid=None, username=None, password=None):

#     #print(f"connect_to_AP conn_type={conn_type} conn_name={conn_name} ssid={ssid} username={username} password={password}")

#     if conn_type is None or ssid is None:
#         print(f'connect_to_AP() Error: Missing args conn_type or ssid')
#         return False

#     try:
#         # This is the hotspot that we turn on, on the RPI so we can show our
#         # captured portal to let the user select an AP and provide credentials.
#         hotspot_dict = {
#             '802-11-wireless': {'band': 'bg',
#                                 'mode': 'ap',
#                                 'ssid': ssid},
#             'connection': {'autoconnect': False,
#                            'id': conn_name,
#                            'interface-name': 'wlan0',
#                            'type': '802-11-wireless',
#                            'uuid': str(uuid.uuid4())},
#             'ipv4': {'address-data': 
#                         [{'address': '192.168.42.1', 'prefix': 24}],
#                      'addresses': [['192.168.42.1', 24, '0.0.0.0']],
#                      'method': 'manual'},
#             'ipv6': {'method': 'auto'}
#         }

# #debugrob: is this realy a generic ENTERPRISE config, need another?
# #debugrob: how do we handle connecting to a captured portal?

#         # This is what we use for "MIT SECURE" network.
#         enterprise_dict = {
#             '802-11-wireless': {'mode': 'infrastructure',
#                                 'security': '802-11-wireless-security',
#                                 'ssid': ssid},
#             '802-11-wireless-security': 
#                 {'auth-alg': 'open', 'key-mgmt': 'wpa-eap'},
#             '802-1x': {'eap': ['peap'],
#                        'identity': username,
#                        'password': password,
#                        'phase2-auth': 'mschapv2'},
#             'connection': {'id': conn_name,
#                            'type': '802-11-wireless',
#                            'uuid': str(uuid.uuid4())},
#             'ipv4': {'method': 'auto'},
#             'ipv6': {'method': 'auto'}
#         }

#         # No auth, 'open' connection.
#         none_dict = {
#             '802-11-wireless': {'mode': 'infrastructure',
#                                 'ssid': ssid},
#             'connection': {'id': conn_name,
#                            'type': '802-11-wireless',
#                            'uuid': str(uuid.uuid4())},
#             'ipv4': {'method': 'auto'},
#             'ipv6': {'method': 'auto'}
#         }

#         # Hidden, WEP, WPA, WPA2, password required.
#         passwd_dict = {
#             '802-11-wireless': {'mode': 'infrastructure',
#                                 'security': '802-11-wireless-security',
#                                 'ssid': ssid},
#             '802-11-wireless-security': 
#                 {'key-mgmt': 'wpa-psk', 'psk': password},
#             'connection': {'id': conn_name,
#                         'type': '802-11-wireless',
#                         'uuid': str(uuid.uuid4())},
#             'ipv4': {'method': 'auto'},
#             'ipv6': {'method': 'auto'}
#         }

#         conn_dict = None
#         conn_str = ''
#         if conn_type == CONN_TYPE_HOTSPOT:
#             conn_dict = hotspot_dict
#             conn_str = 'HOTSPOT'

#         if conn_type == CONN_TYPE_SEC_NONE:
#             conn_dict = none_dict 
#             conn_str = 'OPEN'

#         if conn_type == CONN_TYPE_SEC_PASSWORD:
#             conn_dict = passwd_dict 
#             conn_str = 'WEP/WPA/WPA2'

#         if conn_type == CONN_TYPE_SEC_ENTERPRISE:
#             conn_dict = enterprise_dict 
#             conn_str = 'ENTERPRISE'

#         if conn_dict is None:
#             print(f'connect_to_AP() Error: Invalid conn_type="{conn_type}"')
#             return False

#         #print(f"new connection {conn_dict} type={conn_str}")

#         NetworkManager.Settings.AddConnection(conn_dict)
#         print(f"Added connection {conn_name} of type {conn_str}")

#         # Now find this connection and its device
#         connections = NetworkManager.Settings.ListConnections()
#         connections = dict([(x.GetSettings()['connection']['id'], x) for x in connections])
#         conn = connections[conn_name]

#         # Find a suitable device
#         ctype = conn.GetSettings()['connection']['type']
#         dtype = {'802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI}.get(ctype,ctype)
#         devices = NetworkManager.NetworkManager.GetDevices()

#         for dev in devices:
#             if dev.DeviceType == dtype:
#                 break
#         else:
#             print(f"connect_to_AP() Error: No suitable and available {ctype} device found.")
#             return False

#         # And connect
#         NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
#         print(f"Activated connection={conn_name}.")

#         # Wait for ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready
#         print(f'Waiting for connection to become active...')
#         loop_count = 0
#         while dev.State != NetworkManager.NM_DEVICE_STATE_ACTIVATED:
#             #print(f'dev.State={dev.State}')
#             time.sleep(1)
#             loop_count += 1
#             if loop_count > 30: # only wait 30 seconds max
#                 break

#         if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
#             print(f'Connection {conn_name} is live.')
#             return True

#     except Exception as e:
#         print(f'Connection error {e}')

#     print(f'Connection {conn_name} failed.')
#     return False




