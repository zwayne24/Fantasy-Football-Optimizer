import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary, LpStatus, PULP_CBC_CMD
import tkinter as tk
from tkinter import Canvas, Scrollbar, VERTICAL

# run the optimization
def run_optimization(teams, pick_number, qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, te_bench, kicker, flex_starter, dst, df):
    total_roster = qb_starter + rb_starter + wr_starter + te_starter + flex_starter + qb_bench + wr_bench + rb_bench + te_bench + kicker + dst
    picks = draft_picks(teams, pick_number, total_roster)
    points_per_pick = ppp(df, picks)
    print(points_per_pick)
    # maximization problem
    m = LpProblem('draft', LpMaximize)
    # get the number of rows and columns from the points per pick matrix
    # rows are the number of picks left, columns are the number of positions
    rows = len(points_per_pick)
    cols = len(points_per_pick[0])
    # create the variables
    # x is a weighting for each player
    #   not drafted is a weight of 0
    #   starter is a weight of 16
    #   bench is a weight that is less than 16, depending on the position
    # selected_starter is a binary variable that is 1 if the player is a starter, 0 if not
    # selected_bench is a binary variable that is 1 if the player is a bench player, 0 if not
    x = [[LpVariable(f'x{i}{j}', lowBound=0, cat='Integer') for j in range(cols)] for i in range(rows)]
    selected_starter = [[LpVariable(f'selected_starter{i}{j}', cat='Binary') for j in range(cols)] for i in range(rows)]
    selected_bench = [[LpVariable(f'selected_bench{i}{j}', cat='Binary') for j in range(cols)] for i in range(rows)]

    # sets the number of qb starters and bench players, 0 is the column for QB
    m+= lpSum([selected_starter[i][0] for i in range(rows)]) == qb_starter, 'qb_starter'
    m+= lpSum([selected_bench[i][0] for i in range(rows)]) == qb_bench, 'qb_bench'
    # sets the weighting, x is 16 if the player is a starter, 1 if bench, 0 if neither
    for i in range(rows):
        m+= x[i][0] == 16*selected_starter[i][0] + selected_bench[i][0], f'qb_weighting{i}'
    
    # same as before, except an rb can be a flex, so the amound of starting rbs can waver
    m+= lpSum([selected_starter[i][1] for i in range(rows)]) >= rb_starter, 'rb_starter'
    m+= lpSum([selected_starter[i][1] for i in range(rows)]) <= rb_starter+flex_starter, 'rb_starter_flex'
    m+= lpSum([selected_bench[i][1] for i in range(rows)]) == rb_bench, 'rb_bench'
    # sets the weighting, x is 16 if the player is a starter, 0 if not selected, and 1-3 for bench 
    # depending on how many bench rbs you already have
    for i in range(rows):
        m+= x[i][1] == 16*selected_starter[i][1] + rb_bench*selected_bench[i][1], f'rb_weighting{i}'
    
    # wrs same as rbs      
    m+= lpSum([selected_starter[i][2] for i in range(rows)]) >= wr_starter, 'wr_starter'
    m+= lpSum([selected_starter[i][2] for i in range(rows)]) <= wr_starter+flex_starter, 'wr_starter_flex'
    m+= lpSum([selected_bench[i][2] for i in range(rows)]) == wr_bench, 'wr_bench'
    # sets the weighting, x is 16 if the player is a starter, 0 if not selected, and 1-3 for bench 
    # depending on how many bench wrs you already have
    for i in range(rows):
        m+= x[i][2] == 16*selected_starter[i][2] + wr_bench*selected_bench[i][2], f'wr_weighting{i}'

    # for flex position, it can be a rb or wr, so we just need the total wr/rb starters to be correct, wherever the flex comes from
    m+= lpSum([selected_starter[i][2] for i in range(rows)])+lpSum([selected_starter[i][1] for i in range(rows)]) == rb_starter+flex_starter+wr_starter, 'flex_starter'
        
    # TE
    m+= lpSum([selected_starter[i][3] for i in range(rows)]) == te_starter, 'te_starter'
    m+= lpSum([selected_bench[i][3] for i in range(rows)]) == te_bench, 'te_bench'
    for i in range(rows):
        m+= x[i][3] == 16*selected_starter[i][3]+selected_bench[i][3], f'te_weighting{i}'
    
    # K - no bench kickers
    m+= lpSum([selected_starter[i][4] for i in range(rows)]) == kicker, 'kicker'
    m+= lpSum([selected_bench[i][4] for i in range(rows)]) == 0, 'kicker_bench'
    for i in range(rows):
        m+= x[i][4] == 16*selected_starter[i][4], f'kicker_weighting{i}'
    
    # DST - no bench DST
    m+= lpSum([selected_starter[i][5] for i in range(rows)]) == dst, 'dst'
    m+= lpSum([selected_bench[i][5] for i in range(rows)]) == 0, 'dst_bench'
    for i in range(rows):
        m+= x[i][5] == 16*selected_starter[i][5], f'dst_weighting{i}'

    # Each round, only one player can be selected
    for i in range(rows):
        m += lpSum(selected_starter[i])+lpSum(selected_bench[i]) == 1, f'round{i}'

    # Objective function: Maximize the sum of selected values
    # which is the weighted sum of the points per pick
    m += lpSum(x[i][j] * points_per_pick[i][j] for i in range(rows) for j in range(cols))

    # Solve the problem and suppress output
    m.solve(PULP_CBC_CMD(msg=1))

    # if the status is optimal, get the results
    if LpStatus[m.status] == "Optimal":
        pos_to_draft = ""
        for i in range(rows):
            for j in range(cols):
                # if the value is greater than 1, it means that position was selected
                # find the position for your current pick
                # i==0 means it it's your current pick, j is the position
                if x[i][j].varValue >= 1 and i == 0:
                    if j == 0:
                        pos_to_draft = "QB"
                    elif j == 1:
                        pos_to_draft = "RB"
                    elif j == 2:
                        pos_to_draft = "WR"
                    elif j == 3:
                        pos_to_draft = "TE"
                    elif j == 4:
                        pos_to_draft = "K"
                    elif j == 5:
                        pos_to_draft = "DST"
                    
                    # to_draft is the best player available at that optimal position to draft
                    to_draft = df[df['Pos'] == pos_to_draft].iloc[0]['Player']
                    # return the best player available at that position
                if x[i][j].varValue >= 1:
                    print("#"*50)
                    print(j)
        return to_draft
    else:
        # if no optimal solution is found, return this
        return "No optimal solution found"      
    
