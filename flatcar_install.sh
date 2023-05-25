#!/bin/bash
# Copyright (c) 2013 The CoreOS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e -o pipefail

function ensure_tool() {
    local tool="${1}"
    command -v "${tool}" >/dev/null || { echo "error: command '${tool}' not found" >&2 ; exit 1; }
}

if command -v lbzip2 >/dev/null; then
    BZIP_UTIL=lbzip2
else
    BZIP_UTIL=bzip2
    ensure_tool "${BZIP_UTIL}"
fi

toolset=( blockdev btrfstune cp cut dd gawk gpg grep head ls lsblk mkdir mkfifo mktemp mount rm sed sort tee udevadm wget wipefs ) 

for t in "${toolset[@]}"; do ensure_tool "${t}"; done

error_output() {
    echo "Error: return code $? from $BASH_COMMAND" >&2
}

default_board() {
    if [[ -e /usr/share/flatcar/release ]]; then
        gawk --field-separator '=' '/FLATCAR_RELEASE_BOARD=/ { print $2 }' /usr/share/flatcar/release
        return
    fi

    case "$(uname -m)" in
    aarch64 ) echo "arm64-usr" ;;
    * )       echo "amd64-usr" ;;
    esac
}

# Finds an unmounted disk with size greater than 10GB and prints it to stdout,
# otherwise prints an empty line.
find_smallest_unused_disk() {
    local disks="$(lsblk -lnpdb -x SIZE -o NAME,SIZE $INCLUDE_MAJOR $EXCLUDE_MAJOR \
        | (
        while IFS= read -r line; do
            drive=$(echo "$line" | awk '{print $1}')
            size=$(echo "$line" | awk '{print $2}')
            mountpoints=$(lsblk -ln -o MOUNTPOINT "$drive")
            device_mapper_usages=$(lsblk -ln -o PATH "$drive" |  grep -v "^$drive")
            if [[ "$size" -gt 10000000000 ]] && [[ -z "$mountpoints" ]] && [[ -z "${device_mapper_usages}" ]]; then
                echo "$drive" "$size"
            fi
        done))"
    # Get smallest disk size by looking at first entry of $disks
    local smallestsize="$(echo "$disks" | head -n 1 | cut -d ' ' -f 2)"
    # If there more then one disk having the smallest size, sort them alphabetically and take the first one
    local smallestdisk="$(echo "$disks" | grep "$smallestsize" | cut -d ' ' -f1 | sort | head -n 1)"
    echo "$smallestdisk"
}

# Everything we do should be user-access only!
umask 077

if grep -q "^ID=flatcar$" /etc/os-release; then
    source /etc/os-release
    [[ -f /usr/share/flatcar/update.conf ]] && source /usr/share/flatcar/update.conf
    [[ -f /etc/flatcar/update.conf ]] && source /etc/flatcar/update.conf
fi

# Fall back on the current stable if os-release isn't useful
: ${VERSION_ID:=current}
CHANNEL_ID=${GROUP:-stable}

BOARD=$(default_board)

OEM_ID=
for f in /usr/share/oem/oem-release /etc/oem-release; do
    if [[ -e $f ]]; then
        # Pull in OEM information too, but prefixing variables with OEM_
        eval "$(sed -e 's/^/OEM_/' $f)"
    fi
done
if [[ "${OEM_ID}" = "qemu" ]] || [[ "${OEM_ID}" = "qemu_uefi" ]]; then
    OEM_ID=""
fi

USAGE="Usage: $0 {{-d <device>}|-s} [options]
Options:
    -d DEVICE   Install Flatcar Container Linux to the given device.
    -D          Download a Flatcar Container Linux image to the current directory, without installing it
    -s          EXPERIMENTAL: Install Flatcar Container Linux to the smallest unmounted disk found
                (min. size 10GB). It is recommended to use it with -e or -I to filter the
                block devices by their major numbers. E.g., -e 7 to exclude loop devices
                or -I 8,259 for certain disk types. Read more about the numbers here:
                https://www.kernel.org/doc/Documentation/admin-guide/devices.txt.
    -V VERSION  Version to install (e.g. current, or current-2022 for the LTS 2022 stream) [default: ${VERSION_ID}].
    -B BOARD    Flatcar Container Linux board to use [default: ${BOARD}].
    -C CHANNEL  Release channel to use (e.g. beta) [default: ${CHANNEL_ID}].
    -I|e <M,..> EXPERIMENTAL (used with -s): List of major device numbers to in-/exclude
                when finding the smallest disk.
    -o OEM      OEM type to install (e.g. 'ami' or '' to force none), using flatcar_production_<OEM>_image.bin.bz2 [default: ${OEM_ID:-(none, i.e., the empty string)}].
    -c CLOUD    Insert a cloud-init config to be executed on boot.
    -i IGNITION Insert an Ignition config to be executed on boot.
    -b BASEURL  URL to the image mirror (overrides BOARD and CHANNEL).
    -k KEYFILE  Override default GPG key for verifying image signature.
    -f IMAGE    Install unverified local image file to disk instead of fetching.
    -n          Copy generated network units to the root partition.
    -u          Create UEFI boot entry
    -y          Dry-run.  Run some checks and print option settings.
    -v          Super verbose, for debugging.
    -h          This ;-).

This tool installs Flatcar Container Linux on a block device. If you PXE booted
Flatcar Container Linux on a machine then use this tool to make a permanent install.
"

