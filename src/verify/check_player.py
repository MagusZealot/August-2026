import json

all_games = {}
for i in range(27):
    fname = 'C:\\Users\\IT-40126\\Documents\\August 2026-20261008T011759Z-1-001\\August 2026\\output\\all_players_dossiers_' + str(i).zfill(2) + '.json'
    with open(fname) as f:
        data = json.load(f)
    for p in data.get('players', []):
        if p.get('player_id') == 'p02cf17391168':
            for g in p.get('games', []):
                game_name = g['game']
                if game_name not in all_games:
                    all_games[game_name] = {'bets': 0, 'debit': 0.0, 'wins': 0, 'losses': 0}
                all_games[game_name]['bets'] += g['bets']
                all_games[game_name]['debit'] += g['debit']
                all_games[game_name]['wins'] += g['wins']
                all_games[game_name]['losses'] += g['losses']
            break

print('All games for player across all dossiers:')
for game, stats in all_games.items():
    print('  ' + game + ': bets=' + str(stats['bets']) + ', debit=' + str(stats['debit']) + ', wins=' + str(stats['wins']) + ', losses=' + str(stats['losses']))

total_bets = sum(s['bets'] for s in all_games.values())
total_debit = sum(s['debit'] for s in all_games.values())
print('Total: bets=' + str(total_bets) + ', debit=' + str(total_debit))