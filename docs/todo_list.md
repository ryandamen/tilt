Todo list
# Create checkbox with ctr + shift + C
# Mark checkbox with ctr +shift + enter

* [X] ~~*Replicate basic riotwatcher code*~~ [2020-12-24]
* [X] ~~*Access player info*~~ [2020-12-24]
* [X] ~~*Access match info*~~ [2020-12-24]
* [X] ~~*Retrieve last 100 matches from a player of a certain que*~~ [2020-12-26]
* [X] ~~*Check if the API key is valid*~~ [2020-12-27]
* [X] ~~*Create a function that calculates KDA and is able to handle 0 deaths*~~ [2021-01-24]
* [X] ~~*Retrieve the KDA of player from a single match, ranked queue*~~ [2021-02-03]
* [X] ~~*Retrieve the KDA of player from a multiple matches, ranked queue**~~ [2021-02-06]
* [ ] Retrieve the KDA of player from a single match, ranked queue based on time
* [ ] Retrieve the KDA of player from one season matchs, ranked queue
* [ ] Retrieve the KDA of player from one season matchs, ranked & normal queue
* [ ] Remove all games that are shorten then 5 minutes (presumed to be remake 3min +1 minute waiting and 30 seconds voting time remake vote start )
* [ ] take all matches that have been played with a maximum of 30 minutes in between games
* [ ] Calculate the season KDA of alnas per queue
* [ ] Plan next steps
* [ ] take last game per season
* [ ] take last games of the last patch per season
* [ ] Decide a home: A) submit as a conference or journal, and B) where
* [ ] Once home decided, add deadline to the to do list




Nicole tasks

Writing
* [ ] Write Abstract
* [ ] Write Intro
* [ ] Write Lit review / Theoretical background
* [ ] Write Method
* [ ] Write Results
* [ ] Write Discussion
* [ ] Proofread person 1
* [ ] Incorporate person 1 feedback
* [ ] Proofread person 2
* [ ] Incorporate person 2 feedback

Coding 
* [ ] Get summoner IDs & names by region, tier & division https://developer.riotgames.com/apis#league-exp-v4/GET_getLeagueEntries
    * [ ] fully collect dataset for Challenger (1 division, 1 pages)
    * [ ] fully collect dataset for Grandmaster (1 division, 4 pages)
    * [ ] Put it into a method so you can call it (def ... return ... )
* [ ] Get account ID by summoner ID or name https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerName
* [ ] Get matchlist by account ID https://developer.riotgames.com/apis#match-v4/GET_getMatchlist
    Can filter by the endTime and beginTime --> 	The end time to use for filtering matchlist specified as epoch milliseconds. If beginTime is specified, but not endTime, then endTime defaults to the the current unix timestamp in milliseconds (the maximum time range limitation is not observed in this specific case). If endTime is specified, but not beginTime, then beginTime defaults to the start of the account's match history returning a 400 due to the maximum time range limitation. If both are specified, then endTime should be greater than beginTime. The maximum time range allowed is one week, otherwise a 400 error code is returned.