# Image signing key:
# $ gpg2 --list-keys --list-options show-unusable-subkeys \
#     --keyid-format SHORT F88CFEDEFF29A5B4D9523864E25D9AED0593B34A
# pub   rsa4096/0593B34A 2018-02-26 [SC]
#       F88CFEDEFF29A5B4D9523864E25D9AED0593B34A
# uid         [ultimate] Flatcar Buildbot (Official Builds) <buildbot@flatcar-linux.org>
# sub   rsa4096/064D542D 2018-02-26 [S] [revoked: 2018-03-14]
# sub   rsa4096/D0FC498C 2018-03-14 [S] [revoked: 2018-09-26]
# sub   rsa4096/896E394F 2018-09-26 [S] [expired: 2019-09-26]
# sub   rsa4096/AF9CF1AF 2019-09-30 [S] [expires: 2020-09-29]
# sub   rsa4096/FCBEAB91 2020-08-28 [S] [expires: 2021-08-28]
# sub   rsa4096/250D4A42 2021-08-10 [S] [expires: 2022-08-10]
# sub   rsa4096/267EC954 2022-08-11 [S] [expires: 2023-08-11]
GPG_LONG_ID="E25D9AED0593B34A"
GPG_KEY="-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBFqUFawBEACdnSVBBSx3negnGv7Ppf2D6fbIQAHSzUQ+BA5zEG02BS6EKbJh
t5TzEKCRw6hpPC4vAHbiO8B36Y884sSU5Wc4WMiuJ0Z4XZiZ/DAOl5TFfWwhwU0l
SEe/3BWKRtldEs2hM/NLT7A2pLh6gx5NVJNv7PMTDXVuS8AGqIj6eT41r6cPWE67
pQhC1u91saqIOLB1PnWxw/a7go9x8sJBmEVz0/DRS3dw8qlTx/aKSooyaGzZsfAY
L1+a/xst8LG4xfyHBSAuHSqi76LXCdBogU2vgz2V46z29hYRDfQQQGb4hE7UCrLp
EBOVzdQv/vAA9B4FTB+f5a7Vi4pQnM4DBqKaf8XP4wgQWBW439yqna7rKFAW+JIr
/w8YbczTTlJ2FT8v8z5tbMOZ5a6nXAn45YXh5d80CzqEVnaG8Bbavw3WR3jD81BO
0WK+K2FcEXzOtWkkwmcj9PrOKVnBmBv5I+0xtpo9Do0vyONyXPDNH/I4b3xilupN
bWV1SXUu8jpCf/PaNrj7oKHB9Nciv+4lqu/L5YmbaSLBxAvHSsxRpKV53dFtU+sR
kQM5I774B+GnFvhd6k2uMerWFaA1aq7gv0oOm/H5ZkndR5+eS0SAx49OrMbxKkk0
OKzVVxFDJ4pJWyix3dL7CwmewzuI0ZFHCANBKbiILEzDugAD3mEUZxa8lQARAQAB
tD9GbGF0Y2FyIEJ1aWxkYm90IChPZmZpY2lhbCBCdWlsZHMpIDxidWlsZGJvdEBm
bGF0Y2FyLWxpbnV4Lm9yZz6JAk4EEwEIADgWIQT4jP7e/ymltNlSOGTiXZrtBZOz
SgUCWpQVrAIbAwULCQgHAgYVCgkICwIEFgIDAQIeAQIXgAAKCRDiXZrtBZOzSi5G
EACHLSjK24szSj4O8/N9B6TOLnNPJ17At/two/iHfTxrT8lcLM/JQd97wPqH+mVK
hrZ8tCwTZemVeFNXPVy98VYBTjAXscnVh/22DIEYs1wbjD6w8TwgUvzUzpaQJUVu
YlLG3vGAMGaK5FK41BFtsIkar6zaIVy5BPhrA6ASsL9wg9bwSrXT5eKksbaqAZEG
sMiYZxYWzxQHlPu19afxmzBJdVY9YUHEqBYboslGMlLcgErzF7CaiLjDEPkt5Cic
9J3HjIJwlKmVBT6DBdt/tuuzHQntYfPRfOaLVtF/QxRxKNyBtxYndG6k9Vq/cuIN
i5fHpyZ66+9cwswrLISQpAVWa0AW/TENuduj8IU24zCGL7RZVf0jnmALrqkmBTfY
KwtTdpaFle0dC7QP+B27vT/GhBao9KVazfLoAT82bt3hXqjDciAKAstEbqxs75f2
JhIl0HvqyJ47zY/5zphxZlZ+TfqLvJPoEujEUeuEgKm8xmSgtR/49Ysal6ELxbEg
hc6qLINFeSjyRL20aQkeXtQjmZJGuXbUsLBSbVgUOEU+4vvID7EiYyV7X36OmS5N
4SV0MD0bNF578rL4UwhH1WSDSAgkmrfAhgFNof+MlI4qbn39tPiAT9J9dpENay0r
+yd59VhILA3eafkC6m0rtpejx81sDNoSp3UkUS1Qq167ZLkCDQRalBYrARAAsHEO
v6b39tgGxFeheiTnq5j6N+/OjjJyG21x2Y/nSU5lgqPD8DtgKyFlKvP7Xu+BcaZ7
hWjL0scvq0LOyagWdzWx5nNTSLuf8e+ShlcIs3u8kFX8QMddyD5l76S7nTl9kE1S
i2WkO6B4JgzRQCAQyr2B/knfE2wrxPsJsnB1qzRIAXHKvs8ev8bR+FfFSENxI5Jg
DoU3KbcyJ5lMKdVhIhSyGSPi1/emEpbEIv1XYV9l8g4b6Ht5fVsgeYUZbOF/z5Gc
+Kwf3ikGr3KCM/fl06xS/jpqM08Z/Uyei/L8b7tv9Wjop5SXN0yPAr0KIGQdnq5z
GMPf9rkG0Xg47JSQcvDJb0o/Ybi3ND3Mj/Ci8q5UtBgs9PWVBS4JyihKYx2Lb+Wj
+LERdEuv2qRPXO045VgOT5g0Ntlc8EvmX3ulofbM2f1DnPnq3OxuYRIscR/Nv4gi
coNLexv/+mmhdxVJKCSTVPp4SoK4MdBOT0B6pzZjcQBI1ldePQmRZMQgonekUaje
wWy1hp9o+7qJ8yFkkaLTplbZjQtcwfI7cGqpogQmsIzuxCKxb1ze/jed/ApEj8RD
6+RO/qa3R4EGKlSW7FZH20oEDLyFyeOAmSbZ8cqPny6m8egP5naXwWka4aYelObn
5VY6OdX2CJQUuIq8lXue8wOAPpkPB61JnVjQqaUAEQEAAYkCNgQoAQgAIBYhBPiM
/t7/KaW02VI4ZOJdmu0Fk7NKBQJaqVa3Ah0CAAoJEOJdmu0Fk7NK8WMP/R+T//rW
QeuXMlV+l8bHKcbBGWBvvMV5XcsJKDxtzrclPJLqfuBXSDTwqlirXXqlEeI613kE
UWG0b0Ny0K87g9CnkbsJiizGtyQJp2HuMnjRivTd/1V30ACCaK01nbu1/sdOk6Y4
Cimv+mGEgzjcXVXs72p+qqhDEaMgf1GYjDrzVHUnKUNIU8QOG2HRVhpP27bOg9Ao
a9Exdo04w3dXxso3KGeVkEE8dN0rKmHQ67jcCqKogzNlsIujbJkgRbwk/e3BgDWX
ifQSMW4SAAl/PVP7z3h6QoLcYSddOMMYwqP5Oqe4obBaKgVrn705s/Z0pW5nEzFg
38hEoJe+CCXjPl0zjHKQGzhwR/MLWvMf6jO06uvASiJuU/hefVCCek9b5SLn+IPU
J+uLh57F1I7O4ohPWY9+sbrpibx2pcSmcefVMwX/iSt6RNlBITYVQLGN8+/0gcRz
3jGf7m+M8Y7KYrmFxtwPsFejygDr6VVvoUarPPnJSzP+UdPqzUCcxdnV7Ub4QMRl
wUyvnwgnpn0xOsZ/Pdh5gOC06Yrkjbr12DWIpUxy/9z/QR2TeImi02trRKpCh9xw
0bKlsWBt1oUnNnQjnMUB9tmWsF1I6DrO/FUcB+5d7iy+MnPB1LIKS8JokODWIrOq
dg763UZfGbp4EbLlO1vcwIdKC6AGoS6hoyPUiQRyBBgBCAAmFiEE+Iz+3v8ppbTZ
Ujhk4l2a7QWTs0oFAlqUFisCGwIFCQHhM4ACQAkQ4l2a7QWTs0rBdCAEGQEIAB0W
IQQeEA3Xpnem+aUyyfm1HeN3Bk1ULQUCWpQWKwAKCRC1HeN3Bk1ULe4hD/0XLBuo
inLaN2wVQpbjeIEG9Shbaax+BmsuufjiVgNxKEkBg4q6/miCpdpjYmcvv7nNG5uK
zuQ/fnLzgldiVS0G+0BVBelF1FlT85xaI/enIrsvTauGEsfie7/ljrkV//0MFqdB
ZnM680JDVbvl8f2RDBACmz3PoJr8kg3PZwvb028effeTqhZ8zA5ZW5rum0Cn6dOb
v3OrCyQw/aoUvjH65j3T+fr17Em5dYaxNShFxoMBKxSsr+V4opwGEzBRxuoLrzAl
/LcazNAL/CLj+7JBxFj4FL5fB7VQcBEBDFBwg0ropojUeqT8Y2oyygnwLHc4otwV
TNxezToTFucnIq87IAqpTdEe3dHXx1CRJAyIeXxh6j+rYpidiL4CegIczva/xE+P
CqKV1qsGPysD301pXEYy4W1nLuST1tu/xbZCIJdqUwOxsVN5D9UVsFEr4Szfq0QC
14UQzMeXJSdXE2Z1TAnl7381AUC8LoRp55BH5Jih/zrUT1+HrzwdWBZdBJc04f5I
RiZqhZ8Goso5Ki6yFGCEXuitQUyWS0OWkZTX4m2rNIiPMw8PVweQ+yeqwaAapfm7
JX4l3Wa9fRpwK8LLV5/iaXti7IEla51lCCHRn+yM+0XcYI//53qQXVobcaC8Z9uy
LfJCjCtETknO2/uGL+kNyoZ4ykMfIhqOaxZWnqfzD/4kHM+EB4Yuti1kxFmSdnjp
MLEOXNFRoJcvPL7kw6ZMQaWZ96UOdlcL2GiHWAyYThsSjWez+kZ60GuDL+JwfQaR
InavuacP3Dw2eg8/W5XAT/G2EEmA4wuDMXZ07aPa3nJPdlCMcwxQLyHb6ZgModxZ
IHXaX/JEylapdh0j4sQf5P8OvK2Qq212OVuIaZPnjloQDeJqJTzP9iGDaJ3Ne6gM
n6nZ3ZIK1qtJc9WxRtjIOLS2ZdMSB5JWb1gE4nEkvDChbWKfeMpv5ox8G6HJe9Xk
sygGj876vmyAHDwl8zsYMvWeFZONxsahKpDFjXKMcnIpV8ZPfaCT4r4G6x4Qil8u
A1iwCKXo4d+uq3qrRKyhGOE+B+H/5QCGmmfAXhBVsR2aUldK0kx/IVi7HJD1aBRF
k+cpC0+vMw4O4f4qXzm2z5qWHftcB/EBhN+h4+IIDSE+wEtz9OdEpXXbPZ1sd7eS
8K4OjjliG2meTQE/wvn1BNtJVJ2rGQX6moCGx/1FYdLXLROv6hOnBslMVHFRbe+9
OmTFXEDlb6Nh/08PwYdyqk4qXddebALpC0TmyEty8QnjEmL1IhDtMTDVlj/33imb
L0waKqGJ5U3s2fA8VaDZQWL6U/c71xtuVFt6trS4rnsoBzlILPfC1n2wpPvKPEHL
avOKXgf6jXnmSzi5GbnBgbkCDQRaqVbRARAA0R+Z6SrbAI5b8m/j+Q3yc2tc5wDB
i7Hly0SW95ydLkKGaGvHhpLrBM5WwKdtQzF45A9tlyu6iGys5HWPRW3BqMpZrcv8
+2QHyoI2lYM/b0ioai2gSZB+lao955iJyBQ8c+pLSybxwcdaXTb6iBLGReCYXlrL
QL6H+NYw338x8bhRvaDanPQis81GzxtSZgRjtZbAGSvOgq25A3oCTF45O8cfBz+I
FxNaziS7x6lXuqOatv5n3HzffGOz3q1baKsxMRVGx3PdAI/LvRRd9SeBeTpFZQYY
ujCC5K8ds7yxB39Hel5llKnoXLHNm/wLGukXY+PtJVzhtBDL0X3o6OUfsb9tPzwM
oMyA8gRXf94nw2XRT8MMrjGChB7Clfq9AFP3e44D3MaVWbEGOWNG9rQ5s72dk7dF
K416D5cc+BQ8mvllYzZ8gzOgYKnlfVmhqVDAIkFz601+lLRUdK4pD0t1BCmlINSY
EKQNmp0NCSNVCbWWscKvTjboqb76oH/hjnIDqh3GeGdnIJ8vGwUdNN2NBA0rrK8o
+lD1Kc+e6Whe5xORc5krUZYtDCwW6ylRb118rmrHsojxoTH/kGr2IB0po59LT01l
M6KjLfGWrz76jJZmDLQ2gDBZNjuqDV+raHaKpVgUlbTHvmVvumBCm50Haz5w2vbM
txDxVhxU1FdYY00AEQEAAYkCNgQoAQgAIBYhBPiM/t7/KaW02VI4ZOJdmu0Fk7NK
BQJbq1h6Ah0CAAoJEOJdmu0Fk7NKGuAP/0LeLoKVOI8GRiU25bBek4mElKV5YNwU
8QMf75VPnRxklMFGkrPDuVCHVIsOUGo7jF4EHfH8ACgXNsFx8v9pMgsvk4WvfxbY
hepoNNOF/PLsPc125Z3hNq3uJsAMEpijNt8pNXgMvYj6mUKRGuMcIm1KLlczknwU
vtAIWSV+qqpCUL2miVPzp7Y8lexUeB1dsxAiF4btZIJ2i53S72kPMqwLzHdrPxDt
TiIweNz/T5K+C19MDAZ9AVp5qTcPWhQMDnNz3bY/4B2NcAwPJTCRxt7Ne5Ufxpll
3D92jwKZxREBdBPlRq/Qr4JEm4VXOw4QLFoU/WOyRBd4q4aNeFR00J5unZ2zcQ/E
ZL5OvHmkZ2Xl27Cuky1dAnT6hdadjMgWfQB/giXfP8Tu0Qpi7ISv5fEyUh70RpKr
SPdbUIR92IR8Qu862SSZsn7KoywUb2lFYzj6N9c1XORBexgRQgGAMdcT0REXyyS0
bl+9aBRntiw00FkEe7V1+EOLTi40bbddLC0Oatxa35lYg38VYmnhHCrkUl3iCLa/
AlhZmUGXSwmACNRzVRzFPAZMjdql+SEIF0XLYe96sb5twX2aztemy0GMU0ybK3pH
eYrpccUsPRPiHvT4k5TqAA+D1Y1WDjEhidPCbYeyThhAu+lfJiSVn2ex8ESByA/c
/QqOMREjkWlwiQRyBBgBCAAmFiEE+Iz+3v8ppbTZUjhk4l2a7QWTs0oFAlqpVtEC
GwIFCQHhM4ACQAkQ4l2a7QWTs0rBdCAEGQEIAB0WIQSmIfHalsk8Y5UGgy1gNEOh
0PxJjAUCWqlW0QAKCRBgNEOh0PxJjFXaD/0cyALbk6YivbqAMCMXnfBFj5kOoG5T
EGC7quviOVI+U5yNyFzqJtayfaxX3EsF9IjZR4cW58gdcQALS/gGAukexDigoYUz
2h1q2r4zr5pxbj+ez9+fftNDpwp7CmuaB5bzVh1bu8gwVJf4yaSsGubBIgfaysB0
Mzc4eJqIpDFMRQvSOOv7TgzXqAsXQuphoqkB5RuiKtKeugv4qofH5fuM3C/Y4QZ8
edQlTA41KOay1a76xAK85a8qMCjVQVCrepo5+LYXwZAryp4WKIbTSbUNRr5GGgSa
UWBe0/Rz5eqOL3r1YV1WzttWgBLzZUZJqvaYoWtfJGwjxDAFebE+meqtLIh/IDEu
Tc4D3Vge6kCI1jjNDKMZQYf6j1rybKPVzOgkxjCyRcgUI8Y904l9LZ3/BiRV8dY4
nBjWmCYVJPlAVzfDxFwF+A2kKInskPriiYJpFX8MVjy/6GfkJTtMZo1bovSDZZ0n
2MbQ+V3mftV8GkL+RPU5xQ79dPx6Ki81Dh31/T0d8FkEpWLbDy3gc1qgvRWcp6bC
uS1Rg0pf7+ftRYDEW7BBOBzmqfNljolHMWPeZT/1sCs7PmDS+kErZARFm0huMljt
8MNx50KljIVGDUbjOmDaOopTqKFhho/UTTe1Kho3iwTIYIgrzfuCT7t2k0Wx+/NI
y6BcGlPHU/R95gl0D/4yrId19rW5h425bWYmKZ6Ilh+H1zipl5OS0iEllmm4sLcp
Mub2+B+YFU3/EvbF0zkCny2HXy2gyZLhbvNm6Zr4FPW/xfaEnB4OXOOnUbA4+RNf
7bTngPXwhaxN+wQti+Uo0LcwKAU5KIBC9KcT46NirakEu5+5XaU2r+lsa7hlJWfb
17e4tmcOB4QfMTsJu+4DcWJqu+cdtm2N4VcorJCvfw/EffnGaGK0mwRvJp7CZiWi
Vc3T70fH+Rbv6NrgJEFV90XuoetQROwqjBEdbL8iNcuvjWO8j8NSlRKrV+UivP+w
yDf0UCQoMTnFshBM0ZnW+8i/jqsg3kKxs7xuxCZVMfwxzkNb6h/YlbqjRR/hFZ56
Chf1guaCfYJn0vCtdTLWimasemZfcKX7oE9EIbrs8FZcd89FkU0wgrJRscoUAiVP
mbkklT9AvTy7Gp4CCMS8Z22r3Q0d3GgIvFNhakLyDzBKPBf+vJyQEx9SdFIM/Kjv
4grCEjQNrWXXsh8ecurhciHPuiykffmMYyWUzdcc0pQyyyhoYiGbmflGIKx/6M9D
OOW2Q4k7ogubPRLZ/nabZnxJdIbi8WVXgSI2JCuO3+i9dpW+Q9s8F5mPht1QmQnI
ZrA5R/pLRP2oE9x9LDvUPLkQdLIB9RRyTw6D5A1UOI4TuLPOhFpcXqNODjJcO7kC
DQRbq1i2ARAApdwHI9mdWuHcct2tCY4uRFR9m0CliX2vJ3ZOHBmo1wS3HBv0BkAv
zmQwOE5xMDk6i9aN/w6fYii0s1Pfj2cwLz8Iw93icnInk7WGU2KoryWM9+KNGIA+
XOtyobwTh4BHY5ggeYDkdOs7Nrlj1FTlj428NaevU75Cm9xQm6aAZnZZtjSDBTWw
BuSXfFa70kiZzpwKMP/jB8ylWdA74VzkCFfYcdwJHzzrcDS64VRqNhWM/vRFJmLP
wN4MHkAE5RDb4cjGAwkwmZQuDzuk2O9oOukxKd7v/ZUmql4k0qDxi3M9dC3SJJ+O
fVPRlyZ74UVlspgjr5zxSBCerj/aDbVSWWr6JjgeRTQdg6WKhO0+mfmttiANxv/a
fBMDaxys9ee5sJL+WHP62fucD8ukmMEVM0P971U/JBfV8r8VRpy+OENgt6ynJ9dV
4YCdOT2xo42YwkBCYcVOF6iY2YqFd3oDSZARqEk4vr+A2/eNDU37+OBWr8E1pfO7
H6FW4/tVRxYjywat6743e0VTjNbwPGmOFBGc0VuwCJzRsY5dwIi9hlXDGwfNpgzd
tB+ON4BEY4f8ooSYCfHa9G2HeXj/+txxN6Km8Oh8OnQpyfJ6POQQVXX+bUG1W8EC
jNBdoi6m00ZqNVtDsNbdKdWTYYhKtgPUOreGmF75k+LLjiqO4jIE1E0AEQEAAYkE
cgQYAQgAJhYhBPiM/t7/KaW02VI4ZOJdmu0Fk7NKBQJbq1i2AhsCBQkB4TOAAkAJ
EOJdmu0Fk7NKwXQgBBkBCAAdFiEEYozCEpOAZdq047lJqKvwBYluOU8FAlurWLYA
CgkQqKvwBYluOU9wWBAApKMHrxbOqWa0gij3ODcvzpky76y1YWG45iroC55B56X0
XslUpHJno7vTLobV5aJDeXlgaYD2ptn53wW31fTZL/1P0lkyIu30OwYwLvOxaFjT
rsVPCwTz80h6TzsaShFiKirZJhPg5UzC0xfmM4aaQGsoC/Z5pOTyfrYrXgbQPNUJ
f8zagYqpo0WZoG2R2cNwH5VzlJAv/JBB0SdMVgBS7bUXP1eudqn1gmZxw6GUEGU5
5tj4X72ceYHiA+MMlKWsvpwJD9iRsl3yuzcBi8yOA0/jSrXu+5BLGaAAXMyMKETg
+e1ierxZ64yoV+AU6xcKykVzThxG5SoH6NiXsCs0XBOpWxQjfJ4MAeWLfTRMf805
2OSzRsIf1/p2byyTbuApshp//O9c+jbPgEvG7G4VeQdBROY2/46+XR7Q0BrDMom9
Bmk93SSbG9oubYKKALrjJaPIzTieLM3t2zLKZ/RJ6JARYDd6+BMdVNs9QS6Hkwq1
4lIDxz9jqenAXSpnK8fKg2xxzz/UFhoThlY/wlrWP+Sa4FQl1lorcz6Xid+yNoxF
CZw+iWx7FMng0QDM9rtyhAbFkm7JFnDuojVFeNTdTUy+siAZB0cFdP84BkcYugvx
WGM8uYydVOrPlI/nzGomgljIqgzvJm+Crun8eYggmItY53U6xDJmQT7Xrtk7YCa+
0Q/+PRuDorQauvB53mfynLywqxn3h/NyegDrlyq+5Nqsjm3nq0umUSG4/kXMwALy
0h6boyGWR/rkHnLOE1gLQ6fSlpcN8YHtsW6+czpkVH1b+wws/RPg49muTADHeYeM
n5eC0aVrUq7D7IVH+UGILDWJuzq2b+jO/IpXd9kIPlwY/2PFIjwfoSd7W+pjgVXh
6Z+xtWE5mVXnSfxPIXxv/cNd9LtYyT9R6RN7Xu+3hJz/BRp6MUANbdErYD36zERz
GKUO2eJVbOJReevXb24SZzIJkpBF2qwI5dEl8yk12YpGCu75XtFRux3cVhDpdQsx
+/RZGV7Id1X55s4/LiqF5PSEFTB4kZpiY+meq3sKOPT+Ra9BLeur8yo7ftMK13WB
BL2e/mzwfw+s2x1sjWRCuc5KbnK2yTY9ske2hdtAPmVJTDXBO3JWfZj5xKuuc3mp
q7OEd9+gKTiW4PyZfxQIzwXi9BJ6R3+ax7WYR0bi7Gll0910RNFV3MOiLhupIS0Y
BuipB6OgQNFUSjB6vammTd3R+98jIrtWyRDHPmdtgRcK86EbRpj6MHd7rATkdG+S
D0+DXGwfuWIeq2OA+P6lHWEmjlepFSEBS72P5jmpbRtNd+aHN23VesPI/WBQkfBU
4Tu51CGRd4KZk5ugFZ5YqjaM3m70od1zrsdq+BCNsfzuJqW5Ag0EXZHfzAEQALaX
xQvhNPHFx5PiroyTkEX95SsFuoMVnkXHfjEsBKStVJ6ZEF6t1PV/q+Kj+rQB25up
11tfQdElG8Elw46tsvlfWt4uVsdcttUWNHSsygwfmZbQxBVt+nlWXMaC3/124KP4
ewOn6YAw9biL+cioV0L0fSw1bnUv9LtUZS0h+KuyQ1KFFv015z9uC2LLT/v0XP6S
8AW9LNrKNI7q6XOW5JpJWSOLGpc6eS5F2T/eplpjxUr1Ua6PSH+g0LJSppbCqIf7
lNaRCVSSTD2gxCRw1MwWPKqYnseXoilcQe+Zv/wW9k0wyj9ekfkca6mCqBGhe88D
SqBZVaOfCRNNW1AdsTtIJcW9U1e0WFQIVMCADdLyze7ktTHIc8+/vsVM20/8eMEG
MSspehWgJOEgNDhPTAHyolfa6z/U/lOvtTMkhO5L6XrIwSDaKvYHqVuRiOoPXYey
Qfe+PAGszbM9+JH2j3JywKb7RuK5MUL5PBfUGgHseikK2697ix7z2theIjiAO0sm
/JkLC2Q3zKxQL3szkO70xWB5L2yajifNtvncqqPUvq6aFkxcJ1H4DXoDpdytKBt8
KtcjJcwPBrw7zMQ+bFXRdTDbtDGZxc0AhhfvboC0NtxzpTi0E2z4gY3YGjseJs6h
BW4d875PKG8oBsMMNIqjIuldB0vTQQmh45D/DDG9ABEBAAGJBHIEGAEIACYWIQT4
jP7e/ymltNlSOGTiXZrtBZOzSgUCXZHfzAIbAgUJAeEzgAJACRDiXZrtBZOzSsF0
IAQZAQgAHRYhBMj+hTEBIuYmdT2wzzvCD/ivnPGvBQJdkd/MAAoJEDvCD/ivnPGv
9UcP/2s31nMRdyXYAL14xiU5L4lQP2Rsr2BvcsdeCn/ZjK4e5tv52sOAYKkk7yhH
2Egxss+liM70Tg3XWnTfmrxgM1uY64Pvx5G9qlLoDzXElEAHWlIkyV5bj/SUHS3c
B2nuZjZEpDgXGYWQaHV5We0QepvV3e3sv9saOcQN5ihlGnr+MlEOxNQbAnOMamWj
S2ztMakfo/kEH2OuZcikgmT5d2RjQooamgKQXKyVOzOlxYV0L5sGZLSK0DFV3KTI
Qs/ccfr8MLv902If/mLF62lz5ba24p2wUtM+vrp9EaXWExTYR9WTcYBPM8tG7txF
q8mopL7siu/fU/XPUitWjSi6ZDX6RFljESjdR3xs7CwI/DErEak2T8Y3/inAHnGM
HB5amPkqv2LyeEEQ7ZhIjmA4mWgbTsPiQet+qY+GqSKlSIGoJv4KZKBmBKFW6PK6
xZpWioGj+BLqtduHc0yPf0fW6FDaI57IHMZD8kVXw9dZpn14wExfeYsoptHXRecH
1ouSWd4/IK6PJRWzoAiOu481IREkDml3Rlhqj6UUr5+eseQ6SFWdFo3KlfC+7O5K
VsAmEx99bj/9w0NLr2lHw2uEAPTdpDVUWh0hURxCu4uyEVsCdUmNklVAz9t/zqKV
a8A/MMYxaytsw5e+QftTKPlTBsCJkJo1qypcQDe78OdUIecYABUQAJIDOIV19WSK
ruQW2ICZdMI/6BbGzrKMvxbJnzdC7PMnJbXDEqzsGMMYziK3Qhf/zi4SpUEP/RRe
qJJjzzguFYEtP21/ugXFX0/4uWBkGGkPcSmqtanixg1LefJIlw6g1ZWeteU7x68d
dNyyEC+BP7HaVHX1mCfhkPiPH3zvTa07boOJhsaYWOGyc16RtVlJSJXxgTEY2SJD
JwtnSf5ujVOfIsOGQVshB95BZdGCYIru+n7YSD0ghcm6az0Dnwr6sscQLYOpwb/O
mTp8P7lG9aEqbzSPDtVhWrrbIp+jibgTzGu+jqMFFpBSTcD6F3ClAOkmFpj6UHLn
LnFWBs7rbznZVB1D1EM83ETnE9gc4C3n2OL08kAKHQ1RWDQcG3rU7evgxf0kBFdA
tgn4tIU2qlyR9MG2hy7wsXA9oR9/CndX+NJrkYSQxiRT9OWi85WBIV6LqkdypE3O
fbofQWtv8IuFfAv/a8Ah/38hXn2N1KcVm4IbrNeKjrlmVIhVSkHjVQcX5iw/tPuX
rTqi0XMNnnf0GneaTTVSI1wTa66Ha9SY+MsWKEK7aBI6S+ecpSG7oRhsV7yvzXPQ
ul9QP/O4K8SmteNujH88+sfj62+0qJeHnxAgMo62VXR9L7a0zSPIQJXpNun6BJn6
HKbWRxot9GQuVdS+tRnE8fZulLeBvixyuQINBF9I4E0BEADd8vDObd3EctBbBMFc
8BPjuEgnfC4c+EltYEm69EZvhVh3jtWtSBrTS9AaT+7+Dt2LphDal0Z1u753R6vL
PVIVt01983cWOP8+tEG8Kj7ghfMV3hBJmYyK8Zumh37L7C9ye/JHUDyePmaDJuCb
DSwKR6H7UXlAjnmP4gmSLnmAZXBEQX1E3AgZy9qMehRc/F4ZZQlU3bSreyNJCm1F
3/FNhQRmsUDv4fHcYnWSwbl8OGqmRfCAj+bzWt998zjapvcwEe/OZfqXgdJ9ZWJc
g8nirp0iwP5bKtC6UTZk5mU6+BukZ4oKhtwlX3/OuHDfshy4+QiSUL3aZhOAVGlx
n0ZU2ERYFqef2x4+THRj9+Y4pSLNbapSHQgSj7kPupS7txtQnJzm+GxkmbbiwgtZ
91Dtv6k5hycPiiCV+UfwvnKEA7lGHHkGCdLS/zWBDb8Iq6RwSOrfFlHG8ihR94zK
rUEYUzrZQa9aCP1aWdrdcr/RejDgNREq+eR3x0OvPqKQRse/NtstvQDzALbztYgR
7ObQMNrK7F+ba1uF9m3fZFi7l79xFT8kvFOzyBmCdVyxqRrbEmC0svG4x3SUMBEn
dvNTjnQMId1WYvEkLldp3Waj0Zca2Yf86oWROLW39xVphTH8MouE97fvCNIKzKD9
L7xF5TJrw02JHW5lR+4rGI8HMwARAQABiQRyBBgBCAAmFiEE+Iz+3v8ppbTZUjhk
4l2a7QWTs0oFAl9I4E0CGwIFCQHhM4ACQAkQ4l2a7QWTs0rBdCAEGQEIAB0WIQR4
KzvJ8Qz2OKXc9RBbKRDL/L6rkQUCX0jgTQAKCRBbKRDL/L6rkVMzEACYgX7Yk6hh
Qp9BW27lwN0dJJ8+8l73SNFoco5nIcLnXZHiLFXygxXe6WJbEV2QXjp9gvFhtvYt
ijx1RObW8qSnUzSPzYOIo/iYzpe1GgoHmKabF9vD8J3NbLTpt+px2ssIsn/s25fb
gALBuXbtEx9viPIgpQz3s6LafGO4oPUQr0Q2rTyFdK3ib3X44A36KCh790+Rsqhz
jgUWAm6LyXgW/QpjFel8QmnVgVmFJWEMttgDWvUtWlgMO+BgS958dDk1L/s9bQc+
xqsIav2kvdt9c8/3+xOhC/bp5aa0NYGcdYSsOAMVofbG34dntV3/HKUnvCRnZd9T
2n+s7P1kDnnJTOiVsw9ThF/dvU7zUj4SYvqtYUrwWfd+4xzzXIWISiauZBtx8HOH
/Wi2li1gLkY1caYRzuJJphFY2bgSeZJQw9sjStVh49yOT9DdT4rNZoTS1HXjLSws
YdLCYM7I8p3d6qMucqZhJ/usDH5pCSW/j92hHyl3P9M7fCUN2dVIg0OseVY9d8XF
UnGdwFpbIaXmBbb3blo47CE68U1MUTSegitkJLQPM0YWmK+5+NI+Yh9HynepbAaq
IVOzjoIMS2wshy4Yxg2zMTj4bWgJ2PhFGtqA4Ia7KP33Qj/iVl6JKEq6axhI7nZu
8ofvuE7W5JudWR8KKraR9ULU7AEtiU9mask7D/9Y6PgP5rMp6+2uYYxBsc1is9dW
XqdAVHEUSLroBRaqq3ywi/WsBOZR47J/k1xHeCPiGUot0tlHSKy84danVxFnSZm1
8QtD6UEDgq0tWNrOSPG6tu+2I/Ma8FGrs6gWZxyVKu3G1HgnZ8gg0NzA5vATa5Kv
stN3wCtzAU2NqrvP2T4mWeakXmDe61O696h101WfOazGC5NDjWDdTHQLdYdxPzr7
yDinIBNPwBX9NEmjxS1x/QtMfMzE4hp8AZwEjgnYDWxiG4yFPdfEVlKgy3TxC68l
VoGyrl3gbTSdXqj+gPHjeVpZviB11WZcEuMdjhKwILS5l4u/gZR1Akw5wPPc4g1O
71M+qy8wivBs107Yzvin3BqnVjO+ZZ0Wm0HOg/bLYo+7zbWdq/C2PTJdCbKRWa0I
hpZca59g7ANOc8ycEg7NVFsLwLeWwBwGRMkqQ8ciS6EOXY6VdkGbtZCC8r1SXdgh
rkvnyXftWOnv/RmQzOchr1wwo2+D9VEu6EhCYBlRTKXZp9FZIF/y4n8eJt4YxaPN
EoJhXjTMWaFJ4/BHSwgyQDa/LfTik5xZnk3zJb1XW8qQzCYvMkwjxil72kl60l9f
C38qY4FLQmyjl5vQ3lgACKffbJJ9ujNgMkbNZgOX3dEGr6p0CzMFxLOavvG4a9nu
ImM5rbOC6ZJdwLUTArkCDQRhEoRvARAArCO3OaYvwccaRumfHLqVyhEKNpeRG31Q
MrR2QF/gncdpPama8f4sVqY7EJYgT4/zgoTP3mTSNNETj1KzcA+ZhJhzv548JWwt
jokyFp5POXEq0PbTZ1Zg4/2Gn9QVxWa+dIstK6r2H+jz0oazB5sahf+BlAVH6+1n
9YFq3utQ/xvkZk+R3qxNdAIDcLKFVUM6Z56fJSnl6Sx2PmJAM2MqZ2oJtfFpa9T/
xv3Nsb0h4b/WvkM8vVpHqnSYdALlQMlho+lM/c/HiFyr4M8tGm3+SMW2TSP4zEe9
SEOcfvLHRTpWDebaoMJ9sUU4aLNWswpnQ+YsEcmFvUTtcH6DpHOX3MDL+ol+Uy6I
pc/ASp+7/pRgO0lqm27lzzNoBp0qdA2J2fgnET+z3HDx3MyliQsaCDf2e25pikLe
JbtAh362peGWz5GkzqEi0kkbRRftjWLRNSosFEBQPx72jcdh312O3zcBk2q/oiAv
tbzCUTWohVeL4lXxVMEeey/BLH+/KCyBR9TD/lPi1Hddd6Orrj5kjjWnUeqXPnSO
RfPwI/zdQM1hECHP1gHp+lLNR0d64vZDN+A3L8YbD6N4qic6fJUXe/VFU7zHOTkb
QitV6QkhifsJnYrOQbJ4pVVKgU6zvOy4vsSTLUqShvKkzHGbbtyR1zsLGS6nwrHD
NeWZfEBgKVsAEQEAAYkEcgQYAQgAJhYhBPiM/t7/KaW02VI4ZOJdmu0Fk7NKBQJh
EoRvAhsCBQkB4TOAAkAJEOJdmu0Fk7NKwXQgBBkBCAAdFiEEhYpWD5fJrrIuwccy
lh3d1SUNSkIFAmEShG8ACgkQlh3d1SUNSkKoURAAn96VKV6sP9fkMzmf1mdQIfx9
L++Yy+ZkGi3ZEGnnsPureu9EhaVmIuhhlCJHhgK3T4xqx8Pmn+xKLrnq2/V/xXqt
HwLsgv+aex+9PnIXITDmXbsoFblt4FDz+mNhiBqXueKc95J5jsdib38nH+qA7v7b
I5D5VrDYtgEc13KGOtRMeVF/iul/hMF8JJZUL/oQaTtUtk+5w5cmCyGucPj2Ivyd
el9SLHCZqSc4BHYrHZAUy2IWB9u1y15j82HezcJcxpg355PaG5EnYaDY1wo+ZqMx
ZvmZB2mUcDh9IKLTngbex0MmCoEr1qBcFrOvp5iZkGl0xmySGlWfAKKDLLL/hfEU
ahjiFyA4DEooCGR2sPWUgNrEnVANJEBfq1azbouroRfdiSYBv/lqJGJwahPo4NCu
+kbyERBqYWvAKegjuGy0+rvTicFfaDx824Kt10aDxt56Hqd6/AvQeC+XFSfijpUr
voPO8pPlwyUEzkxD9h0WbKWTDe3tdP9dILr3jTcBLvJLsUPQ5mrsU7ccB5OtpdOt
NhIWzjr9jqBvRYm5xoOFh0ox5R0909IIRhwNbQqLDIi/xknK4LBwH1VDnWzc6LtZ
LHjG0+9mQ5rqXnDotxbsYgJzqab4/lMsiwD7RynzGY4r6bBinOGU6FEST6I2f/TU
TyRYTcyieT0mwBVJaJBK4Q/9EkVthCy8DLt6D3ZGTRED1Kw8j8+4X2ColntFjHzf
x1pk8GOAcdOlEQFAzmaexQPfSKZtSXl5BxXkCjFJsXt37BQSgVuYcP5wZgyItlCk
anDKWUN69AYFJEsaGPwENaYvnqsnisWqdYLoxkC1GsTaaVSsDi+eDPyGqmCmUnBh
FDzA673kf/mUj+FHRsioncJFwln23Ml4UgGGorpz1DeSHqD0Qp4xwYMNTf8sBHmq
BtJdFr4en0ajT9QlxADm4uReJMZeQ2LNtDj52UGWO1tcqSQFLhNmPzpMxJ1tjRcl
McNTzxH9afCj6kd+1Lo3kvnqylUk9S3Hrguj9kp6cMYliVEMmmRs6pQdpcUnCtjx
SJi/nIzHqZihlAzBn50X+Euare91mKbrmgFc/mvBfbIwILD7ZB+AKAZDLhLSmjlO
4FSPe6TINjbpNC4aj/sEvShdL2UABOWKP9qG/XIxQCWY9zrvq/AjSlwjrT9ybon9
Up4P4Y0iST50ruicfF5C63NjZAg0cHtk8wf8uwoqedH0yiHJpWaSDKIH146r8USn
yr23wLqJv4jzqZyw5/qSpp6pYQ5LMenZLL5AcXwMFHo9w3csh/LCjHxESdS7Jlh6
SXrvlKGv1V62GtLZE2SqveYjZN1Av8Pa4S1OYfqN262rDUi0vIYvvVYTeuAW8W74
1b25Ag0EYvTakgEQAJW0+3yvZLYH3v7iT/1FMX0zxDaWKZOBC0H3JsMxKtrM7WA5
0cnyMRqUoqBdH3ktgUBphFvyY4dmAHuwAjRwe160s77fXR2Y3XcWC5NRkeNUgIp9
ghcN5dakkOuogxUCueQKDnB0zeSltvNkVcnRKWYbRhsy7NoEu4r7iQ2KtLCWhlRF
A84kgmYfRRRCH5ngL/eKbE9cp/v1y5N4xYosJqx6RhajfsWHstH4g38CflSB/dHh
9tDPvQ/QygCuS7ENS59JDmy2pTuL5bfdTGj8mYhV3O+bVgwMXDz5bDGAqnNIzgMp
WmAxiRUnYVBWFgoHfdiZFQ3YjgTCC86CG/8keszlyqsOQhpe3qOL4Syq3mtsEkKv
EJ8/jglN5tlGro79/tm6HGNBomGB8lqo80DDycW4LMGCenS/24we8KGOX946rwPF
j7y5FHFHouyCREqIEX+WUU2RHioMLENxbdF6QYo3yz9b3U+UMyflhgOP5KAlJI4U
enP1r6eagEyYO4I12sjlJYcINeP2k5NXwZCT8LIGblRXnWXDJF5coFd+pAl0c2o9
lEh8WZv/wvQ44dfz0dyY3aZgYm0lro5xjtnNW/V/sJLcLSC8TIj7smHRJC07pxVK
+2u1x7sl2VzpNuGNnsqmNHj9oyQyBkwj8/Ne7PmFYkovV715PjAADtBG+OflABEB
AAGJBHIEGAEIACYWIQT4jP7e/ymltNlSOGTiXZrtBZOzSgUCYvTakgIbAgUJAeEz
gAJACRDiXZrtBZOzSsF0IAQZAQgAHRYhBI1tp4U8/hse00btDe299BEmfslUBQJi
9NqSAAoJEO299BEmfslUF4IP/0mOsYR+W+BNBB1tUjYGHyA2NOblXu6zmVNCCDFc
kayM+8NH6AbYpLO3TiM55JmeukRCM3se2Zvf/wr2Ks5ywDAXvdYxw38ueUJmnKSx
yz/2yk4CJiYC6mnjvU4Gs7o+4yQQ4wPVSD6IVt1kVccuZEO0c9qTIbOhhIxHjXv6
1pKY/kLElBHntLPoFZxwDSmtCTpnde8gmOUlg/tI2Ku8w+Sv/c0cGVWwJA/WmRMV
tEvkBhtwgq/OrUkiU59PdUXD7Uuy7Btgh2LuOYaSQR5a4H4/Q6OZzEGrzqWoC946
x55LtMolg/fhvMTo8siStREfd98KrBEDrryq3Zmv1j88sBoqUjyIF3a779Ktw8vs
Vu9nz+x8Woy+OewBhYtoCbx7FlCtsbSjQkkgZ4t0X4pLH+G1uL28xsoXD8B1Grgc
HXaBvS2pCpSAb7Zx6wSVkQKTm0/GEZSv43C427bywWeHLynoOUYSsY1BLDPwGbOU
bDGB2tzuXysebAaWrmbYfC34ITBEzod/L5Pwh+AvJrOYjvOL81zMKk6Ldt57AjCB
FZOrhqo4UMeFJeEbIywmGRlHg3EYqlrj8uuOu0PIFfDEHzFzdSyPIjNQGbFGmTuk
ksynNf5VbV3j7pEi04qJrA0KwQQY3WDUypu0AllP7WldbxoJYye1KAQOnH/sXfN3
vGseJ6kP/A1FDR5A/snA51kUalfZ6MbNxSC4RLRhKM0L8ICYl50X3DyJBS5ScakR
JTkiaPv6l5RlpUs+R8L0FZ20gNSZIn70D3jFzh29lEGnbf+P2UKQvmr9TUBcZBNA
Nfj2EXdmZAzQu8QEPk7/8PONeszftNYxSjk7UtO+Z9QQzTnipksIQDvIGBuX27a0
i4a0NgHko0HsxtsfAruAWEXVlWyNtMcNvdozbHkPqr4kvw76we3MIPTSBuZ8DUuf
upatEcblh2VyRIWbzFmvuq7GnAmfynyU9NU+2kjmW6peYX5/c72LKWghsnPCx8xF
k15blEo/kSMKN5vr+ZyiFas7IDJd2xmx1pd2xYvoNBl72ClflvsdMEnqx6Tpdh9B
uvyCrat1qt4F8aKqao8sXbopH7QvDBpqGqgMGLkoPheOXypBvnvoYKL7tOoF4XJL
AFM9PKGECoegwC0Mla15amgkfViUWdCsDy8UsSlPfBdvHdJrhChuPDwZV9GztZjj
NdYVRi1OaxZP24IN7o40VFxvMh12E3HaideLi5MzZxxkXhr8m485b2hgvkuNUjoD
nvFn8rZe8axx9FFhpg7/JvCAik3IxRbusM3WDqmFuBGK33phfD5wAKIWrBwT3iMU
4GnMNmKOMrYCE/edg4eOPFj+wjWw8ZGD8XrnHVI0k8fGOoLvAm/xuQINBGQHFqQB
EACucSUehSi8KixdOc9pYVWBCoqu5V2NlrjbpVVpmPB118fLPaZV4MSB/AnHssWw
XDeO9zWyyLYstN78D/dWcX8Al74JFtBAM0lfgnqE5na8JZYrEivdsjQUO3Cf250G
yXJwpK+CXpAtH6qVrO595exknHKKTv2dfV51UxDXXzYhLznnYHZoTnzpMKUSwqwP
ywdwDVkalpXfFxP43w+gSuX7uOAI/hhX/iRE0drVDy85422FZnncNdigO6JjARn7
CAoYDcb4K1+zn9WcwzWqV4+yhYDt+yf+o+TLhyF9BarG8cQ1tE4RfaDMZuXp0iKL
itX01mFb0sQ2ZF0YBhQdGaBj/AcfE4e7Sacz9gC93Xd3FaVt0zgsTxMt3Z0dMzAw
9lf7i/aPFFJQLoAZtuYU4hb3S4CG0+l3WPTdW5U276bV5WrTyvibfpNs8mctH4lB
I4jhSkqoPwZ+8gts3XT336P3F2Z/i3cbLmfjbSeAUYRV5BdkozbuWfO6JrZq/BId
KEUMlVi99CJD1fREyMXnr3aROdw7jKhtW5x59Act/ZXB9jixJ5EdxMe5aLeYKNSm
L8I4TXG4DEvbPu/HCHNMlDRoga1CCmVaUEhuJwQaH4PhhlX9M69Bmz42NS8A0Fol
JkiCsCQTQjyzvgXb1Pa0WKUVjPkQIGEUAaQdAGcns9svJQARAQABiQRyBBgBCAAm
FiEE+Iz+3v8ppbTZUjhk4l2a7QWTs0oFAmQHFqQCGwIFCQPCZwACQAkQ4l2a7QWT
s0rBdCAEGQEIAB0WIQTpQm2LZ+Nd9Ha9BIGF98iGiDficQUCZAcWpAAKCRCF98iG
iDficV5MEAClR4UiibpFIYRsbdtPQC/RUIRPbx8naJ8o9h3RqnQKQPgIPkJUS8d9
vVHQlQ8rhzrzWctOMWHgDRDEojLjXwyYSHRBawJN39D/Fs+D6Nrg9gFkdBmrU2My
+Xia2Wgb+R2qUTnl8sP+d8k8zUC8UoZIX2ksK5yzw3Zwozg6X5Bd70zIru1RJtQd
9ZFDb/PVobWGbqS+saGEDi0Wa7YrmRRA+kQtvMIywX5LFJ5/bSqH3BsJduwmCnJH
84WcxYW6Ntbta7MsnmrDEwfKwmu6d0XgL0mUaOGlt7UoECckZLU/VWh+V9hhSjPi
Dp1IX3ucfmWfsEokN1ePMnl1LWbew7yF5WsNl0/BLVczx99uoYZ6FeW3cy+8PT3q
5Tuc7kjV9oQddJcS+slmlpyuXGH+vXa8WvSDWxPHat1tPhh2QEMGbVFeCw9XhwLu
98YC+Hc2BImD9FfL46GMXPmiBJ5S9qqJjb2lGB+Y4lnbus8DavpudumgO2b3p4CH
eWQYCZY993gcZIiI1/9YMXtXABZ034XoennSq1gzoAxmWGoEk9E/ZNcDLhigW2UN
D8w/mfBKD729NhGSBlL8LmAxwHe61fnL2Z+yTjVvWfsgMXSsn1U0QYkjgE6rzqDY
1w29Iduo1QLvcXQj+fVvu0O5zYPeRYV+RHG+l65KmB8Tjomq6FW2tsInD/92KSGF
0TIk0rOjJA8Zy7Eers21QsTScUrfI3hntzcPpMZzWRBWuyXqf/4350lRTki3hMSx
YB/eJlwehTmUAkC9E3oUE36PJqpp2mzC2cP68CIOdUtkdOVqzkfeZ54LlaJxgo5y
BuC9AqUH5OfVNjZps3yygYv2ahIPBMR8JNduUiTAuvXbIENVy58q6/rZjHcKRp8b
MUX6uWJrIXO5aSAIEljx9DbQoxSbmNJPiriuSKHbhrNPpI4xRlO9gTbaEC0ELKGC
qw0lA1it1XvbZtP4CHcfJ0hyGvy9yvDH2poMgjkhu7OZdN1qBsBRHIIED/Ijy+tz
nq7rQvmaDqZavlQbYREHdrjB/sS10Sblfu9h+vIwSx05UwSNGWNiDrvkQDPbVnTh
R32zsNAlq+f0CEmsgbYPrE/lFwfFS49F2Kmma92qcDiK76Audz/dqz6xPvYQCqra
a6Sa/uYr9aiaLsZTJ7nQ904KUE+Zwk7gcO32Bl7UO3NvkWlvSqOWGS/75WUgbrD6
RARo6Xv6c8/OxgizzkboGBrdqqpmbG9PGi+gMrxShYtmZYcpD+dB91oKMC5q2lu6
IGrEVlky2zd7KvrIE3YMETdYL0Eec/H0Jwuxnp9sr7GkBSUns0IczEK/En/NLcBm
TkvXzMghTKTbYL9TjbK/CLzOR+5XXCHxXgDGLg==
=VZfW
-----END PGP PUBLIC KEY BLOCK-----
"

