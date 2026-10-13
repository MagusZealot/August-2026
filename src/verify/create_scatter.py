import pandas as pd
import numpy as np

df = pd.read_csv('C:/Users/IT-40126/Documents/August 2026-20261008T011759Z-1-001/August 2026/data/raw/2026-10-06-13-38-11_EXPORT_CSV_45625_808_0.csv')

print('Shape:', df.shape)
print('Unique game_codes:', df['game_code'].nunique())
print('Unique game_names:', df['game_name'].nunique())
print()
print('Balance range:', df['balance'].min(), '-', df['balance'].max())
print('Effective bet amount range:', df['effective_bet_amount'].min(), '-', df['effective_bet_amount'].max())
print()
print('Game codes sample:', df['game_code'].unique()[:20])
print('Game names sample:', df['game_name'].unique()[:20])