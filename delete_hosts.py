#!/usr/bin/python
""" This script deletes any found host entry.

    It will read .nipaprc per default or rely on command line arguments for
    connection settings to the backend.
"""

from __future__ import print_function

import ConfigParser
import os
from pynipap import Prefix, Pool, VRF
import pynipap

class ConfigExport:
    def __init__(self):
        """ Init!
        """
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


    def delete_hosts(self):
        """ Delete hosts
        """
        for p in self.prefixes:
            if p.type == 'host':
                p.remove()
                print(p.prefix + ' deleted')

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

    if not args.query:
        print("Please specify a query", file=sys.stderr)
        sys.exit(1)
    
    ce = ConfigExport()
    ce.get_prefixes(args.query)
    ce.delete_hosts()