DEVICE=
CLOUDINIT=
IMAGE_FILE=
KEYFILE=
VERSION_SUMMARY='Flatcar Container Linux'
CREATE_UEFI=

WGET_ARGS="--tries 10 --timeout=20 --retry-connrefused"

while getopts "V:B:C:DI:d:o:c:e:i:t:b:k:f:nusyvh" OPTION
do
    case $OPTION in
        V) VERSION_ID="$OPTARG"; VERSION_SPECIFIED=1 ;;
        B) BOARD="$OPTARG" ;;
        C) CHANNEL_ID="$OPTARG"; CHANNEL_SPECIFIED=1 ;;
        D) DOWNLOAD_ONLY='true';;
        I) INCLUDE_MAJOR="-I $OPTARG" ;;
        d) DEVICE="$OPTARG" ;;
        o) OEM_ID="$OPTARG" ;;
        c) CLOUDINIT="$OPTARG" ;;
        e) EXCLUDE_MAJOR="-e $OPTARG" ;;
        i) IGNITION="$OPTARG" ;;
        t) ;; # compatibility option; previously set TMPDIR
        b) BASE_URL="${OPTARG%/}" ;;
        k) KEYFILE="$OPTARG" ;;
        f) IMAGE_FILE="$OPTARG" ;;
        n) COPY_NET=1;;
        u) CREATE_UEFI=1;;
        s) INSTALL_TO_SMALLEST=1 ;;
        y) DRY_RUN=1 ;;
        v) set -x ;;
        h) echo "$USAGE"; exit;;
        *) exit 1;;
    esac
