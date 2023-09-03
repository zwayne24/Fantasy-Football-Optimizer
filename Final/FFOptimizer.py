import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary, LpStatus, PULP_CBC_CMD
import tkinter as tk
from tkinter import Canvas, Scrollbar, VERTICAL
import os

class PlayerDraftApp:
    def __init__(self, root, df):
        self.root = root
        # set title of window
        self.root.title("Fantasy Football Draft Optimizer")
        
        # set data frame and copy to serve as original for tier list
        self.df = df
        self.dfog = df.copy()
        # set number of teams, positions, and roster requirements
        self.teams = 12
        self.pick_number = 9
        self.positions = ["QB", "RB", "WR", "TE", "K", "DST"]
        self.qb_starter = 1
        self.rb_starter = 2
        self.wr_starter = 2
        self.te_starter = 1
        self.flex_starter = 1
        self.qb_bench = 1
        self.wr_bench = 2
        self.rb_bench = 2
        self.kicker = 1
        self.dst = 1
        self.total_roster = self.qb_starter + self.rb_starter + self.wr_starter + self.te_starter + self.flex_starter + self.qb_bench + self.wr_bench + self.rb_bench + self.kicker + self.dst
        # set drafted player list to empty, to be filled and shown who you draft on window
        self.drafted_players = ""
        # set total drafted to empty, to be added to and used to know who to grey out on tier list
        self.total_drafted = []
        # set current pick to 1
        self.current_pick = 1
        # create list of draft picks, dependent on number of teams, draft rounds, and your pick number
        self.picks = self.draft_picks(self.teams,self.pick_number,self.total_roster)
        # create points per pick, 2d array of how many points you can expect to get from each position at each of your picks
        self.points_per_pick = self.ppp(self.df, self.picks)
        
        # create result label - label at bottom, shows when your next pick is or who the best available player is
        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack(side="bottom", anchor="s")
        
        # create pick label - label at top left that shows the current pick
        self.pick_label = tk.Label(self.root, text=f"Pick: {self.current_pick}")
        self.pick_label.pack(side="top", anchor="w")
        
        # creates the scrollable lists of players
        self.create_widgets()
        
        # creates the drafted players label - showing who you have drafted
        self.drafted_label = tk.Label(self.root, text="Drafted: \n")
        self.drafted_label.pack(side="top", anchor="e")
        
        # creates the tiers tab
        self.tier_tab=tk.Toplevel(self.root)
        self.tier_tab.title("Player Tiers")
        self.tier_tab.configure(bg="white")
        # creates the tiers
        self.create_tiers(self.tier_tab)
        
    ###############################################################
        
    # creates the scrollable lists of players
    def create_widgets(self):
        self.listboxes = {}

        # create a the draft button
        draft_button = tk.Button(self.root, text="Draft Player", command=self.draft_player)
        draft_button.pack(side="top", anchor="n")
        
        # create a frame for each position
        for pos in self.positions:
            # gets list of players at each position
            players = self.df[self.df["POS"] == pos]["Player"].tolist()
            # creates the listbox for each position
            self.create_player_list(pos, players)
    
    # creates the listbox for each position             
    def create_player_list(self, pos, players):
        # sort players in position by pos_rank
        players = sorted(players, key=lambda x: int(self.df.loc[(self.df["Player"] == x) & (self.df["POS"] == pos), "pos_rank"].iloc[0]))
        # create a frame for each position
        frame = tk.Frame(self.root)
        label = tk.Label(frame, text=f"{pos}s:")
        label.pack(side="top")
        listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        # add each player to the listbox - pos_rank: player
        for player in players:
            pos_rank = int(self.df.loc[(self.df["Player"] == player) & (self.df["POS"] == pos), "pos_rank"].iloc[0])
            player_with_rank = f"{pos_rank}: {player}"
            listbox.insert(tk.END, player_with_rank)
        
        # add the listbox to the frame
        listbox.pack(side="top")
        frame.pack(side="left", padx=10)
        self.listboxes[pos] = listbox

    ###############################################################

    def create_tiers(self, tier_tab):
        # delete all widgets in the frame - so that when a player is drafted, you update the tiers with a fresh canvas
        for widget in tier_tab.winfo_children():
            widget.destroy()
        
        # create a canvas for the tiers - scroll region needs to be long enough to see all players, width listed works for 6 positions
        self.canvas = Canvas(tier_tab, scrollregion=(0, 0, 1150, 1800), width=1025, height=300, bg="white")
        self.canvas.pack(side="left", fill="both", expand=True)

        # create scrollbar for canvas
        scrollbar = Scrollbar(tier_tab, orient=VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=scrollbar.set)

        # create frame for canvas
        frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=frame, anchor="nw")

        # create the tiers list for each position
        for idx, position in enumerate(self.positions):
            # get the players at each position
            position_df = self.dfog[self.dfog['Pos'] == position]
            # get the unique tiers at each position
            unique_tiers = position_df['Cluster'].unique()

            # start with the position label
            position_label = tk.Label(frame, text=f"{position}", bg="black", fg = 'white', font="Helvetica 18 bold")
            position_label.grid(row=0, column=idx, padx=10, sticky="n")

            # create a label for each player in each tier
            for tier in unique_tiers:
                # get the players in each tier
                tier_players = position_df[position_df['Cluster'] == tier]['Player'].tolist()
                # go through the players from the bottom of the tier to the top, adding them with newlines on top
                # if you add the players from the top to the bottom, the bottom player's label will cover the top player's label
                # but you need to add each player individually, so that you can change the font color if they are drafted
                # this is why we add each player with decreasing newlines instead of adding all the players with one label
                n = len(tier_players)
                # reverse the tier order
                tier_players = tier_players[::-1]
                newlines = ""
                
                # create a label for each player in the tier
                for player_name in tier_players:
                    font_style = "Helvetica 13 bold"
                    fg = "black"
                    # lose a newline for each player
                    newlines = "\n"*(n+1)
                    n-=1
                    
                    # if the player has been drafted by you, change the font color to green and still bold
                    if player_name in self.drafted_players:
                        fg = "green"
                    # else if the player has been drafted by someone else, change the font color to gray and unbolded
                    elif player_name  in self.total_drafted:
                        fg = "gray"  # Change font color to blue for drafted players
                        font_style = "Helvetica 13"
                    
                    # create the label for the player - as a spacing preference, we want there to be a newline between 
                    # the last player in the tier and the start of the next tier label
                    if n == len(tier_players)-1:
                        tier_label = tk.Label(frame, text=f"{newlines}{player_name}\n", bg="white", font=font_style, fg=fg)
                        tier_label.grid(row=tier, column=idx, padx=10, sticky="n")
                    else:
                        tier_label = tk.Label(frame, text=f"{newlines}{player_name}", bg="white", font=font_style, fg=fg)
                        tier_label.grid(row=tier, column=idx, padx=10, sticky="n")
                
                # create the label for the tier        
                tier_label = tk.Label(frame, text=f"TIER {tier}:", bg="white", font="Helvetica 13 bold underline")
                tier_label.grid(row=tier, column=idx, padx=10, sticky="n")
    
    ###############################################################
    
    # draft a player
    def draft_player(self):
        # get the selected player
        selected_player = self.get_selected_player()
        # if a player is selected, i.e. someone didn't just click the button draft the player
        if selected_player:
            # get the player's name, without the rank
            player_split = selected_player.split(": ")[1]

            # Because the model looks at what players will be available at the next pick
            # We need to add to the ADP of players when someone projected to go before them is drafted
            # Otherwise players who's ADP is before your pick but are still available won't be taken into account
            for i in self.df.index:
                if self.df.loc[i, "Rank"] < self.df.loc[(self.df["Player"] == player_split), "Rank"].iloc[0]:
                    self.df.loc[i, "Rank"] += 1
            
            # If the player drafted was on your pick
            if self.current_pick in self.picks:
                # remove this draft pick from your list of picks
                self.picks.remove(self.current_pick)
                # get the position of the player drafted
                position = self.df[self.df["Player"] == player_split]["POS"].iloc[0]
                # add this player to the drafted players list, this will get updated and show on the right
                self.drafted_players += f"{self.current_pick}: {player_split} - {position}\n"
                # now that you have drafted a player, you need to adjust the required number of players you have left
                # this could be a starter or a bench player and depends on the position of the player drafted
                if position == "QB" and self.qb_starter > 0:
                    self.qb_starter -= 1
                elif position == "QB":
                    self.qb_bench -= 1
                elif position == "RB" and self.rb_starter > 0:
                    self.rb_starter -= 1
                elif position == "WR" and self.wr_starter > 0:
                    self.wr_starter -= 1
                elif position == "TE" and self.te_starter > 0:
                    self.te_starter -= 1
                elif position == "K":
                    self.kicker -= 1
                elif position == "DST":
                    self.dst -= 1
                # i have it set up so that a TE is not a flex player, but you can change this if you want
                # i just think would a second TE ever be your flex
                elif (position == "RB" or position == "WR") and self.flex_starter > 0:
                    self.flex_starter -= 1
                    # my preference - if you drafted an RB for your flex, you need one less RB on your bench
                    if position == "RB":
                        self.wr_bench += 1
                        self.rb_bench -= 1
                elif position == "RB":
                    self.rb_bench -= 1
                elif position == "WR":
                    self.wr_bench -= 1
                    
            # now that you have potentially adjusted the number of players you need to draft
            # remove the player from the listbox
            self.remove_player(selected_player)
            # drop the drafted player from the dataframe
            self.df = self.df[self.df["Player"] != player_split]
            # reget the projected points per pick with the new dataframe and picks
            self.points_per_pick = self.ppp(self.df, self.picks)
            # add the player to the total drafted list
            self.total_drafted.append(player_split)
            # update the tiers
            self.create_tiers(self.tier_tab)
                    
            # add one to the current pick
            self.current_pick += 1 
            
            # if you are now on your pick, run the optimization
            if self.current_pick in self.picks:  
                optimization_results = self.run_optimization()
                # update the results with the Best pick
                self.update_results(optimization_results)
            else:
                # if you are not on your pick, tell the user how many picks until their next pick
                self.update_results( f"Your Next Pick: {self.picks[0]}, is up in {self.picks[0]-self.current_pick} picks.")
            
            # if you have drafted all your players, the draft is over
            if len(self.picks) == 0:
                self.result_label["text"] = "Draft is over"
                

    # get the selected player from the listboxes
    def get_selected_player(self):
        for pos, listbox in self.listboxes.items():
            if listbox.curselection():
                selected_player = listbox.get(listbox.curselection())
                return selected_player
        return None

    # remove the player from the listbox and add them to the drafted players list
    def remove_player(self, player):
        # split the player name from the rank, get the position, and the listbox
        player_split = player.split(": ")[1]
        position = self.df[self.df["Player"] == player_split]["POS"].iloc[0]
        listbox = self.listboxes[position]
        # find the index of the player in the listbox and delete them
        index = listbox.get(0, tk.END).index(player)
        listbox.delete(index)
    
    ###############################################################
    
    # run the optimization
    def run_optimization(self):
        # maximization problem
        m = LpProblem('draft', LpMaximize)
        # get the number of rows and columns from the points per pick matrix
        # rows are the number of picks left, columns are the number of positions
        rows = len(self.points_per_pick)
        cols = len(self.points_per_pick[0])
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
        m+= lpSum([selected_starter[i][0] for i in range(rows)]) == self.qb_starter, 'qb_starter'
        m+= lpSum([selected_bench[i][0] for i in range(rows)]) == self.qb_bench, 'qb_bench'
        # sets the weighting, x is 20 if the player is a starter, 1 if bench, 0 if neither
        for i in range(rows):
            m+= x[i][0] == 16*selected_starter[i][0] + selected_bench[i][0], f'qb_weighting{i}'
        
        # same as before, except an rb can be a flex, so the amound of starting rbs can waver
        m+= lpSum([selected_starter[i][1] for i in range(rows)]) >= self.rb_starter, 'rb_starter'
        m+= lpSum([selected_starter[i][1] for i in range(rows)]) <= self.rb_starter+self.flex_starter, 'rb_starter_flex'
        m+= lpSum([selected_bench[i][1] for i in range(rows)]) == self.rb_bench, 'rb_bench'
        for i in range(rows):
            m+= x[i][1] == 16*selected_starter[i][1] + 3*selected_bench[i][1], f'rb_weighting{i}'
        
        # wrs same as rbs      
        m+= lpSum([selected_starter[i][2] for i in range(rows)]) >= self.wr_starter, 'wr_starter'
        m+= lpSum([selected_starter[i][2] for i in range(rows)]) <= self.wr_starter+self.flex_starter, 'wr_starter_flex'
        m+= lpSum([selected_bench[i][2] for i in range(rows)]) == self.wr_bench, 'wr_bench'
        for i in range(rows):
            m+= x[i][2] == 16*selected_starter[i][2] + 3*selected_bench[i][2], f'wr_weighting{i}'
            
        # for flex position, it can be a rb or wr, so we just need the total wr/rb starters to be correct, wherever the flex comes from
        m+= lpSum([selected_starter[i][2] for i in range(rows)])+lpSum([selected_starter[i][1] for i in range(rows)]) == self.rb_starter+self.flex_starter+self.wr_starter, 'flex_starter'
            
        # TE
        m+= lpSum([selected_starter[i][3] for i in range(rows)]) == self.te_starter, 'te_starter'
        m+= lpSum([selected_bench[i][3] for i in range(rows)]) == 0, 'te_bench'
        for i in range(rows):
            m+= x[i][3] == 16*selected_starter[i][3]+selected_bench[i][3], f'te_weighting{i}'
        
        # K - no bench kickers
        m+= lpSum([selected_starter[i][4] for i in range(rows)]) == self.kicker, 'kicker'
        m+= lpSum([selected_bench[i][4] for i in range(rows)]) == 0, 'kicker_bench'
        for i in range(rows):
            m+= x[i][4] == 16*selected_starter[i][4], f'kicker_weighting{i}'
        
        # DST - no bench DST
        m+= lpSum([selected_starter[i][5] for i in range(rows)]) == self.dst, 'dst'
        m+= lpSum([selected_bench[i][5] for i in range(rows)]) == 0, 'dst_bench'
        for i in range(rows):
            m+= x[i][5] == 16*selected_starter[i][5], f'dst_weighting{i}'

        # Each round, only one player can be selected
        for i in range(rows):
            m += lpSum(selected_starter[i])+lpSum(selected_bench[i]) == 1, f'round{i}'

        # Objective function: Maximize the sum of selected values
        # which is the weighted sum of the points per pick
        m += lpSum(x[i][j] * self.points_per_pick[i][j] for i in range(rows) for j in range(cols))

        # Solve the problem and suppress output
        m.solve(PULP_CBC_CMD(msg=0))

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
                        to_draft = self.df[self.df["Projection"] == self.df.loc[self.df['POS'] == pos_to_draft]['Projection'].max()]['Player'].iloc[0]
                        # return the best player available at that position
                        return f"BEST PICK: {to_draft}"

        else:
            # if no optimal solution is found, return this
            return "No optimal solution found"                                         
    
    # update labels after each pick                         
    def update_results(self, results):
        # Update the result label - bottom
        self.result_label.config(text=results)
        # update current pick
        self.pick_label.config(text=f"Pick {self.current_pick}")
        # update your drafted players
        self.drafted_label.config(text=f"Drafted \n {self.drafted_players}")
        
    ##############################################################################################################

    # gets all draft picks for a drafter from the number of teams in the league, their slot, and the num of rounds
    def draft_picks(self,teams,slot,rds):
        picks = []
        for i in range(1,rds+1):
            for j in range(1,teams+1):
                if j == slot and i % 2 == 1:
                    picks.append(((i-1)*teams)+j)
                elif j == teams - slot + 1 and i % 2 == 0:
                    picks.append(((i-1)*teams)+j)

        return picks

    # gets the points per pick for each position
    def ppp(self,df, picks):
        # initialize points per pick array, rows = # of picks, cols = # of positions
        points_per_pick = [[0 for i in range(len(self.positions))] for j in range(len(picks))]
        for i in range(len(picks)):
            # if it's your current pick, get the max points available for each position
            if i == 0:
                max_qb_pts = (df.loc[df['POS'] == 'QB'])['Projection'].max()
                max_rb_pts = (df.loc[df['POS'] == 'RB'])['Projection'].max()
                max_wr_pts = (df.loc[df['POS'] == 'WR'])['Projection'].max()
                max_te_pts = (df.loc[df['POS'] == 'TE'])['Projection'].max()
                max_k_pts = (df.loc[df['POS'] == 'K'])['Projection'].max()
                max_def_pts = (df.loc[df['POS'] == 'DST'])['Projection'].max()
            # if it's not your current pick, i.e. you're forecasting out
            # find the players expected to be available at each future pick by using the ADP
            # and take an average of the top 2 player projections at each position
            else:
                max_qb_pts = (df.loc[df['POS'] == 'QB'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(2)['Projection'].mean()
                max_rb_pts = (df.loc[df['POS'] == 'RB'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(3)['Projection'].mean()
                max_wr_pts = (df.loc[df['POS'] == 'WR'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(3)['Projection'].mean()
                max_te_pts = (df.loc[df['POS'] == 'TE'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(2)['Projection'].mean()
                max_k_pts = (df.loc[df['POS'] == 'K'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(2)['Projection'].mean()
                max_def_pts = (df.loc[df['POS'] == 'DST'].loc[df['Rank'] >= picks[i]]).sort_values(by='Projection',ascending=False).head(2)['Projection'].mean()
            
            # assign the max points for each position to the points per pick array
            points_per_pick[i][0] = max_qb_pts
            points_per_pick[i][1] = max_rb_pts
            points_per_pick[i][2] = max_wr_pts
            points_per_pick[i][3] = max_te_pts
            points_per_pick[i][4] = max_k_pts
            points_per_pick[i][5] = max_def_pts
                
        return points_per_pick

##############################################################################################################

def main():
    # read in the csv - I used FantasyPros stat projections that I used to create 
    # fantasy point projections for each player depending on my league settings
    # I merged this with ADP FantasyPros data
    # I also clustured players into tiers based on their projections
    # replace with exact file``
    df = pd.read_csv('/Users/zachwayne/Documents/GitHub/Fantasy-Football-Optimizer/Final/2023_draft.csv')

    root = tk.Tk()
    app = PlayerDraftApp(root, df)
    root.mainloop()

if __name__ == "__main__":
    main()
