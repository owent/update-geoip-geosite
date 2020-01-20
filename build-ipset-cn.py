#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import re
import csv

script_dir = os.path.dirname(os.path.realpath(__file__))

def main():
    loc_file = os.path.join(script_dir, 'geoip', 'GeoLite2-Country-Locations-en.csv')
    ipv4_file = os.path.join(script_dir, 'geoip', 'GeoLite2-Country-Blocks-IPv4.csv')
    ipv6_file = os.path.join(script_dir, 'geoip', 'GeoLite2-Country-Blocks-IPv6.csv')

    GEONAME_ID_CN=''
    with open(loc_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'country_iso_code' in row and row['country_iso_code'].upper() == 'CN':
                GEONAME_ID_CN = row['geoname_id'].strip()
    print('GEONAME_ID_CN={0}'.format(GEONAME_ID_CN))

    processing_index = 0
    ipv4_output = codecs.open(os.path.join(script_dir, 'ipv4_cn.ipset'), "w", encoding='utf-8')
    ipv4_output_max_size = 65536
    ipv4_output_records = []
    with open(ipv4_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            processing_index = processing_index + 1
            if processing_index % 10000 == 0:
                print('GEOIP_IPV4_CN: Parse {0}-{1} ...'.format(processing_index + 1, processing_index + 10000))
            if 'geoname_id' in row and row['geoname_id'].strip() == GEONAME_ID_CN:
                ipv4_output_records.append(row['network'])

    while ipv4_output_max_size < len(ipv4_output_records):
        ipv4_output_max_size = ipv4_output_max_size * 2
    # ipv4_output.write("create GEOIP_IPV4_CN hash:net family inet hashsize {0} maxelem {1}\n".format(int(ipv4_output_max_size / 64), ipv4_output_max_size))
    processing_index = 0
    for record in ipv4_output_records:
        processing_index = processing_index + 1
        if processing_index % 1000 == 0:
            print('GEOIP_IPV4_CN: Writing {0}-{1} ...'.format(processing_index + 1, processing_index + 1000))
        ipv4_output.write("add GEOIP_IPV4_CN {0}\n".format(record))
    ipv4_output.close()


    processing_index = 0
    ipv6_output = codecs.open(os.path.join(script_dir, 'ipv6_cn.ipset'), "w", encoding='utf-8')
    ipv6_output_max_size = 65536
    ipv6_output_records = []
    with open(ipv6_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            processing_index = processing_index + 1
            if processing_index % 10000 == 0:
                print('GEOIP_IPV6_CN: Parse {0}-{1} ...'.format(processing_index + 1, processing_index + 10000))
            if 'geoname_id' in row and row['geoname_id'].strip() == GEONAME_ID_CN:
                ipv6_output_records.append(row['network'])

    while ipv6_output_max_size < len(ipv6_output_records):
        ipv6_output_max_size = ipv6_output_max_size * 2
    # ipv6_output.write("create GEOIP_IPV6_CN hash:net family inet6 hashsize {0} maxelem {1}\n".format(int(ipv6_output_max_size / 64), ipv6_output_max_size))
    processing_index = 0
    for record in ipv6_output_records:
        processing_index = processing_index + 1
        if processing_index % 1000 == 0:
            print('GEOIP_IPV6_CN: Writing {0}-{1} ...'.format(processing_index + 1, processing_index + 1000))
        ipv6_output.write("add GEOIP_IPV6_CN {0}\n".format(record))
    ipv6_output.close()

if __name__ == '__main__':
    main()
