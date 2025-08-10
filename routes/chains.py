from fastapi import APIRouter, Depends
from pytest import Session

from auth_deps import get_current_user
from database import get_db
from models.user import User

router = APIRouter(prefix="/chains", tags=["Chains"])

chains = {
  "Foundational Chains": {
    "ethereum": {
      "c_id": "eth-mainnet",
      "icon_name": "eth"
    },
    "sepolia": {
      "c_id": "eth-sepolia",
      "icon_name": "eth"
    },
    "holesky": {
      "c_id": "eth-holesky",
      "icon_name": "eth"
    },
    "polygon": {
      "c_id": "matic-mainnet",
      "icon_name": "matic"
    },
    "bsc": {
      "c_id": "bsc-mainnet",
      "icon_name": "bsc"
    },
    "optimism": {
      "c_id": "optimism-mainnet",
      "icon_name": "opt"
    },
    "base": {
      "c_id": "base-mainnet",
      "icon_name": "base"
    },
    "gnosis": {
      "c_id": "gnosis-mainnet",
      "icon_name": "gno"
    }
  },

  "Frontier Chains": {
    "bitcoin": {
      "c_id": "btc-mainnet",
      "icon_name": "btc"
    },
    "solana": {
      "c_id": "solana-mainnet",
      "icon_name": "sol"
    },
    "unichain": {
      "c_id": "unichain-mainnet",
      "icon_name": "uni"
    },
    "berachain": {
      "c_id": "berachain-mainnet",
      "icon_name": "bera"
    },
    "apechain": {
      "c_id": "apechain-mainnet",
      "icon_name": "ape"
    },
    "arbitrum": {
      "c_id": "arbitrum-mainnet",
      "icon_name": "arb"
    },
    "arbitrum_nova": {
      "c_id": "arbitrum-nova-mainnet",
      "icon_name": "arb-nova"
    },
    "avalanche": {
      "c_id": "avalanche-mainnet",
      "icon_name": "avax"
    },
    "axie": {
      "c_id": "axie-mainnet",
      "icon_name": "axie"
    },
    "boba_bnb": {
      "c_id": "boba-bnb-mainnet",
      "icon_name": "boba"
    },
    "boba_ethereum": {
      "c_id": "boba-mainnet",
      "icon_name": "boba"
    },
    "hyperevm": {
      "c_id": "hyperevm-mainnet",
      "icon_name": "hyper"
    },
    "ink": {
      "c_id": "ink-mainnet",
      "icon_name": "ink"
    },
    "lens": {
      "c_id": "lens-mainnet",
      "icon_name": "lens"
    },
    "linea": {
      "c_id": "linea-mainnet",
      "icon_name": "linea"
    },
    "mantle": {
      "c_id": "mantle-mainnet",
      "icon_name": "mantle"
    },
    "oasis_sapphire": {
      "c_id": "oasis-sapphire-mainnet",
      "icon_name": "oasis"
    },
    "palm": {
      "c_id": "palm-mainnet",
      "icon_name": "palm"
    },
    "scroll": {
      "c_id": "scroll-mainnet",
      "icon_name": "scroll"
    },
    "sei": {
      "c_id": "sei-mainnet",
      "icon_name": "sei"
    },
    "taiko": {
      "c_id": "taiko-mainnet",
      "icon_name": "taiko"
    },
    "viction": {
      "c_id": "viction-mainnet",
      "icon_name": "viction"
    },
    "world": {
      "c_id": "world-mainnet",
      "icon_name": "world"
    },
    "zksync": {
      "c_id": "zksync-mainnet",
      "icon_name": "zksync"
    },
    "zora": {
      "c_id": "zora-mainnet",
      "icon_name": "zora"
    }
  },

  "Community Chains": {
    "aurora": {
      "c_id": "aurora-mainnet",
      "icon_name": "aurora"
    },
    "avalanche_beam": {
      "c_id": "avalanche-beam-mainnet",
      "icon_name": "beam"
    },
    "avalanche_dexalot": {
      "c_id": "avalanche-dexalot-mainnet",
      "icon_name": "dexalot"
    },
    "avalanche_meld": {
      "c_id": "avalanche-meld-mainnet",
      "icon_name": "meld"
    },
    "avalanche_numbers": {
      "c_id": "avalanche-numbers",
      "icon_name": "numbers"
    },
    "avalanche_shrapnel": {
      "c_id": "avalanche-shrapnel-mainnet",
      "icon_name": "shrapnel"
    },
    "avalanche_step_network": {
      "c_id": "avalanche-step-network",
      "icon_name": "step"
    },
    "avalanche_uptn": {
      "c_id": "avalanche-uptn",
      "icon_name": "uptn"
    },
    "avalanche_xanachain": {
      "c_id": "avalanche-xanachain",
      "icon_name": "xana"
    },
    "blast": {
      "c_id": "blast-mainnet",
      "icon_name": "blast"
    },
    "bnb_opbnb": {
      "c_id": "bnb-opbnb-mainnet",
      "icon_name": "opbnb"
    },
    "canto": {
      "c_id": "canto-mainnet",
      "icon_name": "canto"
    },
    "celo": {
      "c_id": "celo-mainnet",
      "icon_name": "celo"
    },
    "covalent": {
      "c_id": "covalent-internal-network-v1",
      "icon_name": "covalent"
    },
    "cronos": {
      "c_id": "cronos-mainnet",
      "icon_name": "cronos"
    },
    "cronos_zkevm": {
      "c_id": "cronos-zkevm-mainnet",
      "icon_name": "zkevm"
    },
    "defi_kingdoms": {
      "c_id": "defi-kingdoms-mainnet",
      "icon_name": "dfk"
    },
    "emerald_paratime": {
      "c_id": "emerald-paratime-mainnet",
      "icon_name": "oasis"
    },
    "fantom": {
      "c_id": "fantom-mainnet",
      "icon_name": "ftm"
    },
    "fraxtal": {
      "c_id": "fraxtal-mainnet",
      "icon_name": "frax"
    },
    "horizen_eon": {
      "c_id": "horizen-eon-mainnet",
      "icon_name": "eon"
    },
    "merlin": {
      "c_id": "merlin-mainnet",
      "icon_name": "merlin"
    },
    "metis": {
      "c_id": "metis-mainnet",
      "icon_name": "metis"
    },
    "moonbeam": {
      "c_id": "moonbeam-mainnet",
      "icon_name": "moonbeam"
    },
    "moonriver": {
      "c_id": "moonriver-mainnet",
      "icon_name": "moonriver"
    },
    "polygon_zkevm": {
      "c_id": "polygon-zkevm-mainnet",
      "icon_name": "zkevm"
    },
    "redstone": {
      "c_id": "redstone-mainnet",
      "icon_name": "redstone"
    },
    "rollux": {
      "c_id": "rollux-mainnet",
      "icon_name": "rollux"
    },
    "sx": {
      "c_id": "sx-mainnet",
      "icon_name": "sx"
    },
    "x1": {
      "c_id": "x1-mainnet",
      "icon_name": "x1"
    },
    "zetachain": {
      "c_id": "zetachain-mainnet",
      "icon_name": "zeta"
    }
  },

  "Archived Chains": {
    "dos": {
      "c_id": "avalanche-dos",
      "icon_name": "dos"
    },
    "fncy": {
      "c_id": "bnb-fncy-mainnet",
      "icon_name": "fncy"
    },
    "evmos": {
      "c_id": "evmos-mainnet",
      "icon_name": "evmos"
    },
    "songbird": {
      "c_id": "flarenetworks-canary-mainnet",
      "icon_name": "songbird"
    },
    "harmony": {
      "c_id": "harmony-mainnet",
      "icon_name": "harmony"
    },
    "lisk": {
      "c_id": "lisk-mainnet",
      "icon_name": "lisk"
    },
    "loot": {
      "c_id": "loot-mainnet",
      "icon_name": "loot"
    },
    "meter": {
      "c_id": "meter-mainnet",
      "icon_name": "meter"
    },
    "milkomeda_c1": {
      "c_id": "milkomeda-c1-mainnet",
      "icon_name": "milkomeda"
    },
    "mode": {
      "c_id": "mode-mainnet",
      "icon_name": "mode"
    },
    "telos": {
      "c_id": "telos-mainnet",
      "icon_name": "telos"
    },
    "ultron": {
      "c_id": "ultron-mainnet",
      "icon_name": "ultron"
    }
  }
}

@router.get("/")
def get_chains(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return chains
