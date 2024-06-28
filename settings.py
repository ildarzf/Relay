# Бриджит только ETH
chain_from = 'zksync' # 'ethereum', 'optimism', 'zkevm', 'arbitrum', 'nova', 'zksync', 'linea', 'base', 'zora', 'scroll', 'mode', 'blast'

chain_to = 'zora' # 'ethereum', 'optimism', 'zkevm', 'arbitrum', 'nova', 'zksync', 'linea', 'base', 'zora', 'scroll', 'mode', 'blast'

time_wait_wal = [250, 600]  # пауза между кошельками

proc_stay_wallet = [6, 12]  # какой процент оставлять на кошельке в сети отправления.

skip_if_low = 0.0043  # если меньше этого значения ETH не выводить

ACCEPTABLE_GWEI_BASE = 20   # Гвей выше которого ждем

shuffle =True # перемешать кошельки False/True