done

function print_settings() {
    echo "\
Settings:
    VERSION:  ${VERSION_ID}
    BOARD:    ${BOARD}
    CHANNEL:  ${CHANNEL_ID}
    OEM:      ${OEM_ID:-(none)}
    CLOUD:    ${CLOUDINIT:-(none)}
    IGNITION: ${IGNITION:-(none)}
    BASEURL:  ${BASE_URL:-(none)}
    KEYFILE:  ${KEYFILE:-(none)}
    IMAGE:    ${IMAGE_FILE:-(none)}"
}

# Run Device checks, ignore if the download only flag is present

if [[ -z "${DOWNLOAD_ONLY}" ]]; then
    # Device is required, must not be a partition, must be writable
    if [[ -z "${DEVICE}" ]] && [[ -z "${INSTALL_TO_SMALLEST}" ]]; then
        echo "$0: No target block device provided, either -d or -s is required. Or use -D to download image." >&2
        echo "$USAGE" >&2
        exit 1
    fi

    if [[ -n "${INSTALL_TO_SMALLEST}" ]]; then
        DEVICE="$(find_smallest_unused_disk)"
        if [[ -z "${DEVICE}" ]]; then
            echo "$0: Could not find smallest disk to install (min. 10GB)." >&2
            exit 1
        fi
    fi

    if ! [[ $(lsblk -n -d -o TYPE "${DEVICE}") =~ ^(disk|mpath|loop|lvm)$ ]]; then
        echo "$0: Target block device (${DEVICE}) is not a full disk." >&2
        exit 1
    fi

    if [[ ! -w "${DEVICE}" ]]; then
        echo "$0: Target block device (${DEVICE}) is not writable (are you root?)" >&2
        exit 1
    fi

    if [[ -n "${CLOUDINIT}" ]]; then
        if [[ ! -f "${CLOUDINIT}" ]]; then
            echo "$0: Cloud config file (${CLOUDINIT}) does not exist." >&2
            exit 1
        fi

        if type -P coreos-cloudinit >/dev/null; then
            if ! coreos-cloudinit -from-file="${CLOUDINIT}" -validate; then
                echo "$0: Cloud config file (${CLOUDINIT}) is not valid." >&2
                exit 1
            fi
        else
            echo "$0: coreos-cloudinit not found. Could not validate config. Continuing..." >&2
        fi
    fi

    if [[ -n "${IGNITION}" ]]; then
        if [[ ! -f "${IGNITION}" ]]; then
            echo "$0: Ignition config file (${IGNITION}) does not exist." >&2
            exit 1
        fi
    fi
