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

ACCELERATED_DOMAINS_CHINA="https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf";
GFWLIST_ORIGIN_URL="https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt";
# MYIP=$(curl https://myip.biturl.top/ 2>/dev/null);

go get -insecure -v -t -d github.com/v2ray/domain-list-community/... ;

## add accelerated-domains-cn
curl -L "$ACCELERATED_DOMAINS_CHINA" -o ./src/github.com/v2ray/domain-list-community/data/accelerated-domains-cn ;

sed -i.bak -r 's;server\s*=\s*/([^/]+).*;\1;g' ./src/github.com/v2ray/domain-list-community/data/accelerated-domains-cn ;

rm -f ./src/github.com/v2ray/domain-list-community/data/accelerated-domains-cn.bak ;

sed -i.bak '/accelerated-domains-cn/d' ./src/github.com/v2ray/domain-list-community/data/cn ;

echo "include:accelerated-domains-cn" >> ./src/github.com/v2ray/domain-list-community/data/cn ;

rm -f ./src/github.com/v2ray/domain-list-community/data/cn.bak ;

## add gfw
curl -L "$GFWLIST_ORIGIN_URL" -o ./src/github.com/v2ray/domain-list-community/data/gfwlist.txt ;

python patch-gfwlist.py ./src/github.com/v2ray/domain-list-community/data/gfwlist.txt ;

rm -f ./src/github.com/v2ray/domain-list-community/data/gfwlist.txt ;

cat ./src/github.com/v2ray/domain-list-community/data/gfw ;

go run ./src/github.com/v2ray/domain-list-community/main.go ;

mv dlc.dat geosite.dat ;

chmod +x build-ipset-cn.py ;

./build-ipset-cn.py ;
