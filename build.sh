#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")" ;

SCRIPT_DIR="$PWD";

export GOPATH=$SCRIPT_DIR ;

find . -iname "*.dat" | xargs rm -f ;

set -e ;

# start to build geoip.dat
cd "$SCRIPT_DIR/geoip" ;

unzip GeoLite2-Country-CSV.zip ;
rm GeoLite2-Country-CSV.zip ;
mv GeoLite2*/* ./ ;
ls ;

cd "$SCRIPT_DIR" ;

go get -insecure -u github.com/v2ray/geoip ;
$GOPATH/bin/geoip --country=./geoip/GeoLite2-Country-Locations-en.csv --ipv4=./geoip/GeoLite2-Country-Blocks-IPv4.csv --ipv6=./geoip/GeoLite2-Country-Blocks-IPv6.csv ;

# start to build geosite.dat

GEOIP_DAT_URL="https://github.com/v2ray/geoip/releases/latest/download/geoip.dat";
GFWLIST_ORIGIN_URL="https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt";
GFWLIST_GEN_SCRIPT_URL="https://raw.githubusercontent.com/cokebar/gfwlist2dnsmasq/master/gfwlist2dnsmasq.sh";
# MYIP=$(curl https://myip.biturl.top/ 2>/dev/null);

go get -insecure -v -t -d github.com/v2ray/domain-list-community/... ;
go run ./src/github.com/v2ray/domain-list-community/main.go ;

mv dlc.dat geosite.dat ;