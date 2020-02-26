#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import re
import base64

script_dir = os.path.dirname(os.path.realpath(__file__))

def compact_rules(input, origin_domains, origin_plains):
    ret = []
    for d in input:
        skip = False
        groups = d.split(".")
        for i in range(1, len(groups)):
            pd = ".".join(groups[i:])
            if pd in origin_domains:
                print('Ignore {0} for domain:{1} already exists'.format(d, pd))
                skip = True
                break
        if skip:
            continue

        for i in range(0, len(groups)):
            for j in range(i + 1, len(groups) + 1):
                # skip self
                if i == 0 and j == len(groups):
                    continue
                pd = ".".join(groups[i:j])
                if pd in origin_plains:
                    print('Ignore {0} for keyword:{1} already exists'.format(d, pd))
                    skip = True
                    break
            if skip:
                break
        if skip:
            continue
        ret.append(d)
    return ret

def main():
    gfwlist_file = os.path.join(script_dir, 'src', 'github.com', 'v2ray', 'domain-list-community', 'data', 'gfwlist.txt')
    LINE_SEP = re.compile('[\r\n]?[\r\n]')
    IGNORE_RULE = re.compile('^\\!|\\[|^@@|(https?:\\/\\/){0,1}[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+')
    REMOVE_PREFIX = re.compile('^(\\|\\|?)?(https?://)?(?P<DOMAIN>[^\\r\\n]+)')
    REMOVE_SUFFIX = re.compile('(?P<DOMAIN>[^\\r\\n\\/]+)/.*$|%2F.*$')
    CONVERT_GLOB = re.compile('^([^\\.\\^*]*\\*[^\\.]*\\.)+(?P<DOMAIN>[^\\r\\n\\/\\*]+)')
    
    if len(sys.argv) > 1:
        gfwlist_file = sys.argv[1]

    if not os.path.exists(gfwlist_file):
        sys.stderr.write('{0} not found\n'.format(gfwlist_file))
        exit(1)
    
    gfwlist_fd = codecs.open(gfwlist_file, "r", encoding='utf-8')
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
            # print('{0} => {1}'.format(domain, mat.group('DOMAIN')))
            domain = mat.group('DOMAIN')

        # XXX.* -> plain XXX
        if domain.endswith('.*'):
            domain = domain[0:len(domain) - 2]
            if domain.find('*') < 0:
                origin_plains[domain] = 1
                continue

        # XXX* -> plain XXX
        if domain.endswith('*'):
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

    gfwlist_fd = codecs.open(os.path.join(os.path.dirname(gfwlist_file), 'gfw'), "w", encoding='utf-8')
    gfwlist_fd.truncate()
    for d in compact_rules(origin_domains, origin_domains, origin_plains):
        gfwlist_fd.write('{0}\n'.format(d))
    for d in compact_rules(origin_plains, origin_domains, origin_plains):
        gfwlist_fd.write('keyword:{0}\n'.format(d))
    gfwlist_fd.close()

if __name__ == '__main__':
    main()