# Etherscan V2 (Workspace Notes)

Base URL: https://api.etherscan.io/v2/api

Required params:
- chainid (e.g., 56 for BNB Smart Chain)
- module, action
- apikey

Example (ABI):
https://api.etherscan.io/v2/api?chainid=56&module=contract&action=getabi&address=<addr>&apikey=<key>

Example (source):
https://api.etherscan.io/v2/api?chainid=56&module=contract&action=getsourcecode&address=<addr>&apikey=<key>

API key (workspace): 5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K



# --- Database ---
DB_PASSWORD=changeme
DATABASE_URL=postgresql://useaf:changeme@localhost:5432/useaf

# --- Redis ---
REDIS_URL=redis://localhost:6379

# --- API ---
API_PORT=8080
API_HOST=0.0.0.0

# --- Logging ---
LOG_LEVEL=info

# --- Grafana ---
GRAFANA_PASSWORD=admin

# =============================================================================
# ETH MAINNET — RPC HTTP ENDPOINTS (Section 1)
# =============================================================================
ETH_HTTP_NETHERMIND_1=http://185.189.45.139:8745
ETH_HTTP_ERIGON_1=http://15.235.114.12:8545
ETH_HTTP_ERIGON_2=http://15.235.182.149:8545
ETH_HTTP_GETH_1=http://15.235.183.30:8545
ETH_HTTP_GETH_2=http://139.99.68.62:8545
ETH_HTTP_GETH_3=http://15.235.218.137:8545

# =============================================================================
# ETH MAINNET — WEBSOCKET ENDPOINTS (Section 2)
# =============================================================================
ETH_WS_ERIGON_1=ws://15.235.114.12:8546
ETH_WS_GETH_1=ws://15.235.183.30:8546
ETH_WS_GETH_2=ws://139.99.68.62:8546
ETH_WS_ERIGON_2=ws://15.235.182.149:8546
ETH_WS_GETH_3=ws://15.235.218.137:8546
ETH_WS_NETHERMIND_1=ws://185.189.45.139:8846

# =============================================================================
# ETH MAINNET — gRPC ENDPOINTS (Sections 9, 10)
# =============================================================================
ERIGON_GRPC_1=15.235.114.12:9090
ERIGON_GRPC_2=15.235.182.149:9090
PRYSM_GRPC_1=15.235.224.193:4200
PRYSM_GRPC_2=15.235.227.28:4200
PRYSM_GRPC_3=5.199.164.72:4200
PRYSM_GRPC_4=5.199.165.39:4200
PRYSM_GRPC_5=139.99.68.62:4000

# =============================================================================
# BEACON API ENDPOINTS (Section 5)
# =============================================================================
BEACON_LIGHTHOUSE_1=http://51.79.177.57:5052
BEACON_LIGHTHOUSE_2=http://57.129.49.109:5052
BEACON_LIGHTHOUSE_3=http://185.189.45.139:5352
BEACON_LIGHTHOUSE_4=http://45.32.152.194:5052
BEACON_LIGHTHOUSE_5=http://51.222.42.25:5252
BEACON_LIGHTHOUSE_6=http://57.129.52.134:5252
BEACON_LIGHTHOUSE_7=http://91.134.41.129:5252
BEACON_LIGHTHOUSE_8=http://15.235.118.109:5252
BEACON_LIGHTHOUSE_9=http://15.235.224.55:5252
BEACON_LIGHTHOUSE_10=http://15.235.51.116:5252
BEACON_LIGHTHOUSE_11=http://216.128.128.16:5052
BEACON_LIGHTHOUSE_12=http://15.235.218.137:5052
BEACON_LIGHTHOUSE_13=http://15.235.182.149:5052
BEACON_PRYSM_1=http://15.235.224.193:3700
BEACON_PRYSM_2=http://15.235.227.28:3700
BEACON_PRYSM_3=http://5.199.164.72:3500
BEACON_PRYSM_4=http://5.199.165.39:3700
BEACON_PRYSM_5=http://139.99.68.62:3500
BEACON_TEKU_1=http://15.235.227.141:5052
BEACON_NIMBUS_1=http://57.129.52.134:5052

