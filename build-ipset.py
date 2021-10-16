#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import re
import csv

script_dir = os.path.dirname(os.path.realpath(__file__))

def main():
    loc_code = 'cn'
    if len(sys.argv) > 1:
        loc_code = sys.argv[1].lower()
    loc_file = os.path.join(script_dir, 'repos', 'geoip', 'geolite2', 'GeoLite2-Country-Locations-en.csv')
    ipv4_file = os.path.join(script_dir, 'repos', 'geoip', 'geolite2', 'GeoLite2-Country-Blocks-IPv4.csv')
    ipv6_file = os.path.join(script_dir, 'repos', 'geoip', 'geolite2', 'GeoLite2-Country-Blocks-IPv6.csv')

    GEONAME_ID=''
    with open(loc_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'country_iso_code' in row and row['country_iso_code'].lower() == loc_code:
                GEONAME_ID = row['geoname_id'].strip()
    print('GEONAME_ID={0}'.format(GEONAME_ID))

    processing_index = 0
    ipv4_output = codecs.open(os.path.join(script_dir, 'ipv4_{0}.ipset'.format(loc_code)), "w", encoding='utf-8')
    ipv4_output_max_size = 65536
    ipv4_output_records = []
    with open(ipv4_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            processing_index = processing_index + 1
            if processing_index % 10000 == 0:
                print('GEOIP_IPV4_{0}: Parse {1}-{2} ...'.format(loc_code.upper(), processing_index + 1, processing_index + 10000))
            if 'geoname_id' in row and row['geoname_id'].strip() == GEONAME_ID:
                ipv4_output_records.append(row['network'])

    while ipv4_output_max_size < len(ipv4_output_records):
        ipv4_output_max_size = ipv4_output_max_size * 2
    # ipv4_output.write("create GEOIP_IPV4_{0} hash:net family inet hashsize {1} maxelem {2}\n".format(loc_code.upper(), int(ipv4_output_max_size / 64), ipv4_output_max_size))
    processing_index = 0
    for record in ipv4_output_records:
        processing_index = processing_index + 1
        if processing_index % 1000 == 0:
            print('GEOIP_IPV4_{0}: Writing {1}-{2} ...'.format(loc_code.upper(), processing_index + 1, processing_index + 1000))
        ipv4_output.write("add GEOIP_IPV4_{0} {1}\n".format(loc_code.upper(), record))
    ipv4_output.close()


    processing_index = 0
    ipv6_output = codecs.open(os.path.join(script_dir, 'ipv6_{0}.ipset'.format(loc_code)), "w", encoding='utf-8')
    ipv6_output_max_size = 65536
    ipv6_output_records = []
    with open(ipv6_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            processing_index = processing_index + 1
            if processing_index % 10000 == 0:
                print('GEOIP_IPV6_{0}: Parse {1}-{2} ...'.format(loc_code.upper(), processing_index + 1, processing_index + 10000))
            if 'geoname_id' in row and row['geoname_id'].strip() == GEONAME_ID:
                ipv6_output_records.append(row['network'])

    while ipv6_output_max_size < len(ipv6_output_records):
        ipv6_output_max_size = ipv6_output_max_size * 2
    # ipv6_output.write("create GEOIP_IPV6_{0} hash:net family inet6 hashsize {1} maxelem {2}\n".format(loc_code.upper(), int(ipv6_output_max_size / 64), ipv6_output_max_size))
    processing_index = 0
    for record in ipv6_output_records:
        processing_index = processing_index + 1
        if processing_index % 1000 == 0:
            print('GEOIP_IPV6_{0}: Writing {1}-{2} ...'.format(loc_code.upper(), processing_index + 1, processing_index + 1000))
        ipv6_output.write("add GEOIP_IPV6_{0} {1}\n".format(loc_code.upper(), record))
    ipv6_output.close()

if __name__ == '__main__':
    main()