fi

if [[ -n "${DRY_RUN}" ]]; then
    print_settings
    exit 0
fi

function is_modified() [[ -e "${WORKDIR}/disk_modified" ]]

_disk_status=
function wait_for_disk() {
    [ -n "${_disk_status}" ] ||
    read -rt 7200 _disk_status <> "${WORKDIR}/disk_modified"
}

function write_to_disk() {
    mkfifo -m 0600 "${WORKDIR}/disk_modified"
    trap '(exec 2>/dev/null ; echo done > "${WORKDIR}/disk_modified") &' RETURN

    # We are at the point of no return, so wipe disk labels missed below.
    # In particular, ZFS writes labels in the last half-MiB of the disk.
    dd conv=nocreat count=1024 if=/dev/zero of="${DEVICE}" \
        seek=$(($(blockdev --getsz "${DEVICE}") - 1024)) status=none

    dd bs=1M conv=nocreat of="${DEVICE}" status=none

    # inform the OS of partition table changes
    udevadm settle
    local try
    for try in 0 1 2 4; do
        sleep "$try"  # Give the device a bit more time on each attempt.
        blockdev --rereadpt "${DEVICE}" && unset try && break ||
        echo "Failed to reread partitions on ${DEVICE}" >&2
    done
    [ -z "$try" ] || exit 1
    udevadm settle
}