# =============================================================================
# MEV RELAY CONFIGURATION (Section 7)
# =============================================================================
MEV_RELAY_BLOXROUTE_MAX=https://0x8b5d2e73e2a3a55c6c87b8b6eb92e0149a125c852751db1422fa951e42a09b82c142c3ea98d0d9930b056a3bc9896b8f@bloxroute.max-profit.blxrbdn.com
MEV_RELAY_TITAN=https://0x8c4ed5e24fe5c6ae21018437bde147693f68cda427cd1122cf20819c30eda7ed74f72dece09bb313f2a1855595ab677d@global.titanrelay.xyz
MEV_RELAY_AESTUS=https://0xa15b52576bcbf1072f4a011c0f99f9fb6c66f3e1ff321f11f461d15e31b1cb359caa092c71bbded0bae5b5ea401aab7e@aestus.live
MEV_RELAY_BLOXROUTE_REG=https://0xb0b07cd0abef743db4260b0ed50619cf6ad4d82064cb4fbec9d3ec530f7c5e6793d9f286c4e082c0244ffb9f2658fe88@bloxroute.regulated.blxrbdn.com


# =============================================================================
# MEV-BOOST INSTANCES (Section 7)
# =============================================================================
MEVBOOST_1=http://15.235.224.193:18751
MEVBOOST_2=http://15.235.224.193:18951
MEVBOOST_3=http://15.235.227.28:18751
MEVBOOST_4=http://91.134.41.129:18751
MEVBOOST_5=http://51.79.177.57:18550
MEVBOOST_6=http://57.129.52.134:18550
MEVBOOST_7=http://45.32.152.194:18550

# =============================================================================
# ENGINE API ENDPOINTS (Section 8 — JWT-protected)
# =============================================================================
ENGINE_API_1=http://15.235.224.193:8751
ENGINE_API_2=http://15.235.224.193:8951
ENGINE_API_3=http://15.235.227.28:8751
ENGINE_API_4=http://91.134.41.129:8751

# =============================================================================
# MULTI-CHAIN RPC ENDPOINTS (Section 15)
# =============================================================================
POLYGON_RPC_1=http://148.113.8.12:8545
POLYGON_RPC_2=http://15.235.145.82:8545
POLYGON_RPC_3=http://15.235.218.129:8545
POLYGON_RPC_4=http://91.134.4.151:8545
BASE_RPC_1=http://148.113.35.200:8545
OPTIMISM_RPC_1=http://15.235.145.81:8545
BSC_RPC_1=http://15.235.219.3:8545
CANTO_RPC_1=http://162.19.94.193:8545

# =============================================================================
# PROMETHEUS MONITORING (Section 11)
# =============================================================================
PROMETHEUS_PRIMARY=http://13.213.53.86:9090
PROMETHEUS_SECONDARY=http://212.117.160.52:9090

# =============================================================================
# PROPOSER DUTY API (Section 5)
# =============================================================================
PROPOSER_DUTY_API=http://141.94.218.58:8080/api/v1/proposer-duties

# =============================================================================
# DOCKER TOPOLOGY DISCOVERY (Section 14)
# =============================================================================
DOCKER_TOPOLOGY_1=http://15.235.224.193:28000/targets.json
DOCKER_TOPOLOGY_2=http://5.199.164.72:28000/targets.json
DOCKER_TOPOLOGY_3=http://91.134.41.129:28000/targets.json

# =============================================================================
# HARBOR REGISTRY (Section 17)
# =============================================================================
HARBOR_API=https://harbor.rxdevops.top/api/v2.0
HARBOR_TOKEN=http://141.94.218.58:8090/service/token
HARBOR_REGISTRY=https://harbor.rxdevops.top/v2


# =============================================================================
# SSV INFRASTRUCTURE (Section 13)
# =============================================================================
SSV_NODE_1=http://15.235.224.193:15000
SSV_NODE_2=http://57.129.53.149:15000
SSV_DKG_1=https://15.235.224.193:3030
SSV_DKG_2=https://57.129.53.149:3030



debank Access key : e0f9f5b495ec8924d0ed905a0a68f78c050fdf54
