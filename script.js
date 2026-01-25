
async function chargerDonnees() {
    const reponse = await fetch('stats_groupe.json');
    const donnees = await reponse.json();
    
    const conteneur1 = document.getElementById('player-panel');

    donnees.finalList.forEach(joueur => {
        // 1. Extraire les infos simples
        const nom = joueur.player_info.name;
        const niveau = joueur.player_info.level;
        const photo = joueur.player_info.profilePicture;
        const rank = joueur.player_info.rank;
        const playerTopChamp = joueur.masteries[0].champImageUrl;
        // 3. Créer la div (exemple)
        const card = document.createElement('div');
        const headerCard = document.createElement('div');
        const sectionStats = document.createElement('div');
        const masteriesDiv = document.createElement('div');
        const recentGamesDiv = document.createElement('div');
        const matchMoyDiv = document.createElement('div');


        card.className = 'player-card';

        headerCard.className = 'header-card';
        headerCard.innerHTML = `
            <img src="${photo}" alt="Profile Picture" class="profile-pic">
            <div class="player-info">
            <h2>${nom.toUpperCase()}</h2>
                <div class="level-rank">
                <p class="level">LVL ${niveau}</p>
                <p class="rank">${rank}</p>
                </div>
            </div>
        `;

        headerCard.style.backgroundImage = `linear-gradient(rgba(32, 32, 32, 0.6), rgba(32, 32, 32, 0.65)),url('${playerTopChamp}')`;
        headerCard.style.backgroundSize = 'cover';

        sectionStats.className = 'section-stats';
        masteriesDiv.className = 'masteries-div';
        masteriesDiv.innerHTML = `<h3>MASTERIES</h3>`;

        // 4. Ajouter les statistiques
        for(let i = 0; i < 5; i++) {
            const mastery = joueur.masteries[i];
            const masteryItem = document.createElement('div');
            masteryItem.className = 'mastery-item';
            masteryItem.innerHTML = `
                <img src="https://ddragon.leagueoflegends.com/cdn/16.2.1/img/champion/${mastery.name}.png" alt="${mastery.name}" class="champ-pic">
                <div class="mastery-text">
                    <p class="champ-name">${mastery.name}</p>
                    <p class="champ-mastery">${(mastery.points/1000).toFixed(0)}K pts</p>
                </div>
            `;
            masteriesDiv.appendChild(masteryItem);
        };

        sectionStats.appendChild(masteriesDiv);

        recentGamesDiv.className = 'recent-games-div';
        recentGamesDiv.innerHTML = `<h3>RECENTS GAMES</h3>`;

        // 5. Ajouter les parties récentes

        let meilleurRole = {};
        let meilleurChamp = {};
        
        Object.values(joueur.match_report.champions).forEach(game => {
            if (!meilleurRole[game.role]) {
                meilleurRole[game.role] = game.games;
            } else {
                meilleurRole[game.role] += game.games;
            }
            if (!meilleurChamp[game.name]) {
                meilleurChamp[game.name] = game.games;
            }
            nombresDeGames = game.games;
            const gameItem = document.createElement('div');
            gameItem.className = 'game-item';
            gameItem.innerHTML = `
                <img src="https://ddragon.leagueoflegends.com/cdn/16.2.1/img/champion/${game.name}.png" alt="${game.champion_name}" class="game-champ-pic">
                <div class="game-text">
                    <p class="game-champ-name">${game.name} </p>
                    <p class="game-stats-text">KDA: ${(game.kills/nombresDeGames).toFixed(0)}/${(game.deaths/nombresDeGames).toFixed(0)}/${(game.assists/nombresDeGames).toFixed(0)} | CS : ${(game.cs/nombresDeGames).toFixed(0)}</p>
                    <p class="game-stats-text">Games: ${nombresDeGames}</p>
                </div>
            `;
            recentGamesDiv.appendChild(gameItem);
        });
        meilleurRole = Object.keys(meilleurRole).reduce((a, b) => meilleurRole[a] > meilleurRole[b] ? a : b);

        const listeTriee = Object.entries(meilleurChamp).sort(([, scoreA], [, scoreB]) => scoreB - scoreA); // Tri décroissant (du plus grand au plus petit)
        console.log(listeTriee);

        sectionStats.appendChild(recentGamesDiv);

        matchMoyDiv.className = 'match-moy-div';
        // prepare safe pick values (handle cases where there are fewer than 3 entries)
        const totalMatches = joueur.match_report.total_matches || 1;
        const pick1 = listeTriee[0] || ['N/A', 0];
        const pick2 = listeTriee[1] || ['N/A', 0];
        const pick3 = listeTriee[2] || ['N/A', 0];
        const pct = (count) => ((count / totalMatches) * 100).toFixed(0);

        matchMoyDiv.innerHTML = `
            <div class="match-moy-header">
                <h3>MAIN ROLE : ${meilleurRole.toUpperCase()}</h3>
                <img src="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/svg/position-${meilleurRole.toLowerCase()}-light.svg" alt="${meilleurRole}" class="role-pic">
            </div>
            
            <p class="match-moy-text">Games Played: ${joueur.match_report.total_matches}</p>
            <p class="match-moy-text">Win Rate: ${(joueur.match_report.winrate_global).toFixed(0)}%</p>
            <p class="match-moy-text">GOLD: ${(joueur.match_report.avg_gold).toFixed(0)}</p>
            <p class="match-moy-text">CS: ${(joueur.match_report.avg_cs).toFixed(0)}</p>

            <h3>PICK PROBABILITIES</h3>
            <p class="match-moy-text">1. ${pick1[0]} : ${pct(pick1[1])}%</p>
            <p class="match-moy-text">2. ${pick2[0]} : ${pct(pick2[1])}%</p>
            <p class="match-moy-text">3. ${pick3[0]} : ${pct(pick3[1])}%</p>

        `;

        sectionStats.appendChild(matchMoyDiv);
        
        

        card.appendChild(headerCard);

        card.appendChild(sectionStats);
        
        // Ajouter la carte au conteneur
        conteneur1.appendChild(card);
        
    });
}

chargerDonnees();