def draft_picks(teams,slot,rds):
    picks = []
    for i in range(1,rds+1):
        for j in range(1,teams+1):
            if j == slot and i % 2 == 1:
                picks.append(((i-1)*teams)+j)
            elif j == teams - slot + 1 and i % 2 == 0:
                picks.append(((i-1)*teams)+j)

    return picks
    
def ppp(df, picks):
    positions = ["QB", "RB", "WR", "TE", "K", "DST"]
    # initialize points per pick array, rows = # of picks, cols = # of positions
    points_per_pick = [[0 for i in range(len(positions))] for j in range(len(picks))]
    for i in range(len(picks)):
        # if it's your current pick, get the max points available for each position
        if i == 0:
            max_qb_pts = (df.loc[df['Pos'] == 'QB'])['Projection'].max()
            max_rb_pts = (df.loc[df['Pos'] == 'RB'])['Projection'].max()
            max_wr_pts = (df.loc[df['Pos'] == 'WR'])['Projection'].max()
            max_te_pts = (df.loc[df['Pos'] == 'TE'])['Projection'].max()
            max_k_pts = (df.loc[df['Pos'] == 'K'])['Projection'].max()
            max_def_pts = (df.loc[df['Pos'] == 'DST'])['Projection'].max()
        # if it's not your current pick, i.e. you're forecasting out
        # find the players expected to be available at each future pick by using the ADP
        # and take an average of the top 2 player projections at each position
        else:
            df_next = df.copy()
            # remove the x players with the highest ranking - where x is the number of picks between the previous pick and the current pick
            df_next = df_next.sort_values(by='Rank',ascending=True).iloc[(picks[i]-picks[0]):]
            max_qb_pts = max(0,df_next.loc[df_next['Pos'] == 'QB'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_rb_pts = max(0,df_next.loc[df_next['Pos'] == 'RB'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_wr_pts = max(0,df_next.loc[df_next['Pos'] == 'WR'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_te_pts = max(0,df_next.loc[df_next['Pos'] == 'TE'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_k_pts = max(0,df_next.loc[df_next['Pos'] == 'K'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_def_pts = max(0,df_next.loc[df_next['Pos'] == 'DST'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
        
        # assign the max points for each position to the points per pick array
        points_per_pick[i][0] = max_qb_pts
        points_per_pick[i][1] = max_rb_pts
        points_per_pick[i][2] = max_wr_pts
        points_per_pick[i][3] = max_te_pts
        points_per_pick[i][4] = max_k_pts
        points_per_pick[i][5] = max_def_pts
            
    return points_per_pick

def pppD(df, picks):
    positions = ["QB", "RB", "WR", "TE", "K"]
    # initialize points per pick array, rows = # of picks, cols = # of positions
    points_per_pick = [[0 for i in range(len(positions))] for j in range(len(picks))]
    for i in range(len(picks)):
        # if it's your current pick, get the max points available for each position
        if i == 0:
            max_qb_pts = (df.loc[df['Pos'] == 'QB'])['Projection'].max()
            max_rb_pts = (df.loc[df['Pos'] == 'RB'])['Projection'].max()
            max_wr_pts = (df.loc[df['Pos'] == 'WR'])['Projection'].max()
            max_te_pts = (df.loc[df['Pos'] == 'TE'])['Projection'].max()
            max_k_pts = (df.loc[df['Pos'] == 'K'])['Projection'].max()
        # if it's not your current pick, i.e. you're forecasting out
        # find the players expected to be available at each future pick by using the ADP
        # and take an average of the top 2 player projections at each position
        else:
            df_next = df.copy()
            # remove the x players with the highest ranking - where x is the number of picks between the previous pick and the current pick
            df_next = df_next.sort_values(by='Rank',ascending=True).iloc[(picks[i]-picks[0]):]
            max_qb_pts = max(0,df_next.loc[df_next['Pos'] == 'QB'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_rb_pts = max(0,df_next.loc[df_next['Pos'] == 'RB'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_wr_pts = max(0,df_next.loc[df_next['Pos'] == 'WR'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_te_pts = max(0,df_next.loc[df_next['Pos'] == 'TE'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
            max_k_pts = max(0,df_next.loc[df_next['Pos'] == 'K'].sort_values(by='Projection',ascending=False).head(1)['Projection'].mean())
        
        # assign the max points for each position to the points per pick array
        points_per_pick[i][0] = max_qb_pts
        points_per_pick[i][1] = max_rb_pts
        points_per_pick[i][2] = max_wr_pts
        points_per_pick[i][3] = max_te_pts
        points_per_pick[i][4] = max_k_pts
            
    return points_per_pick


def run_optimizationD(teams, pick_number, qb_starter, qb_bench, rb_starter, rb_bench, wr_starter, wr_bench, te_starter, kicker, flex_starter, df):
    total_roster = qb_starter + rb_starter + wr_starter + te_starter + flex_starter + qb_bench + wr_bench + rb_bench + kicker
    picks = draft_picks(teams, pick_number, total_roster)
    points_per_pick = pppD(df, picks)
    print(points_per_pick)
    # maximization problem
    m = LpProblem('draft', LpMaximize)
    # get the number of rows and columns from the points per pick matrix
    # rows are the number of picks left, columns are the number of positions
    rows = len(points_per_pick)
    cols = len(points_per_pick[0])
    # create the variables
    # x is a weighting for each player
    #   not drafted is a weight of 0
    #   starter is a weight of 16
    #   bench is a weight that is less than 20, depending on the position
    # selected_starter is a binary variable that is 1 if the player is a starter, 0 if not
    # selected_bench is a binary variable that is 1 if the player is a bench player, 0 if not
    x = [[LpVariable(f'x{i}{j}', lowBound=0, cat='Integer') for j in range(cols)] for i in range(rows)]
    selected_starter = [[LpVariable(f'selected_starter{i}{j}', cat='Binary') for j in range(cols)] for i in range(rows)]
    selected_bench = [[LpVariable(f'selected_bench{i}{j}', cat='Binary') for j in range(cols)] for i in range(rows)]

    # sets the number of qb starters and bench players, 0 is the column for QB
    m+= lpSum([selected_starter[i][0] for i in range(rows)]) == qb_starter, 'qb_starter'
    m+= lpSum([selected_bench[i][0] for i in range(rows)]) == qb_bench, 'qb_bench'
    # sets the weighting, x is 16 if the player is a starter, 1 if bench, 0 if neither
    for i in range(rows):
        m+= x[i][0] == 16*selected_starter[i][0] + selected_bench[i][0], f'qb_weighting{i}'
    
    # same as before, except an rb can be a flex, so the amound of starting rbs can waver
    m+= lpSum([selected_starter[i][1] for i in range(rows)]) == rb_starter, 'rb_starter'
    m+= lpSum([selected_bench[i][1] for i in range(rows)]) == rb_bench, 'rb_bench'
    # sets the weighting, x is 16 if the player is a starter, 0 if not selected, and 1-3 for bench 
    # depending on how many bench rbs you already have
    for i in range(rows):
        m+= x[i][1] == 16*selected_starter[i][1] + rb_bench*selected_bench[i][1], f'rb_weighting{i}'
    
    # wrs same as rbs      
    m+= lpSum([selected_starter[i][2] for i in range(rows)]) >= wr_starter, 'wr_starter'
    m+= lpSum([selected_starter[i][2] for i in range(rows)]) <= wr_starter+flex_starter, 'wr_starter_flex'
    m+= lpSum([selected_bench[i][2] for i in range(rows)]) <= wr_bench, 'wr_bench'
    # sets the weighting, x is 16 if the player is a starter, 0 if not selected, and 1-3 for bench 
    # depending on how many bench wr/tes you already have
    for i in range(rows):
        m+= x[i][2] == 16*selected_starter[i][2] +wr_bench*selected_bench[i][2], f'wr_weighting{i}'
        
    # for flex position, it can be a te or wr, so we just need the total wr/te starters to be correct, wherever the flex comes from
    m+= lpSum([selected_starter[i][2] for i in range(rows)])+lpSum([selected_starter[i][3] for i in range(rows)]) == te_starter+flex_starter+wr_starter, 'flex_starter'
        
    # TE
    m+= lpSum([selected_starter[i][3] for i in range(rows)]) >= te_starter, 'te_starter'
    m+= lpSum([selected_starter[i][3] for i in range(rows)]) <= te_starter+flex_starter, 'te_starter_flex'
    m+= lpSum([selected_bench[i][3] for i in range(rows)]) <= wr_bench, 'te_bench'
    # sets the weighting, x is 16 if the player is a starter, 0 if not selected, and 1-3 for bench 
    # depending on how many bench wr/tes you already have
    for i in range(rows):
        m+= x[i][3] == 16*selected_starter[i][3]+wr_bench*selected_bench[i][3], f'te_weighting{i}'
        
    m+= lpSum([selected_bench[i][2] for i in range(rows)])+lpSum([selected_bench[i][3] for i in range(rows)]) == wr_bench, 'flex_bench'
    
    # K - no bench kickers
    m+= lpSum([selected_starter[i][4] for i in range(rows)]) == kicker, 'kicker'
    m+= lpSum([selected_bench[i][4] for i in range(rows)]) == 0, 'kicker_bench'
    for i in range(rows):
        m+= x[i][4] == 16*selected_starter[i][4], f'kicker_weighting{i}'
    
    # DST - no bench DST
    #m+= lpSum([selected_starter[i][5] for i in range(rows)]) == dst, 'dst'
    #m+= lpSum([selected_bench[i][5] for i in range(rows)]) == 0, 'dst_bench'
    #for i in range(rows):
    #    m+= x[i][5] == 16*selected_starter[i][5], f'dst_weighting{i}'

    # Each round, only one player can be selected
    for i in range(rows):
        m += lpSum(selected_starter[i])+lpSum(selected_bench[i]) == 1, f'round{i}'

    # Objective function: Maximize the sum of selected values
    # which is the weighted sum of the points per pick
    m += lpSum(x[i][j] * points_per_pick[i][j] for i in range(rows) for j in range(cols))

    # Solve the problem and suppress output
    m.solve(PULP_CBC_CMD(msg=1))

    # print objective value
    print(m.objective.value())
    
    # if the status is optimal, get the results
    if LpStatus[m.status] == "Optimal":
        pos_to_draft = ""
        for i in range(rows):
            for j in range(cols):
                # if the value is greater than 1, it means that position was selected
                # find the position for your current pick
                # i==0 means it it's your current pick, j is the position
                if x[i][j].varValue >= 1 and i == 0:
                    if j == 0:
                        pos_to_draft = "QB"
                    elif j == 1:
                        pos_to_draft = "RB"
                    elif j == 2:
                        pos_to_draft = "WR"
                    elif j == 3:
                        pos_to_draft = "TE"
                    elif j == 4:
                        pos_to_draft = "K"

                    # to_draft is the best player available at that optimal position to draft
                    to_draft = df[df['Pos'] == pos_to_draft].iloc[0]['Player']
                    # return the best player available at that position
                if x[i][j].varValue >= 1:
                    print("#"*50)
                    print(j)
        return to_draft

    else:
        # if no optimal solution is found, return this
        return "No optimal solution found"                                         
