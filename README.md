# Fantasy Football Optimizer

This project is a fantasy football optimizer. It projects what caliber of players will be available 
at each of your picks, then finds the optimal way to fill your roster to maximize your projected points.

It has a GUI that allows you to cross off drafted players as you go along. On your turn, 
it tells you who you should pick.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

It uses python 3 and the following packages:

* pandas 
* pulp 
* tkinter
* scipy
* matplotlib
* flask

## Usage

It uses stat projections and ADP from fantasy pros.
You can find the data [here](https://www.fantasypros.com/nfl/projections/qb.php?week=draft) and [here](https://www.fantasypros.com/nfl/adp/overall.php).

You can download new data from the links above and put them in the `FantasyProsData` folder to keep 
the data up to date.

To run the program, first go into `FFO_DataSetup.ipynb`. Running through this notebook will create the
necessary data file for the optimizer to run. In this file you can specify your league's scoring system.
You also create the tiers for each position. This is done by using hierarchical clustering to group players.
It requires you to specify the number of tiers you want for each position. 

Once complete, you can run the optimizer by opening up indexDomination.html or indexStandard.html in a browser. 
In the file you just need to specify your the number of bench spots you want for each position. 

Make sure to run 'python app.py' in VSCode terminal first to start the server. Then launch the Selenium window and navigate to your ESPN 
draftroom. Click 'Connect' to scrape the draftroom and 'Optimize' to get the optimal pick recommendation. 

You can also use 'FantasyProsScrape.ipynb' to live scrape and give optimal picks for FantasyPros simulations.

