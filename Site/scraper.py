import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium import webdriver 
from selenium.webdriver.common.by import By
import time

class ESPNManager:
    def __init__(self):
        self.driver = None

    def launch_ESPN(self, browser):
        if browser == 'chrome':
            self.driver = webdriver.Chrome()
        elif browser == 'firefox':
            self.driver = webdriver.Firefox()
        else:
            return 'Please select a valid browser'
        
        self.driver.get('https://www.espn.com/fantasy/football/')
        return 'ESPN launched successfully'

    def scrape_ESPN(self):
        dropdown_element = self.driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/section/div/div[2]/main/div/div/div[3]/div[1]/div[1]/div[2]/div[1]/div/select')

        # Create a Select object
        dropdown = Select(dropdown_element)
        teams = dropdown.options
        table = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/section/div/div[2]/main/div/div/div[3]/div[1]/div[1]/div[2]/div[2]/div/div/div/div/div[2]/table")
        roster_size = len(table.find_elements(By.TAG_NAME, "tr")) - 1
        # roster is df where column names are team names and rows are roster requirements
        positions = []
        uniq_num = 0
        roster = pd.DataFrame()
        for i in range(len(teams)):
            dropdown.select_by_index(i)
            team_df = pd.DataFrame(columns=["Player", "Position"])
            for j in range(1, roster_size + 1):
                team_ele = self.driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/section/div/div[2]/main/div/div/div[3]/div[1]/div[1]/div[2]/div[2]/div/div/div/div/div[2]/table/tbody/tr[{j}]")
                # get the second time it says ("tag name","td")
                try:
                    element = self.driver.find_elements(By.CSS_SELECTOR, ".jsx-2810852873.table--cell.player-column")[j]
                    player = element.get_attribute("title")
                    if player is None or player == "":
                        player = " "
                except:
                    player = " "
                position_ele = team_ele.find_element(By.TAG_NAME, "td")
                team_df.loc[j] = [player, position_ele.text]
                if i == 0:
                    positions.append(position_ele.text + str(uniq_num))
                    uniq_num += 1
            roster[teams[i].text] = team_df["Player"]
        # make last column positions
        roster["Positions"] = positions
        print(roster)
        return roster.to_json()
    
    def scrape_FP(self):
        self.driver.find_element(By.XPATH, '//*[@id="liDraftBoard"]/a').click()
        self.driver.find_element(By.XPATH, '/html/body/div[1]/div[8]/div[2]/div/div[2]/section[2]/vue-draft-board-page-header/header/div[2]/div/div/button').click()
        self.driver.find_element(By.XPATH, '/html/body/ul/li[2]/button').click()
        table = self.driver.find_element(By.XPATH, '//*[@id="draftroom"]/div/div[2]/section[2]/vue-draft-board/div/table')
        rows = table.find_elements(By.TAG_NAME, "tr")
        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            cols = [ele.text.strip() for ele in cols]
            # get 0 and 1 from split on \n
            data.append([ele for ele in cols if ele])
        df = pd.DataFrame(data)
        df = df.drop(0, axis=0)
        for i in range(len(df)):
            for j in range(len(df.columns)):
                if '\n' in df.iloc[i,j] and len(df.iloc[i,j].split('\n')) > 2:
                    df.iloc[i,j] = df.iloc[i,j].split('\n')[0]+" "+ df.iloc[i,j].split('\n')[1]
                else:
                    df.iloc[i,j] = " "
        self.driver.find_element(By.XPATH, '/html/body/div[1]/div[8]/div[3]/vue-left-side-panel-nav/nav/ul/li[2]/a').click()
        starters = self.driver.find_elements(By.XPATH, '/html/body/div[1]/div[8]/div[3]/div/vue-single-team-roster/section/div[1]/div')
        bench = self.driver.find_elements(By.XPATH, '/html/body/div[1]/div[8]/div[3]/div/vue-single-team-roster/section/div[2]/div')
        pos = starters + bench
        uniq_num = 1
        positions = []
        for j in range(len(pos)):
            p = pos[j]
            position = p.find_element(By.XPATH, 'div/div[1]').text
            if position == "BN" or j >= len(starters):
                position = "BE"
            if position == "FLX":
                position = "FLEX"
            positions.append(position + str(uniq_num))
            uniq_num += 1
        df["Position"] = positions
        return df.to_json()

    def scrape_ESPN2(self):
        title = self.driver.find_element(By.XPATH, '//*[@id="news-feed"]/section[1]/section[1]/a/div/div[3]/h2').text
        return title