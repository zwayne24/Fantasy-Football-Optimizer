from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import model
import scraper
import os
app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

manager = None

@app.route('/process-info-ESPN', methods=['POST'])
def process_info_ESPN():
    data = request.json
    roster_settings = data.get('roster_settings')
    personal_team = data.get('personal_team')
    drafted_players = data.get('drafted_players')
    personal_team_name = data.get('personal_team_name')
    
    df = pd.read_csv('../2024_Draft.csv')
    
    # Initialize the desired format for position counts
    drafted_pos = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'DST': 0, 'K': 0, 'FLEX':0}
                
    # go through each team and find the players that are not drafted
    # add them to a list of available players
    available_players = df.copy()
    for idx, (team, players) in enumerate(drafted_players.items()):
        for player_info in players:
            if player_info['Player'] != ' ':
                # split player on space and take first two elements, remove punctuation
                p = player_info['Player'].split(' ')[0] + ' ' + player_info['Player'].split(' ')[1]
                p = p.replace('.', '')
                # find where p matches in df and add to drafted_teams
                for i in range(len(df)):
                    if (df['Player'][i].split(' ')[0] + ' ' + df['Player'][i].split(' ')[1]).replace('.', '') == p:
                        p = df['Player'][i]
                        ppos = df['Pos'][i]
                        if team == personal_team_name:
                            print(personal_team_name)
                            if ppos == 'QB': 
                                drafted_pos['QB'] += 1
                            elif ppos == 'RB':
                                drafted_pos['RB'] += 1
                            elif ppos == 'WR':
                                drafted_pos['WR'] += 1
                            elif ppos == 'TE':
                                drafted_pos['TE'] += 1
                            elif ppos == 'K':
                                drafted_pos['K'] += 1
                available_players = available_players.drop(available_players[available_players['Player'] == p].index)
                    
    qb_starter = max(roster_settings['slots_qb']-drafted_pos[personal_team]['QB'],0)
    qb_bench = max(1 - max(drafted_pos[personal_team]['QB'] - roster_settings['slots_qb'], 0), 0)
    rb_starter = max(roster_settings['slots_rb']-drafted_pos[personal_team]['RB'],0)
    rb_bench = max(3 - max(drafted_pos[personal_team]['RB'] - roster_settings['slots_rb'], 0), 0)
    wr_starter = max(roster_settings['slots_wr']-drafted_pos[personal_team]['WR'],0)
    wr_bench = max(3 - max(drafted_pos[personal_team]['WR'] - roster_settings['slots_wr'], 0), 0)
    te_starter = max(roster_settings['slots_te']-drafted_pos[personal_team]['TE'],0)
    te_bench = 0
    if rb_starter == 0 and wr_starter == 0 and te_starter == 0 and (drafted_pos[personal_team]['RB'] + drafted_pos[personal_team]['WR'] + drafted_pos[personal_team]['TE']) > (roster_settings['slots_rb'] + roster_settings['slots_wr'] + roster_settings['slots_te']):
        flex_starter = 0
    else:
        flex_starter = roster_settings['slots_flex']
    k = max(roster_settings['slots_k']-drafted_pos[personal_team]['K'],0)
    dst = max(roster_settings['slots_def']-drafted_pos[personal_team]['DST'],0)
    print(qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, te_bench, k, flex_starter, dst)
    return jsonify(model.run_optimization(roster_settings['teams'],personal_team, qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, te_bench, k, flex_starter, dst, available_players))

@app.route('/process-info-Domination', methods=['POST'])
def process_info_Domination():
    data = request.json
    roster_settings = data.get('roster_settings')
    personal_team = data.get('personal_team')
    drafted_players = data.get('drafted_players')
    personal_team_name = data.get('personal_team_name')
    
    df = pd.read_csv('../2024_Draft.csv')
               
    # Initialize the desired format for position counts
    drafted_pos = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'DST': 0, 'K': 0, 'FLEX':0}
 
    # go through each team and find the players that are not drafted
    # add them to a list of available players
    available_players = df.copy()
    for idx, (team, players) in enumerate(drafted_players.items()):
        for player_info in players:
            if player_info['Player'] != ' ':
                # split player on space and take first two elements, remove punctuation
                p = player_info['Player'].split(' ')[0] + ' ' + player_info['Player'].split(' ')[1]
                p = p.replace('.', '')
                # find where p matches in df and add to drafted_teams
                for i in range(len(df)):
                    if (df['Player'][i].split(' ')[0] + ' ' + df['Player'][i].split(' ')[1]).replace('.', '') == p:
                        p = df['Player'][i]
                        ppos = df['Pos'][i]
                        if team == personal_team_name:
                            print(personal_team_name)
                            if ppos == 'QB': 
                                drafted_pos['QB'] += 1
                            elif ppos == 'RB':
                                drafted_pos['RB'] += 1
                            elif ppos == 'WR':
                                drafted_pos['WR'] += 1
                            elif ppos == 'TE':
                                drafted_pos['TE'] += 1
                            elif ppos == 'K':
                                drafted_pos['K'] += 1
                available_players = available_players.drop(available_players[available_players['Player'] == p].index)
    print(drafted_pos)              
    # teams, pick_number, qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, kicker, flex_starter, df):                
    qb_starter = max(roster_settings['slots_qb']-drafted_pos['QB'],0)
    qb_bench = max(1 - max(drafted_pos['QB'] - roster_settings['slots_qb'], 0), 0)
    rb_starter = max(roster_settings['slots_rb']-drafted_pos['RB'],0)
    rb_bench = max(3 - max(drafted_pos['RB'] - roster_settings['slots_rb'], 0), 0)
    wr_starter = 0
    wr_bench = max(3 - max(drafted_pos['WR'] - roster_settings['slots_flex'], 0), 0)
    te_starter = 0
    flex_starter = max(roster_settings['slots_flex'] - drafted_pos['WR']-drafted_pos['TE'],0)
    k = max(roster_settings['slots_k']-drafted_pos['K'],0)
    
    return jsonify(model.run_optimizationD(roster_settings['teams'],personal_team, qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, k, flex_starter, available_players))

@app.route('/launch-ESPN', methods=['POST'])
def launch_ESPN():
    global manager
    data = request.json
    browser = data.get('browser')
    manager = scraper.ESPNManager()
    return manager.launch_ESPN(browser)
    
@app.route('/scrape-ESPN', methods=['POST'])
def scrape_ESPN():
    global manager
    if manager:
        return manager.scrape_ESPN()
    else:
        return jsonify({"error": "Manager not initialized"}), 400

@app.route('/scrape-FP', methods=['POST'])
def scrape_FP():
    global manager
    if manager:
        return manager.scrape_FP()
    else:
        return jsonify({"error": "Manager not initialized"}), 400

@app.route('/scrape-ESPN2', methods=['POST'])
def scrape_ESPN2():
    return pd.read_csv('roster.csv').to_json()
    # global manager
    # if manager:
    #     return manager.scrape_ESPN2()
    # else:
    #     return jsonify({"error": "Manager not initialized"}), 400

if __name__ == '__main__':
    app.run(debug=True)