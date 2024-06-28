from config import chain_info, ZERO_ADDRESS
from settings import *
import requests
from web3 import Web3
from loguru import logger
import random
import time



def wallet():
    with open('wallets.txt', 'r') as f:
        wallets = f.read().splitlines()
        return wallets


def get_gas():
    try:
        web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
        gas_price = web3.eth.gas_price
        gwei_gas_price = web3.from_wei(gas_price, 'gwei')
        return gwei_gas_price
    except Exception as error:
        return get_gas()

def wait_gas():
    while True:
        current_gas = get_gas()
        if current_gas > ACCEPTABLE_GWEI_BASE:
            logger.info(f'current gas in Ethereum : {current_gas} > {ACCEPTABLE_GWEI_BASE}')
            time.sleep(20)
        else:
            break

def get_bridge_config(from_chain_id, dest_chain_id, proxie):
        url = "https://api.relay.link/config"

        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "referrer": "https://www.relay.link/",
            "referrerPolicy": "strict-origin-when-cross-origin",
        }

        params = {
            'originChainId': from_chain_id,
            'destinationChainId': dest_chain_id,
            'user': ZERO_ADDRESS,
            'currency': ZERO_ADDRESS,
        }

        response = requests.get(url=url, headers=headers, params=params, proxies=proxie)
        return response.json()

def get_bridge_data(address, from_chain_id, dest_chain_id, amount_in_wei, proxie):
        url = f"https://api.relay.link/execute/call"

        payload = {
            "user": address,
            "txs": [
                {
                    "to": address,
                    "value": amount_in_wei,
                    "data": "0x"
                }
            ],
            "originChainId": from_chain_id,
            "destinationChainId": dest_chain_id,
            "source": "relay.link"
        }

        response = requests.post(url=url, json=payload, proxies=proxie)
        return response.json()


def prepare_transaction(address, chain_from_id, value: int = 0) -> dict:

        tx_params = {
            'chainId': chain_from_id,
            'from': web3.to_checksum_address(address),
            'nonce': web3.eth.get_transaction_count(address),
            'value': value,
        }
        return tx_params

def bridge(address, chain_from, chain_to,amount_in_wei, proxie):

        from_chain_id = chain_info[chain_from]['chain_id']
        dest_chain_id = chain_info[chain_to]['chain_id']

        supported_chains = [1, 10, 1101, 42161, 42170, 324, 59144, 8453, 7777777, 534352, 34443, 81457]
        if from_chain_id not in supported_chains or dest_chain_id not in supported_chains:
            logger.error(f'Бридж из {chain_from} в {chain_to} не доступен')


        networks_data = get_bridge_config(from_chain_id, dest_chain_id, proxie)
        tx_data = get_bridge_data(address, from_chain_id, dest_chain_id, amount_in_wei, proxie)

        amount = amount_in_wei

        if networks_data['enabled']:

            max_amount = networks_data['solver']['capacityPerRequest']

            if amount <= float(max_amount):

                tx = (prepare_transaction(address, from_chain_id, amount)) | {
                    'to': web3.to_checksum_address(tx_data["steps"][0]['items'][0]['data']['to']),
                    'data': tx_data["steps"][0]['items'][0]['data']['data']
                }

                tx.update({'maxFeePerGas': int(web3.eth.gas_price * 1.05)})
                tx.update({'maxPriorityFeePerGas': int(web3.eth.gas_price * 1.05)})
                gasLimit = web3.eth.estimate_gas(tx)
                tx.update({'gas': gasLimit})

                signed_tx = web3.eth.account.sign_transaction(tx, private_key)

                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

                tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

                if tx_receipt['status'] == 1:
                    logger.success(f'Отправил через Relay.link - Tx hash: {chain_info[chain_from]["scan"]}/{tx_hash.hex()}')


                elif tx_receipt['status'] == 0:
                    logger.warning(f'Не удалось отправить')
                    logger.warning(f'Tx hash: {chain_info[chain_from]["scan"]}/{tx_hash.hex()}')


            else:
                logger.info(f"Limit range for bridge: 0 - {max_amount} ETH")
        else:
            logger.info(f"Bridge from {address} -> {dest_chain_id} is not active!")



if __name__ == "__main__":

    wallets = wallet()

    if shuffle:
        random.shuffle(wallets)

    num = 0


    for data in wallets:
        try:
            private_key, proxy = data.split(';')

            if proxy is not None and len(proxy) > 4 and proxy[:4] != 'http':
                proxy = 'http://' + proxy

            proxie = {'http': proxy, 'https': proxy} if proxy and proxy != '' else {}

            rpc = chain_info[chain_from]['rpc']
            web3 = Web3(Web3.HTTPProvider(rpc))
            address = web3.eth.account.from_key(private_key).address
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.from_wei(balance_wei, 'ether')

            rnd_proc = round(random.uniform(proc_stay_wallet[0], proc_stay_wallet[1]), 2)

            rnd_amount = int(balance_wei * ((100 - rnd_proc) / 100))

            balance_round = round(web3.from_wei(rnd_amount, 'ether'), 5)
            balance_round_wei = web3.to_wei(balance_round, 'ether')
            amount_in_wei = balance_round_wei

            num= num+1
            if balance_eth > skip_if_low:
                wait_gas()
                logger.info(f'Начинаю бридж из сети {chain_from} в сеть {chain_to} через Relay.link {address}')
                bridge(address, chain_from, chain_to, amount_in_wei, proxie)
                tm = random.randint(time_wait_wal[0], time_wait_wal[1])
                logger.info(f'Сплю {tm}')
                time.sleep(tm)
            else:
                logger.info(f'Баланс {address} в сети {chain_from} меньше {skip_if_low}.  Перехожу к следующему действию')
        except Exception as err:
           logger.error(f'{err}')






