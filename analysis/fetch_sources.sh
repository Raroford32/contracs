#!/bin/bash
# Batch fetch contract source code from Etherscan V2
API_KEY="5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
OUT_DIR="/home/user/contracs/analysis/sources"

# All addresses from the investigation list
ADDRESSES=(
"0x2375fc81443fc333ae99574ce77da10ce4baed22"
"0x4bb4c3cdc7562f08e9910a0c7d8bb7e108861eb4"
"0x6feb5478f7345abe1d477ff6828819b4c8ba551a"
"0xc82abe4dfa94b9b5453d31274fb7500459a0d12d"
"0xed4e21bd620f3c1fd1853b1c52a9d023c33d83d4"
"0x2a1dca74419c2d304a3d359f428ee1a4e9324a90"
"0xf042c68695c5449f0483f36ec4959adf40ce6ace"
"0xf4d73326c13a4fc5fd7a064217e12780e9bd62c3"
"0x11ae2796e528c3dbb3bd88f37b25aead0cc6e979"
"0xa24f40364aaafaa75cd5fa2b40d4c0a1c9bf6606"
"0x3b65a20f75f97cc7a3664cb2def6d6bd843c123b"
"0x21d6d6d6ffd8b68e94bf5159bb029635af540ae8"
"0xaf5fc45258b5d0af72031ab154bf6dfcfec74b99"
"0xdd83208dd1da48ad1fd1bd3037f962d9a914f398"
"0x03fb20ecfdf599c1a4d44241c8bb1f11f47c2599"
"0xe03aed8dfa6200292a2585918f656e2345ea283f"
"0x0ce62a94dbc2335b227496b61e853880c5dbcd67"
"0x62f2819d505249e63b1daf31b44f152247feb5d5"
"0x2fc945d48a4d61ec988f8cabffbe6f1efe07137f"
"0x8239a6b877804206c7799028232a7188da487cec"
"0xedd0a518d4a84ea6f747856933c4d32df9f664f8"
"0xc781c0cc527cb8c351be3a64c690216c535c6f36"
"0xe43d56ec4a331353849aafd2b5367f77b2a493c9"
"0x480e6993da410d5026d7bd3652f53d99845b6fc3"
"0x585aba689bf7293fe66e9fded9eec9d0e732b180"
"0xb92998ccd53135bf9f26cbb67590b070d287bed9"
"0x02b15c47b4b516a22fd2d8b1fc662afb808a2169"
"0x148167f173cec5fce6e2e303df314efd65b8e441"
"0x27ce6a70b572302cd5466591313a0029b38d7bb0"
"0x1ea9bcd9c7483c9570057921459f4a64aff39b0d"
"0x9e951dd846e748e6fcb58bfb76953c4900f819f4"
"0x889dfe07caa0baf3814ddcd1b933d208d9913b5e"
"0x2f40aeb1a1aa6dd10a8af0926f416d01ffd9777c"
"0x6f1e92fb8a685aaa0710bad194d7b1aa839f7f8a"
"0x2224c28c82874e6537c356adc382918d3b2316c4"
"0x6b59d35a5207bd7c9986a9e1cf9625ca4beb039a"
"0xab190577053458c53317ca95369aaca4673dd86e"
"0x16205e58126580383e5e0461720e336ae77c670e"
"0x6bc726c993103197c41d787dd72ecd4d2e1614e8"
"0x9b5d9e2c2e1e96986603be922bc44304d6aca898"
"0x7e32f4c44e22ab20df287f8a15eb6c0f54da6e30"
"0x82c623270fb3c4e95a36d35e21a95ff328531dc5"
"0x0eb81f6d3c54167ca849a91fff83c926b77368dc"
"0x0e3efd5be54cc0f4c64e0d186b0af4b7f2a0e95f"
"0x66f6d5b5b3c466fbbcb159bb834a3e3249537561"
"0xf6139171a90f72dd298e24af7adcbb0d78175427"
"0x2a65b2cbfbc558f235b51159656efd3518be3ba5"
"0xd7419a0c753378a86c3342ae0c1a4577b9baec83"
"0xefd94041fa3c6b1802d48057cd6a9b0ee4276a89"
"0xb1f0cc7a1bfe763534a67f77562fde688a35fb30"
"0xb7edb5d79c1cde621f0ad0bdd01cfe85e017d60f"
"0x7be03b36bb6eaaed3223f50c7b6ac215673d27f6"
"0x642135ff98c15cba7fcf1766502bd493be4d3492"
"0xf05df39f745a240fb133cc4a11e42467fab10f1f"
"0xb531445401926029b1647669cfac8b4e5d8c7777"
"0xd288755556c235afffb6316702719c32bd8706e8"
"0xe4b91faf8810f8895772e7ca065d4cb889120f94"
"0x14219845c6b7984aa5ec0a39754dcc327169de32"
"0x1e7866b5a5a4f09efd235d28d49568c2fe2f7ecd"
"0xc4543073bfaba77781b46dfb4d43b5ae4e30eb28"
"0x491e3a7cda79af2bba5de48c58445644821d14de"
"0x09dfdf392a56e4316e97a13e20b09c415fcd3d7b"
"0xe03e12f83aba2e6b955f96b5acf64082bb8ac162"
"0xd948ba1b50c474199db204ef128ba413c49fd9b8"
"0x079b3a3ed7c164df63d72355c7dd048ee5e53fe2"
"0x156269966404ca72f6721c3228676c56412c058c"
"0x08071901a5c4d2950888ce2b299bbd0e3087d101"
"0xb03ca9354241688264d7f4547857190b75e26944"
"0x8dfdc61c7c7551d0deec950a2822eb59cddb8f59"
"0x212b5a4ae093a57fecc91477faa8ed1c0a4d7ca8"
"0x128aedc7f41ffb82131215e1722d8366faad0cd4"
"0xfc5807081f91dbbe008aebd1525b0029242b4663"
"0x5daa068b9592781ad49235838fdd38e2d162084b"
"0xcdee8792f28e5c0713dc12c2bab8905ce24d44c1"
"0xe04bb5b4de60fa2fba69a93ade13a8b3b569d5b4"
"0x994d1edf24afe8bb283cc5ab6be90141c395f3fb"
"0x01a360392c74b5b8bf4973f438ff3983507a06a2"
"0x24719d3af60e1b622a29317d29e5ce283617deec"
"0x8aed0055d691e6d619acc96ad0fb3461f5774646"
"0x67bd2425823614a8d0a90c467cf36c34db30edab"
"0x05fc48447e0ac445042823dd36e3e4ed2ffdf6cb"
"0x21320683556bb718c8909080489f598120c554d9"
"0x58749c46ffe97e4d79508a2c781c440f4756f064"
"0xc7315f4faab2f700fc6b4704bb801c46ff6327ac"
"0x446b86a33e2a438f569b15855189e3da28d027ba"
"0x3bf1bd5db4457d22a85d45791b6291b98d0fc5b5"
"0x28ca9caae31602d0312ebf6466c9dd57fca5da93"
"0x6078232c54d956c901620fa4590e0f7e37c2b82f"
"0xaf3bfb50469aecda211db3333b8c0da263b0cce4"
"0x5fc0af6197b250619535ca20e25f18c0baa462ab"
"0x717d0bf97ce58e14945f5e0320ee98381aeaddaf"
)

for addr in "${ADDRESSES[@]}"; do
    outfile="$OUT_DIR/${addr}.json"
    if [ -f "$outfile" ]; then
        continue
    fi
    # Try chain 1 first (Ethereum mainnet)
    curl -s "https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address=${addr}&apikey=${API_KEY}" -o "$outfile"

    # Check if source is available
    status=$(python3 -c "import json; d=json.load(open('$outfile')); print(d.get('result',[{}])[0].get('SourceCode','')[:5])" 2>/dev/null)
    if [ -z "$status" ] || [ "$status" = "" ]; then
        # Try other chains
        for chainid in 56 137 42161 10 8453; do
            curl -s "https://api.etherscan.io/v2/api?chainid=${chainid}&module=contract&action=getsourcecode&address=${addr}&apikey=${API_KEY}" -o "$outfile"
            status=$(python3 -c "import json; d=json.load(open('$outfile')); print(d.get('result',[{}])[0].get('SourceCode','')[:5])" 2>/dev/null)
            if [ -n "$status" ] && [ "$status" != "" ]; then
                echo "$addr found on chain $chainid"
                break
            fi
            sleep 0.25
        done
    else
        echo "$addr found on chain 1"
    fi
    sleep 0.25
done
echo "DONE"