function install_from_file() {
    if ! [ -r "${IMAGE_FILE}" ]; then
        echo "$0: Could not read image file: ${IMAGE_FILE}" >&2
        exit 1
    fi

    echo "Writing ${IMAGE_FILE}..."
    if [[ "${IMAGE_FILE}" =~ \.bz2$ ]]; then
        ${BZIP_UTIL} -cd "${IMAGE_FILE}" | write_to_disk
    else
        write_to_disk < "${IMAGE_FILE}"
    fi

    VERSION_SUMMARY+=" (from ${IMAGE_FILE})"
}

function prep_url(){
    IMAGE_NAME="flatcar_production_image.bin.bz2"
    if [[ -n "${OEM_ID}" ]]; then
        IMAGE_NAME="flatcar_production_${OEM_ID}_image.bin.bz2"
    fi

    if [[ -n "${CHANNEL_SPECIFIED-}" && -z "${VERSION_SPECIFIED-}" ]]; then
        VERSION_ID=current
    fi

    # for compatibility with old versions that didn't support channels
    if [[ "${VERSION_ID}" =~ ^(alpha|beta|stable|edge)$ ]]; then
        CHANNEL_ID="${VERSION_ID}"
        VERSION_ID="current"
    fi

    if [[ -z "${BASE_URL}" ]]; then
        BASE_URL="https://${CHANNEL_ID}.release.flatcar-linux.net/${BOARD}"
    fi

    # if the version is "current", resolve the actual version number
    if [[ "${VERSION_ID}" == "current" ]]; then
        local VERSIONTXT_URL="${BASE_URL}/${VERSION_ID}/version.txt"
        VERSION_ID=$(wget ${WGET_ARGS} -qO- "${VERSIONTXT_URL}" | sed -n 's/^FLATCAR_VERSION=//p')
        if [[ -z "${VERSION_ID}" ]]; then
            echo "$0: version.txt unavailable: ${VERSIONTXT_URL}" >&2
            exit 1
        fi
        echo "Current version of Flatcar Container Linux ${CHANNEL_ID} is ${VERSION_ID}"
    fi

    IMAGE_URL="${BASE_URL}/${VERSION_ID}/${IMAGE_NAME}"
    SIG_NAME="${IMAGE_NAME}.sig"
    SIG_URL="${BASE_URL}/${VERSION_ID}/${SIG_NAME}"
    if ! wget ${WGET_ARGS} --spider --quiet "${IMAGE_URL}"; then
        echo "$0: Image URL unavailable: $IMAGE_URL" >&2
        exit 1
    fi

    if ! wget ${WGET_ARGS} --spider --quiet "${SIG_URL}"; then
        echo "$0: Image signature unavailable: $SIG_URL" >&2
        exit 1
    fi

    # Setup GnuPG for verifying the image signature
    export GNUPGHOME="${WORKDIR}/gnupg"
    mkdir -p "${GNUPGHOME}"
    if [ -n "${KEYFILE}" ]; then
        gpg --batch --quiet --import < "${KEYFILE}"
    else
        gpg --batch --quiet --import <<< "${GPG_KEY}"
    fi

    echo "Downloading the signature for ${IMAGE_URL}..."
    wget ${WGET_ARGS} --no-verbose -O "${WORKDIR}/${SIG_NAME}" "${SIG_URL}"
   
    VERSION_SUMMARY+=" ${CHANNEL_ID} ${VERSION_ID}${OEM_ID:+ (${OEM_ID})}"
}

