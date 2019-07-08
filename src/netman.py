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
        print(f'GetSettings: {dev.ActiveConnection.Connection.GetSettings()["ipv4"]}')
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
    
    settings['ipv4']['addresses'] = []  # deprecated
    settings['ipv4']['address-data'] = []
    settings['ipv4']['gateway'] = ''

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

