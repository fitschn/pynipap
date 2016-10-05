#!/usr/bin/python
""" The script fetches prefixes based on a provided query string and creates
    two /32 host entries for any found prefix.

    It will read .nipaprc per default or rely on command line arguments for
    connection settings to the backend.

    You can create /30 networks with this command:
    nipap address add from-prefix 10.24.16.0/24 prefix_length 30 vrf 100:65500 type assignment tags 'dhcp'
"""

from __future__ import print_function

import ConfigParser
import os
import sys
from pynipap import Prefix, Pool, VRF
import pynipap

class ConfigExport:
    def __init__(self):
        self.prefixes = []


    def get_prefixes(self, query):
        """ Get prefix data from NIPAP
        """
        try:
            res = Prefix.smart_search(query, {})
        except socket.error:
            print >> sys.stderr, "Connection refused, please check hostname & port"
            sys.exit(1)
        except xmlrpclib.ProtocolError:
            print >> sys.stderr, "Authentication failed, please check your username / password"
            sys.exit(1)

        for p in res['result']:
            self.prefixes.append(p)

    def generate_hosts(self, device):
        """ Generate host addresses
        """
        i = 1
        for p in self.prefixes:
            address = p.prefix.split('/')[0]
            octets = address.split('.')
            pre_node1 = '.'.join(octets[:3] + [str( int(octets[3]) + 1 )] ) + '/32'
            pre_node2 = '.'.join(octets[:3] + [str( int(octets[3]) + 2 )] ) + '/32'
            self.write_hosts(pre_node1, pre_node2, p.vrf, 'swp'+str(i), device)
            i = i+1


    def write_hosts(self, pre_node1, pre_node2, vrf, port, device):
        """ Create nipap entries
        """
        h1 = Prefix()
        h1.vrf = vrf
        h1.prefix = pre_node1
        h1.type = 'host'
        h1.avps['devicename'] = device
        h1.avps['portname'] = port
        h1.tags['edge'] = 1
        h1.save({})

        h2 = Prefix()
        h2.vrf = vrf
        h2.prefix = pre_node2
        h2.type = 'host'
        h2.save({})

if __name__ == '__main__':
    # read configuration
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))

    import argparse
    parser = argparse.ArgumentParser()
    # standard arguments to specify nipapd connection
    parser.add_argument('--username', help="NIPAP backend username")
    parser.add_argument('--password', help="NIPAP backend password")
    parser.add_argument('--host', help="NIPAP backend host")
    parser.add_argument('--port', help="NIPAP backend port")

    parser.add_argument('--device', default='', help="hostname of the switch, like cbk130546")
    parser.add_argument('--query', default='', help="query for filtering prefixes")
    args = parser.parse_args()

    auth_uri = "%s:%s@" % (args.username or cfg.get('global', 'username'),
            args.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://%(auth_uri)s%(host)s:%(port)s" % {
            'auth_uri'  : auth_uri,
            'host'      : args.host or cfg.get('global', 'hostname'),
            'port'      : args.port or cfg.get('global', 'port')
            }
    pynipap.AuthOptions({ 'authoritative_source': 'nipap' })
    pynipap.xmlrpc_uri = xmlrpc_uri

    if not args.device:
        print("Please specify a device name", file=sys.stderr)
        sys.exit(1)

    if not args.query:
        print("Please specify a query", file=sys.stderr)
        sys.exit(1)

    ce = ConfigExport()
    ce.get_prefixes(args.query)
    ce.generate_hosts(args.device)
