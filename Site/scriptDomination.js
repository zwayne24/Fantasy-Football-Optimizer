document.addEventListener("DOMContentLoaded", () => {
    let currentTeamIndex = 0;
    let settings = {};
    let teams = [];
    let draftedPlayers = {};
    let done = false;

    const teamList = document.getElementById("team-list");
    const availablePlayersLists = {
        overall: document.getElementById("available-players-overall"),
        QB: document.getElementById("available-players-QB"),
        RB: document.getElementById("available-players-RB"),
        WR: document.getElementById("available-players-WR"),
        TE: document.getElementById("available-players-TE"),
        K: document.getElementById("available-players-K"),
        DST: document.getElementById("available-players-DST"),
    };
    const draftedPlayersList = document.getElementById("drafted-players");
    const launchBtn = document.getElementById("launch-btn");
    const connectBtn = document.getElementById("connect-btn");
    const optimizeBtn = document.getElementById("optimize-btn");
    const teamSelect = document.getElementById("team-select");
    const browserSelect = document.getElementById("browser-select");
    const flashMessage = document.getElementById("flash-message-ESPN");
    const tabLinks = document.querySelectorAll(".tab-link");
    connectBtn.addEventListener('click', async function(event) {
        event.preventDefault();  // Prevent the default form submission behavior
        await connectToESPN();
    });
    optimizeBtn.addEventListener("click", optimize);
    launchBtn.addEventListener("click", launchDriver);
    teamSelect.addEventListener("change", teamSelectChange);

    tabLinks.forEach(tab => {
        tab.addEventListener("click", () => {
            tabLinks.forEach(link => link.classList.remove("active"));
            tab.classList.add("active");
            const tabContent = tab.dataset.tab;
            document.querySelectorAll(".tab-content").forEach(content => {
                content.classList.remove("active");
            });
            availablePlayersLists[tabContent].classList.add("active");
            highlightPlayerIfSelected(tabContent);
        });
    });

    async function connectToESPN() {
        const recommendedPlayer = document.querySelector(`#Recommendation`);
        recommendedPlayer.textContent = ``;
        try {
            const response = await fetch('http://127.0.0.1:5000/scrape-ESPN', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                })
            });
            
            if (!response.ok) {
                showFlashMessage("Only press connect once the ESPN draft room is open in your launched window", "long");
                throw new Error('Network response was not ok');
            }
            done = false;    
            const result = await response.json();
            console.log(result);
            teams = Object.keys(result);
            settings = result[teams[teams.length - 1]];
            // remove numbers from settings
            for (let key in settings) {
                if (settings.hasOwnProperty(key)) {
                    settings[key] = settings[key].replace(/[0-9]/g, '');
                }
                if (settings[key].includes('D/ST') || settings[key].includes('DEF')) {
                    settings[key] = 'DST';
                }
                if (settings[key].includes('WR/TE')) {
                    settings[key] = 'FLEX';
                }
            }
            settings['WR'] = 0
            settings['TE'] = 0
            console.log(settings);
            //pickData = remove first team from result
            delete result[teams[teams.length - 1]];
            teams = Object.keys(result);
            picksData = result;
            return initialize({ settings, picksData });
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function initialize({ settings, picksData }) {
        if (settings) {
            const teams = Object.keys(picksData);
            
            teamList.innerHTML = '';
            
            if (teamSelect.length == 0) {
                teamSelect.innerHTML = '';
            }

            teams.forEach((team, index) => {
                const teamItem = document.createElement("li");
                teamItem.textContent = team;
                if (index === currentTeamIndex) {
                    teamItem.classList.add("active");
                }
                teamList.appendChild(teamItem);

                const option = document.createElement("option");
                option.value = team;
                option.textContent = team;
                if (teamSelect.length < teams.length) {
                    teamSelect.appendChild(option);
                }
            });
            adjustCurrentPick(picksData);
            // Initialize an empty object to store the counts
            for (let team in picksData) {
                if (picksData.hasOwnProperty(team)) {
                    let playerList = picksData[team];
                    // Iterate over each player in the team
                    for (let playerIndex in playerList) {
                        if (playerList.hasOwnProperty(playerIndex)) {
                            let playerName = playerList[playerIndex];
                            let position = settings[playerIndex];
                            // Add position to player
                            picksData[team][playerIndex] = {
                                name: playerName,
                                position: position
                            };
                        }
                    }
                }
            }            

            let formattedTeams = {};
            for (let teamName in picksData) {
                if (picksData.hasOwnProperty(teamName)) {
                    let players = [];
                    for (let playerIndex in picksData[teamName]) {
                        if (picksData[teamName].hasOwnProperty(playerIndex)) {
                            let player = {
                                "Player": picksData[teamName][playerIndex].name,
                                "Pos": picksData[teamName][playerIndex].position
                            };
                            players.push(player);
                        }
                    }
                    formattedTeams[teamName] = players;
                }
            }

            let counts = {};
            // Loop through the keys of the json object
            for (let key in settings) {
                if (settings.hasOwnProperty(key)) {
                    let item = settings[key];
                    // If the item exists in counts, increment its count; otherwise, initialize it to 1
                    counts[item] = counts[item] ? counts[item] + 1 : 1;
                }
            }
            settings = Object.assign(settings, counts);
            console.log(settings);
            draftedPlayers = formattedTeams;
            if (picksData.length >= settings.teams * (settings.QB + settings.RB + settings.WR + settings.TE + settings.K + settings.DST + settings.FLEX + settings.BE)) {
                done = true;
            }

            // need to add position to json for each player based on settings
            displayRosterRequirements(settings);
            const availablePlayers = await fetchAvailablePlayers();
            populatePlayers(availablePlayers);
        } else {
            console.error('Error: Could not find number of teams in API response');
        }
    }

    function highlightPlayerIfSelected(position) {
        const activePlayer = document.querySelector('#players-list li.active');
        if (activePlayer && activePlayer.textContent.includes(position)) {
            const playerName = activePlayer.textContent.split(' (')[0];
            highlightPlayer(playerName);
        }
    }

    async function launchDriver() {
        try {
            const response = await fetch('http://127.0.0.1:5000/launch-ESPN', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    browser: browserSelect.value,
                })
            });

            if (response.ok) {
                // response is string and not json
                const result = await response.text();
                showFlashMessage(result);
            } else {
                const errorResponse = await response.json();
                console.error('Error:', errorResponse);  // Handle the error response
                alert('Error launching ESPN: ' + errorResponse.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function fetchAvailablePlayers() {
        try {
            const playersData = await readCSVFiles();
            playersData.sort((a, b) => a.ADP - b.ADP);
    
            const availablePlayers = playersData.filter(player => {
                const playerNameParts = player.Player.replace(/\./g, '').split(' ').slice(0, 2).join(' ');
                for (const teamPlayers of Object.values(draftedPlayers)) {
                    if (teamPlayers.some(draftedPlayer => {
                        const draftedPlayerNameParts = draftedPlayer.Player.replace(/\./g, '').split(' ').slice(0, 2).join(' ');
                        return draftedPlayerNameParts === playerNameParts;
                    })) {
                        return false;
                    }
                }
                return true;
            });
            return availablePlayers;
        } catch (error) {
            console.error('Error fetching available players:', error);
            return [];
        }
    }    

    function populatePlayers(players) {
        Object.values(availablePlayersLists).forEach(list => list.innerHTML = '');
        players.forEach(player => {
            const playerItem = document.createElement("li");
            const teamText = player.Pos === 'DST' ? '' : ` - ${player.Team}`;
            playerItem.textContent = `${player.Player} (${player.Pos})${teamText}`;
            const vorp = document.createElement("span");
            vorp.classList = "vorp";
            vorp.textContent = ` FPTS: ${player.FPTS}`
            const adp = document.createElement("span");
            adp.classList = "adp";
            adp.textContent = `ADP: ${player.ADP}     |      `
            playerItem.appendChild(vorp);
            playerItem.appendChild(adp);
            availablePlayersLists.overall.appendChild(playerItem);
            availablePlayersLists[player.Pos].appendChild(playerItem.cloneNode(true));
        });
    }

    function adjustCurrentPick(picksData) {
        let totalPlayers = 0;
        for (const team in picksData) {
            if (picksData.hasOwnProperty(team)) {
                let count = 0;
                for (const player of Object.values(picksData[team])) {
                    if (player.trim() !== "") { // Check if player name is not empty or whitespace
                        count++;
                    }
                }
                totalPlayers += count;
            }
        }
        const round = Math.floor(totalPlayers / teams.length);
        currentTeamIndex = totalPlayers % teams.length;
        const isAscending = (round % 2 === 0);
        currentTeamIndex = isAscending ? currentTeamIndex : teams.length - currentTeamIndex - 1;
        highlightCurrentTeam();   
    }

    function highlightCurrentTeam() {
        const teamItems = document.querySelectorAll("#team-list li");
        teamItems.forEach(item => item.classList.remove("active"));
        teamItems[currentTeamIndex].classList.add("active");
    }

    async function optimize() {
        if (done) {
            showFlashMessage("Draft is complete!");
            return;
        }
        try {
            roster_settings = {
                slots_qb: settings.QB,
                slots_rb: settings.RB,
                slots_wr: settings.WR,
                slots_te: settings.TE,
                slots_k: settings.K,
                slots_def: settings.DST,
                slots_flex: settings.FLEX,
                slots_super_flex: 0,
                teams: teams.length,
                rounds: (settings.QB + settings.RB + settings.WR + settings.TE + settings.K + settings.DST + settings.FLEX + settings.BE)
            }
            showFlashMessage("Optimizing...may take up to 30 sec", 'long');
            const response = await fetch('http://127.0.0.1:5000/process-info-Domination', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    personal_team: currentTeamIndex+1,
                    roster_settings: roster_settings,
                    drafted_players: draftedPlayers,
                    personal_team_name: teams[currentTeamIndex]
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            highlightPlayer(result);
            const recommendedPlayer = document.querySelector(`#Recommendation`);
            recommendedPlayer.textContent = `Recommended Player: ${result}`;

            showFlashMessage("Done!");
        } catch (error) {
            console.error('Error:', error);
        }
    }

    function highlightPlayer(player) {
        const playerItems = document.querySelectorAll("#players-list li");
        playerItems.forEach(item => item.classList.remove("active"));
        playerItems.forEach(item => {
            if (item.textContent.includes(player)) {
                item.classList.add("active");
            }
        });
    }

    async function displayRosterRequirements(settings) {
        // make a dictionary from settings - i.e. how much each position shows up
        const rosterRequirements = document.createElement("div");
        rosterRequirements.classList.add("roster-requirements");
        // Helper function to create list items for each position
        function createPositionListItems(position, count, players = []) {
            let listItems = '';
            let playerIndex = 0;
            for (let i = 0; i < count; i++) {
                const player = players[playerIndex];
                if (player) {
                    listItems += `<li>${position}: ${player.Player} </li>`;
                    playerIndex++;
                } else {
                    listItems += `<li>${position}</li>`;
                }
            }
           
            return listItems;
        }
    
        // Get drafted players (assuming a global object draftedPlayers or a function to fetch them)
        // Example: const draftedPlayers = await getDraftedPlayers(draft_id);
    
        const selectedTeam = teamSelect.value; // Assume this is the team for which you want to display roster
        const teamDraftedPlayers = draftedPlayers[selectedTeam] || [];
    
        const positions = {
            'QB': settings.QB,
            'RB': settings.RB,
            'WR': settings.WR,
            'TE': settings.TE,
            'K': settings.K,
            'DST': settings.DST,
            'Flex': settings.FLEX,
            'Bench': settings.BE
        };
        console.log(positions);
        rosterRequirements.innerHTML = `
            <h3></h3>
            <ul>
                ${createPositionListItems('QB', positions.QB, teamDraftedPlayers.filter(p => p.Pos === 'QB'))}
                ${createPositionListItems('RB', positions.RB, teamDraftedPlayers.filter(p => p.Pos === 'RB'))}
                ${createPositionListItems('FLEX', positions.Flex, teamDraftedPlayers.filter(p => p.Pos === 'WR' || p.Pos === 'TE' || p.Pos === 'FLEX' || p.Pos === 'WR/'))}
                ${createPositionListItems('K', positions.K, teamDraftedPlayers.filter(p => p.Pos === 'K'))}
                ${createPositionListItems('DST', positions.DST, teamDraftedPlayers.filter(p => p.Pos === 'DST'))}
                ${createPositionListItems('BE', positions.Bench, teamDraftedPlayers.filter(p => p.Pos === 'BE'))}
            </ul>
        `;
        document.getElementById("drafted-players").innerHTML = "";
        document.getElementById("drafted-players").appendChild(rosterRequirements);
    }

    function showFlashMessage(message, type = 'short') {
        flashMessage.textContent = message;
        flashMessage.style.display = 'inline-block';
        if (type === 'short') {
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 1000);
        }
        else if (type === 'long') {
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 5000);
        }
    }

    function teamSelectChange(){
        draftedPlayersList.innerHTML = "";
        displayRosterRequirements(settings);
    }

    async function readCSVFiles() {
        // Array to store all player data from CSV files
        const allPlayersData = [];

        // Names of CSV files - 2024_Draft.csv in parent directory
        const csvFile = ['../2024_Draft.csv'];
        // Read each CSV file and extract 'Player', 'Team', and 'FPTS' columns
        const response = await fetch(csvFile);
        const text = await response.text();
        const csvData = Papa.parse(text, { header: true }).data;

        const filteredData = csvData.filter(player => player.Player.trim() !== '');

        // Extract and retain only the required columns
        const extractedData = filteredData.map(player => ({
            Player: player.Player.replace(/\./g, ''),
            Team: player.Team,
            // round to 2 decimal
            FPTS: player.Projection,
            Pos: player.Pos,
            ADP: player.Rank
        }));

        allPlayersData.push(...extractedData);
        

        return allPlayersData;
    }
});
