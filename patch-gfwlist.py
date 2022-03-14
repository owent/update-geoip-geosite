#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import re
import base64
import argparse


def compact_rules(input, origin_domains, origin_plains):
    ret = []
    for d in input:
        if len(d.strip()) == 0:
            continue
        skip = False
        groups = d.split(".")
        for i in range(1, len(groups)):
            pd = ".".join(groups[i:])
            if pd in origin_domains or pd in origin_plains:
                print('Ignore {0} for domain:{1} already exists'.format(d, pd))
                skip = True
                break
        if skip:
            continue

        # Ingore tail wildcard
        # for i in range(0, len(groups)):
        #     for j in range(i + 1, len(groups) + 1):
        #         # skip self
        #         if i == 0 and j == len(groups):
        #             continue
        #         pd = ".".join(groups[i:j])
        #         if pd in origin_plains:
        #             print('Ignore {0} for keyword:{1} already exists'.format(
        #                 d, pd))
        #             skip = True
        #             break
        #     if skip:
        #         break
        if skip:
            continue
        ret.append(d)
    return ret


def main():
    cmd_parser = argparse.ArgumentParser(usage="%(prog)s [options...]")
    cmd_parser.add_argument("-g",
                            "--gfwlist",
                            action="store",
                            help="gfwlist.txt",
                            dest="gfwlist_file",
                            default=os.path.join('data', 'gfwlist.txt'))
    cmd_parser.add_argument("-d",
                            "--dnsmasq-conf",
                            action="store",
                            help="dnsmasq-blacklist.conf",
                            dest="gfwlist_dnsmasq_conf",
                            default=os.path.join('dnsmasq-blacklist.conf'))
    cmd_parser.add_argument(
        "--dnsmasq-server",
        action="store",
        help="DNS Server for dnsmasq(e.g. 1.1.1.1,1.1.1.1#53)",
        dest="gfwlist_dnsmasq_server",
        default='1.1.1.1')
    cmd_parser.add_argument("--dnsmasq-ipset",
                            action="store",
                            help="ipset for dnsmasq",
                            dest="gfwlist_dnsmasq_ipset",
                            default='DNSMASQ_GFW_IPV4,DNSMASQ_GFW_IPV6')
    cmd_parser.add_argument("-s",
                            "--smartdns-conf",
                            action="store",
                            help="smartdns-blacklist.conf",
                            dest="gfwlist_smartdns_conf",
                            default=os.path.join('dnsmasq-blacklist.conf'))
    cmd_parser.add_argument("--smartdns-group",
                            action="store",
                            help="group of smartdns",
                            dest="gfwlist_smartdns_group",
                            default='gfwlist')
    cmd_parser.add_argument("--smartdns-ipset",
                            action="store",
                            help="ipset for smartdns",
                            dest="gfwlist_smartdns_ipset",
                            default='#4:DNSMASQ_GFW_IPV4,#6:DNSMASQ_GFW_IPV6')
    cmd_parser.add_argument(
        "--smartdns-nfset",
        action="store",
        help="nftables set for smartdns(e.g. #4:inet mytable myset,#6:-)",
        dest="gfwlist_smartdns_nfset",
        default=None)
    cmd_parser.add_argument("-c",
                            "--coredns-conf",
                            action="store",
                            help="coredns-blacklist.conf",
                            dest="gfwlist_coredns_conf",
                            default=os.path.join('coredns-blacklist.conf'))
    cmd_parser.add_argument("--coredns-snippet",
                            action="store",
                            help="import snippet of coredns",
                            dest="gfwlist_coredns_snippet",
                            default='gfwlist')

    options = cmd_parser.parse_args()

    LINE_SEP = re.compile('[\r\n]?[\r\n]')
    IGNORE_RULE = re.compile(
        '^\\!|\\[|^@@|(https?:\\/\\/){0,1}[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+')
    REMOVE_PREFIX = re.compile('^(\\|\\|?)?(https?://)?(?P<DOMAIN>[^\\r\\n]+)')
    REMOVE_SUFFIX = re.compile('(?P<DOMAIN>[^\\r\\n\\/]+)/.*$|%2F.*$')
    CONVERT_GLOB = re.compile(
        '^([^\\.\\^*]*\\*[^\\.]*\\.)+(?P<DOMAIN>[^\\r\\n\\/\\*]+)')

    if not os.path.exists(options.gfwlist_file):
        sys.stderr.write('{0} not found\n'.format(options.gfwlist_file))
        exit(1)

    gfwlist_fd = codecs.open(options.gfwlist_file, "r", encoding='utf-8')
    gfwlist_text = base64.b64decode(gfwlist_fd.read()).decode('utf-8')
    gfwlist_fd.close()

    origin_domains = dict()
    origin_plains = dict()
    for line in [x.strip() for x in LINE_SEP.split(gfwlist_text)]:
        if IGNORE_RULE.search(line):
            continue
        domain = line
        mat = REMOVE_PREFIX.match(domain)
        if mat:
            domain = mat.group('DOMAIN')
        mat = REMOVE_SUFFIX.match(domain)
        if mat:
            domain = mat.group('DOMAIN')

        while domain.startswith('.'):
            domain = domain[1:]

        mat = CONVERT_GLOB.match(domain)
        if mat:
            print('Convert: {0} => {1}'.format(domain, mat.group('DOMAIN')))
            domain = mat.group('DOMAIN')

        # XXX.* -> plain XXX
        if domain.endswith('.*'):
            # Ignore tail wildcard
            domain = domain[0:len(domain) - 2]
            if domain.find('*') < 0:
                origin_plains[domain] = 1
                origin_plains['{0}.com'.format(domain)] = 1
                origin_plains['{0}.cn'.format(domain)] = 1
                origin_plains['{0}.com.cn'.format(domain)] = 1
                continue

        # XXX* -> plain XXX
        if domain.endswith('*'):
            # Ignore tail wildcard
            domain = domain[0:len(domain) - 1]
            if domain.find('*') < 0:
                origin_plains[domain] = 1
                continue

        # skip invalid domains (hkheadline.com*blog, search*safeweb)
        if domain.find('*') >= 0:
            print('Skip invalid domain: {0}'.format(domain))
            continue

        if domain.startswith("q=") or domain.startswith("q%3"):
            continue
        origin_domains[domain] = 1

    gfwlist_fd = codecs.open(os.path.join(
        os.path.dirname(options.gfwlist_file), 'gfw'),
                             "w",
                             encoding='utf-8')
    gfwlist_dnsmasq_conf_fd = codecs.open(options.gfwlist_dnsmasq_conf,
                                          "w",
                                          encoding='utf-8')
    gfwlist_smart_conf_fd = codecs.open(options.gfwlist_smartdns_conf,
                                        "w",
                                        encoding='utf-8')
    gfwlist_coredns_conf_fd = codecs.open(options.gfwlist_coredns_conf,
                                          "w",
                                          encoding='utf-8')

    gfwlist_fd.truncate()
    for d in compact_rules(origin_domains, origin_domains, origin_plains):
        gfwlist_fd.write("{0}\n".format(d))
        gfwlist_dnsmasq_conf_fd.write('server=/{0}/{1}\n'.format(
            d, options.gfwlist_dnsmasq_server))
        gfwlist_dnsmasq_conf_fd.write('ipset=/{0}/{1}\n'.format(
            d, options.gfwlist_dnsmasq_ipset))
        gfwlist_smart_conf_fd.write('nameserver /{0}/{1}\n'.format(
            d, options.gfwlist_smartdns_group))
        if options.gfwlist_smartdns_ipset:
            gfwlist_smart_conf_fd.write('ipset /{0}/{1}\n'.format(
                d, options.gfwlist_smartdns_ipset))
        if options.gfwlist_smartdns_nfset:
            gfwlist_smart_conf_fd.write('nftset /{0}/{1}\n'.format(
                d, options.gfwlist_smartdns_nfset))
        gfwlist_coredns_conf_fd.write('{0} {1}\n  import {2}\n{3}\n'.format(
            d, '{', options.gfwlist_coredns_snippet, '}'))
    for d in compact_rules(origin_plains, origin_domains, origin_plains):
        if d in origin_domains:
            continue
        gfwlist_fd.write('keyword:{0}\n'.format(d))
        gfwlist_dnsmasq_conf_fd.write('server=/{0}/{1}\n'.format(
            d, options.gfwlist_dnsmasq_server))
        gfwlist_dnsmasq_conf_fd.write('ipset=/{0}/{1}\n'.format(
            d, options.gfwlist_dnsmasq_ipset))
        gfwlist_smart_conf_fd.write('nameserver /{0}/{1}\n'.format(
            d, options.gfwlist_smartdns_group))
        if options.gfwlist_smartdns_ipset:
            gfwlist_smart_conf_fd.write('ipset /{0}/{1}\n'.format(
                d, options.gfwlist_smartdns_ipset))
        if options.gfwlist_smartdns_nfset:
            gfwlist_smart_conf_fd.write('nftset /{0}/{1}\n'.format(
                d, options.gfwlist_smartdns_nfset))
        gfwlist_coredns_conf_fd.write('{0} {1}\n  import {2}\n{3}\n'.format(
            d, '{', options.gfwlist_coredns_snippet, '}'))
    gfwlist_fd.close()
    gfwlist_dnsmasq_conf_fd.close()
    gfwlist_smart_conf_fd.close()
    gfwlist_coredns_conf_fd.close()


if __name__ == '__main__':
    main()