function download_from_url(){
    prep_url
    echo "Downloading, writing and verifying ${IMAGE_NAME}..."
    if ! wget ${WGET_ARGS} --no-verbose -O "${PWD}/${IMAGE_NAME}" "${IMAGE_URL}"; then
        echo "Could not download ${IMAGE_NAME}" >&2
        exit 1
    fi

    if ! gpg --batch --trusted-key "${GPG_LONG_ID}" --verify "${WORKDIR}/${SIG_NAME}" "${PWD}/${IMAGE_NAME}"; then
        echo "Could not verify ${IMAGE_NAME}." >&2
        exit 1
    fi
}

function install_from_url() {
    prep_url
    echo "Downloading, writing and verifying ${IMAGE_NAME}..."
    if ! wget ${WGET_ARGS} --no-verbose -O - "${IMAGE_URL}" \
        | tee >(${BZIP_UTIL} -cd >&3) \
        | gpg --batch --trusted-key "${GPG_LONG_ID}" \
            --verify "${WORKDIR}/${SIG_NAME}" -
    then
        local EEND=( "${PIPESTATUS[@]}" )
        [ ${EEND[0]} -ne 0 ] && echo "${EEND[0]}: Download of ${IMAGE_NAME} did not complete" >&2
        [ ${EEND[1]} -ne 0 ] && echo "${EEND[1]}: Cannot expand ${IMAGE_NAME} to ${DEVICE}" >&2
        [ ${EEND[2]} -ne 0 ] && echo "${EEND[2]}: GPG signature verification failed for ${IMAGE_NAME}" >&2
        exit 1
    fi 3> >(write_to_disk)
}

