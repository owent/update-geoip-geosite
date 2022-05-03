#!/bin/bash

cd "$(dirname "$0")"

SCRIPT_DIR="$PWD"

export GOPATH=$SCRIPT_DIR/gopath
export GO111MODULE=on

mkdir -p "GOPATH=$SCRIPT_DIR/gopath"

find . -iname "*.dat" | xargs rm -f

set -e

# start to build geoip.dat
cd "$SCRIPT_DIR/geoip"

unzip GeoLite2-Country-CSV.zip
rm GeoLite2-Country-CSV.zip
ls

cd "$SCRIPT_DIR"

echo "Start to generate geoip"

cd repos/geoip
go mod download
mv "$SCRIPT_DIR/geoip"/GeoLite2* geolite2
go run ./ # --country=../../geoip/GeoLite2-Country-Locations-en.csv --ipv4=../../geoip/GeoLite2-Country-Blocks-IPv4.csv --ipv6=../../geoip/GeoLite2-Country-Blocks-IPv6.csv ;

cd ./output/dat || exit 1
mv -f *.dat "$SCRIPT_DIR"

cd "$SCRIPT_DIR"

# start to build geosite.dat
echo "Start to geosite.dat/dlc.dat"
cd repos/domain-list-community

ACCELERATED_DOMAINS_CHINA="https://cdn.jsdelivr.net/gh/felixonmars/dnsmasq-china-list/accelerated-domains.china.conf"
APPLE_CHINA="https://cdn.jsdelivr.net/gh/felixonmars/dnsmasq-china-list/apple.china.conf"
GOOGLE_CHINA="https://cdn.jsdelivr.net/gh/felixonmars/dnsmasq-china-list/google.china.conf"
GFWLIST_ORIGIN_URL="https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
# MYIP=$(curl https://myip.biturl.top/ 2>/dev/null);

## add accelerated-domains-cn
curl -L "$ACCELERATED_DOMAINS_CHINA" -o ./data/accelerated-domains-cn
curl -L "$APPLE_CHINA" -o ./data/apple-cn
curl -L "$GOOGLE_CHINA" -o ./data/google-cn

sed -i.bak -r 's;server\s*=\s*/([^/]+).*;\1;g' ./data/accelerated-domains-cn
sed -i.bak -r '/^\s*#/d' ./data/accelerated-domains-cn
sed -i.bak -r 's;server\s*=\s*/([^/]+).*;\1;g' ./data/apple-cn
sed -i.bak -r '/^\s*#/d' ./data/apple-cn
sed -i.bak -r 's;server\s*=\s*/([^/]+).*;\1;g' ./data/google-cn
sed -i.bak -r '/^\s*#/d' ./data/google-cn

rm -f ./data/accelerated-domains-cn.bak
rm -f ./data/apple-cn.bak
rm -f ./data/google-cn.bak

sed -i.bak '/accelerated-domains-cn/d' ./data/cn

echo "include:accelerated-domains-cn" >>./data/cn
echo "include:apple-cn" >>./data/cn
echo "include:google-cn" >>./data/cn

rm -f ./data/cn.bak

## add cn
echo "" >../../dnsmasq-accelerated-cn.conf
echo "" >../../dnsmasq-special-cn.conf
echo "" >../../smartdns-accelerated-cn.conf
echo "" >../../smartdns-special-cn.conf
echo "" >../../coredns-accelerated-cn.conf
echo "" >../../coredns-special-cn.conf

COREDNS_DOMAIN_PREVIOUS=""
for CN_DOMAIN in $(cat ./data/accelerated-domains-cn); do
  echo "server=/$CN_DOMAIN/223.5.5.5" >>../../dnsmasq-accelerated-cn.conf
  echo "nameserver /$CN_DOMAIN/local_dns" >>../../smartdns-accelerated-cn.conf
  if [[ ! -z "$COREDNS_DOMAIN_PREVIOUS" ]]; then
    echo "$COREDNS_DOMAIN_PREVIOUS," >>../../coredns-accelerated-cn.conf
  fi
  COREDNS_DOMAIN_PREVIOUS="$CN_DOMAIN"
done
echo "$COREDNS_DOMAIN_PREVIOUS {
  import local_dns
}" >>../../coredns-accelerated-cn.conf

COREDNS_DOMAIN_PREVIOUS=""
for CN_DOMAIN in $(cat ./data/apple-cn ./data/google-cn); do
  echo "server=/$CN_DOMAIN/223.5.5.5" >>../../dnsmasq-special-cn.conf
  echo "nameserver /$CN_DOMAIN/local_dns" >>../../smartdns-special-cn.conf
  if [[ ! -z "$COREDNS_DOMAIN_PREVIOUS" ]]; then
    echo "$COREDNS_DOMAIN_PREVIOUS," >>../../coredns-special-cn.conf
  fi
  COREDNS_DOMAIN_PREVIOUS="$CN_DOMAIN"
done
echo "$COREDNS_DOMAIN_PREVIOUS {
  import local_dns
}" >>../../coredns-special-cn.conf

## add gfw
curl -L "$GFWLIST_ORIGIN_URL" -o ./data/gfwlist.txt

python3 ../../patch-gfwlist.py \
  --gfwlist ./data/gfwlist.txt \
  --dnsmasq-conf ../../dnsmasq-blacklist.conf \
  --dnsmasq-server "8.8.8.8" \
  --smartdns-conf ../../smartdns-blacklist.conf \
  --coredns-conf ../../coredns-blacklist.conf

rm -f ./data/gfwlist.txt

cat ./data/gfw

go run ./ --datapath=$PWD/data

mv dlc.dat ../../geosite.dat

cd "$SCRIPT_DIR"

chmod +x build-ipset.py

python3 ./build-ipset.py cn
python3 ./build-ipset.py hk

if [[ -e "test.dat" ]]; then
  rm -rf test.dat
fi

for name in $(ls *.dat); do
  sha256sum ${name} >./${name}.sha256sum
done