function write_cloudinit() if [[ -n "${CLOUDINIT}${COPY_NET}" ]]; then
    # The ROOT partition should be #9 but make no assumptions here!
    # Also don't mount by label directly in case other devices conflict.
    local ROOT_DEV=$(blkid -t "LABEL=ROOT" -o device "${DEVICE}"*)

    mkdir -p "${WORKDIR}/rootfs"
    case $(blkid -t "LABEL=ROOT" -o value -s TYPE "${ROOT_DEV}") in
      "btrfs") mount -t btrfs -o subvol=root "${ROOT_DEV}" "${WORKDIR}/rootfs" ;;
      *)       mount "${ROOT_DEV}" "${WORKDIR}/rootfs" ;;
    esac
    trap 'umount "${WORKDIR}/rootfs"' RETURN

    if [[ -n "${CLOUDINIT}" ]]; then
      echo "Installing cloud-config..."
      mkdir -p "${WORKDIR}/rootfs/var/lib/flatcar-install"
      cp "${CLOUDINIT}" "${WORKDIR}/rootfs/var/lib/flatcar-install/user_data"
    fi

    if [[ -n "${COPY_NET}" ]]; then
      echo "Copying network units to root partition."
      # Copy the entire directory, do not overwrite anything that might exist there, keep permissions, and copy the resolve.conf link as a file.
      cp --recursive --no-clobber --preserve --dereference /run/systemd/network/* "${WORKDIR}/rootfs/etc/systemd/network"
    fi
fi

function write_ignition() if [[ -n "${IGNITION}" ]]; then
    # The OEM partition should be #6 but make no assumptions here!
    # Also don't mount by label directly in case other devices conflict.
    local OEM_DEV=$(blkid -t "LABEL=OEM" -o device "${DEVICE}"*)

    mkdir -p "${WORKDIR}/oemfs"
    mount "${OEM_DEV}" "${WORKDIR}/oemfs" || { btrfstune -f -u "${OEM_DEV}" ; mount "${OEM_DEV}" "${WORKDIR}/oemfs" ; }
    trap 'umount "${WORKDIR}/oemfs"' RETURN

    echo "Installing Ignition config ${IGNITION}..."
    cp "${IGNITION}" "${WORKDIR}/oemfs/config.ign"
fi

function create_uefi() {
    ensure_tool "efibootmgr"
    local EFI_APP="bootx64.efi"
    if [[ "${BOARD}" = "arm64-usr" ]]; then
        EFI_APP="bootaa64.efi"
    fi
    efibootmgr -c -d "${DEVICE}" -l "\\efi\\boot\\${EFI_APP}" -L "Flatcar Container Linux ${CHANNEL_ID}"
}

WORKDIR=$(mktemp --tmpdir -d flatcar-install.XXXXXXXXXX)
trap 'error_output ; is_modified && wipefs --all --backup "${DEVICE}" ; rm -rf "${WORKDIR}"' EXIT

if [[ "${DOWNLOAD_ONLY}" = 'true' ]]; then
    download_from_url
    echo "Success! ${VERSION_SUMMARY} has been downloaded to the current directory"
else
    if [ -n "${IMAGE_FILE}" ]; then
        install_from_file
    else
        install_from_url
    fi
    wait_for_disk
    write_cloudinit
    write_ignition
    if [[ -n "${CREATE_UEFI}" ]]; then
        create_uefi
    fi
    echo "Success! ${VERSION_SUMMARY} is installed on ${DEVICE}"
fi

rm -rf "${WORKDIR}"
trap - EXIT 
