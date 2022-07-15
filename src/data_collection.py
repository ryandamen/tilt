# %% [markdown]
# # TILT - Teemo Induced Loss of Tranquility
# A research project to study main factors in inducing tilt.
#
# ONLY LOOKS AT THE PERSON STATS THEMSELVES
#

# %% [markdown]
# # Imports

# %%
# from collections import defaultdict
# TODO: maybe not have all those skleans and just import sklearn or use as to shorten them
from datetime import datetime
from pathlib2 import Path
from riotwatcher import LolWatcher, ApiError


from tenacity import retry, wait_random_exponential, retry_if_exception_type

import itertools
import datetime
# import time
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


# %% [markdown]
# # Functions

# %%
def touch(path):
    """
    Creates a file and directories in the path if it doesnt exists.

    Args:
        path (str): File path.
    Returns:
        None
    """
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    with open(path, mode="a"):
        pass


# %%
def drop_keys(dictionary, drop_keys):
    """
    Remove unwanted keys from a dictionary.

    Args:
        dict (dict): The dictionary to remove keys from.
        drop_keys (set): Keys to be removed.
    Returns:
        final_dict (dict): Dictionary without the drop_keys.
    """
    final_dict = {key: dictionary[key] for key in dictionary if key not in drop_keys}

    return final_dict

# %%
def overwrite(file_path):
    """
    Overwrite a file if it exists or offers to use a new file path

    Args:
        file_path (str): File path to a file
    Returns:
        None
    """
    while Path(file_path).exists():
        answer = input("""Enter "yes" to overwrite file, or enter new filepath""")
        if answer.upper() in ["Y", "YES"]:
            os.remove(file_path)
        else:
            file_path = answer
            touch(file_path)

# %%
def api_key(api_key_loc):
    """
    Read in the development API key from a file and checks if it is viable.

    Args:
        credentials (str): Name of json file containing the credentials.
    Returns:
        api_key (str): The API key.
    """

    # Keep requestion for a correct key or until canceled
    while True:
        with open(api_key_loc, "r") as credentials:
            creds = json.load(credentials)
            api_key = creds["dev_api_key"]
            lol_watcher = LolWatcher(creds["dev_api_key"])
            try:
                # Validate API key by using it to check server status
                lol_watcher.data_dragon.versions_all()
                # Break if key is functional
                break
            except ApiError as error:
                # If the current API key does not work input new one
                if error.response.status_code == 403:
                    new_api_key = input("API key is incorrect, enter correct key here.")
                    creds["dev_api_key"] = new_api_key
                    # Replace the old API key
                    with open(api_key_loc, "w") as json_data:
                        json.dump(creds, json_data)
    return api_key

# %%
def adj_patch_time(reg, patch_nr="now"):
    # TODO: add option to fill in time epoch instead of only patch nrs
    """
    Read the patch number and return the time adjusted for timezones.

    Args:
        reg (str): Official registered Riot server that hosts league of legends.
        patch_nr (str): League of legends update patch number.
            Defaults to "now" which is the current time.
    Returns:
        adj_time (long): Time in ms following the Coordinated Universal Time (UTC) format.
    """

    # Read patch data
    patch_loc = proj_dir / "data" / "patches.json"
    with open(patch_loc, "r") as in_file:
        patch_data = json.load(in_file)

    # Set the base utc time
    if patch_nr == "now":
        patch_time = int(datetime.utcnow().timestamp())
    else:
        for patch in patch_data["patches"]:
            if patch["name"] == patch_nr:
                patch_time = patch["start"]
    # Check if patch number is valid
    assert patch_time, f"Patch number: {patch_nr} is unknown"

    # Set the time shift
    try:
        reg_shifts = patch_data["shifts"][reg.upper()]
    except KeyError:
        # Check if region provided is valid
        raise KeyError(f"Region: {reg} is unknown")

    # Calculate time adjusted for the time shift of the region
    adj_time = patch_time + reg_shifts
    return adj_time

# %%
def trans_reg(reg_abbrv):
    """
    Translate a league of legends region into a region readable by riot watcher.

    Args:
        reg_abbrv (str): Abbreviation of a official registered Riot servers that
            hosts league of legends (e.g. euw1).
    Returns:
        rw_region (str): Riot Watcher region the reg_abbrv server falls under.
    """
    # Look up in the list what the riot watcher region is for the given region abbreviation
    regions_metadata = {"br1": "americas",
                        "eun1": "europe",
                        "euw1": "europe",
                        "jp1": "asia",
                        "kr": "asia",
                        "la1": "americas",
                        "la2": "americas",
                        "na1": "americas",
                        "oc1": "americas",
                        "tr1": "europe",
                        "ru": "europe"
                        }

    for reg, rw_reg in regions_metadata.items():
        if reg_abbrv.lower() == reg:
            rw_region = rw_reg

    return rw_region

# %%
@retry(wait=wait_random_exponential(multiplier=1, max=60),
       retry=retry_if_exception_type(ApiError))
def get_matches(reg, pid, s_time, e_time):
    """
    Retrieve match IDs from a summoner within a given timeframe.

    Args:
        reg (str): Abbreviation of a official registered Riot servers that
            hosts league of legends (e.g. euw1).
        pid (str): An Encrypted globally unique identifyer for a summoner.
        s_time (long): Start of a timeframe in (milli)seconds following
            the Coordinated Universal Time (UTC) format.
        e_time (long): end of a timeframe in (milli)seconds following
            the Coordinated Universal Time (UTC) format.
    Returns:
        matches (list): League of legends match IDs in chronological order
            starting with the most recent match.
    """

    # Retrieve all match ID's between two time points
    rw_reg = trans_reg(reg)
    matches = lol_watcher.match.matchlist_by_puuid(region=rw_reg,
                                                   puuid=pid,
                                                   start_time=s_time,
                                                   count=100,
                                                   queue=420,
                                                   end_time=e_time)

    # Geather more match IDs in case matches exceeds the standard limit of 100
    while len(matches) % 100 == 0 and len(matches) != 0:
        # Geather match details of earliest match
        match_deets = lol_watcher.match.by_id(rw_reg, matches[-1])
        # Start time of earliest match
        early_g_start = int(str(match_deets["info"]["gameCreation"])[:10])
        # Select 100 matches previous to early_g_start
        match_add = lol_watcher.match.matchlist_by_puuid(region=rw_reg,
                                                         puuid=pid,
                                                         start_time=s_time,
                                                         count=100,
                                                         queue=420,
                                                         end_time=early_g_start)
        if len(match_add) == 0:
            break
        else:
            matches.extend(match_add)

    return matches

# %%
@retry(wait=wait_random_exponential(multiplier=1, max=60),
       retry=retry_if_exception_type(ApiError))
def geather_data(puuid, matches):
    """
    Geather summoner data from a match and chronology data of the match.

    Args:
        puuid (str): An Encrypted globally unique identifyer for a summoner.
        matches (list): League of legends match IDs in chronological order
                        starting with the most recent match.
    Returns:
        df_matches_data (df): Data geathered from matches of a summoner.
    """

    comp_data = []
    # Geather match details
    for match_id in matches:
        reg = match_id.split("_")[0].lower()
        match_deets = lol_watcher.match.by_id(trans_reg(reg), match_id)

        # Collect time data
        time_info = {"gameCreation", "gameStartTimestamp"}
        time_data = dict((key, match_deets["info"][key]) for key in time_info)

        # Collect summoner data
        for game_info in match_deets["info"]["participants"]:
            # Mark the protagonist
            prota_stat = {"prota": False}
            if game_info["puuid"] == puuid:
                prota_stat = {"prota": True}
            # Combine the data data
            match_data = {"reg":reg, "match_id": match_id} | game_info | prota_stat | time_data
            comp_data.append(match_data)

    # Store all data in a dataframe
    df_matches = pd.DataFrame.from_dict(comp_data)

    # Add rest time between previous and next match as a base to filter on
    df_matches["game_end"] = df_matches.loc[:,["gameStartTimestamp", "timePlayed"]].sum(axis=1)
    df_matches["game_end_prev"] = df_matches["game_end"].shift(-10, fill_value=np.nan)
    df_matches["game_make_next"] = df_matches["gameCreation"].shift(10, fill_value=np.nan)
    df_matches["time_since_last"] = df_matches["gameCreation"] - df_matches["game_end_prev"]
    df_matches["time_till_next"] = df_matches["game_make_next"] - df_matches["game_end"]

    return df_matches

# %%
puuid = "qZHgkSP20VlVqICoXMoFpVDfFk8NV54naBnTqgPEZN6GYVdn-Zjo_dVKWYX0gNVXNscT2EtrVnAieQ"
game_ids = ["EUW1_5414939600","EUW1_5414956170","EUW1_5414912862","EUW1_5373474765","EUW1_5373418712","EUW1_5373451710","EUW1_5373326619","EUW1_5373235566","EUW1_5373148726","EUW1_5373075843","EUW1_5342677497","EUW1_5342672741","EUW1_5342645103","EUW1_5342510081","EUW1_5342462317"]

test_data = geather_data(puuid, game_ids)
# print(test.columns)

test_data
# test["puuid"]

# %%
matches_data = test_data
matches_data["idx"] = matches_data.index
df_prota = matches_data.loc[matches_data["prota"] == True]


print(df_prota["time_since_last"])
print(df_prota["time_since_last"].shift(-1))
print(df_prota["time_since_last"].shift(1))

# %%
def filt_matches(matches_data, max_rest, min_streak):
    """
    Filter matches based on rest time in between matches and number of matches played in a row.

    Args:
        matches_data (df): Data geathered from matches of a summoner.
        max_rest (int): Rest time in between matches in miliseconds e.g. 3600000 = 1 hour.
        min_streak (int): Minimum games played in a row with less then max_rest between.
    Returns:
        df_match_streak (df): Matches left over after filtered based on minimum subsequent matches within
            the maximum rest time in between the matches.
        df_match_nostreak (df): The matches filtered out based on minimum subsequent matches within
            the maximum rest time in between the matches.
    """

    # Filter for matches based on rest time below the max_rest time

    # Find games that were played in a streak by grouping based on matches played subsequently
    # Copy index to know where a empty line was inserted
    matches_data["idx"] = matches_data.index
    df_prota = matches_data.loc[matches_data["prota"] == True]
    # Add empty lines between groups to split them up
    indices = np.where(np.logical_or(df_prota["time_till_next"] >= max_rest,
                       np.isnan(df_prota["game_make_next"])))[0] * 10
    rows_ = dict.fromkeys(df_prota.columns.tolist(), np.nan)
    # Add empty lines
    matches_data = pd.DataFrame(np.insert(matches_data.values, [x for x in indices],
                                           values=list(rows_.values()),
                                           axis=0),columns=rows_.keys())

    # Temporarily store streak_id to know how big the groups are
    game_streak = matches_data["idx"].diff().ne(1).cumsum()
    matches_data["streak_id"] = matches_data.groupby(game_streak).ngroup()

    # Collect games that are higher then min_streak
    df_match_streak = (matches_data[matches_data["idx"]
                       .groupby(game_streak)
                       .transform("count") >= min_streak * 10])

    # Collect games that are lower then min_streak
    df_match_nostreak = (matches_data[matches_data["idx"]
                         .groupby(game_streak)
                         .transform("count") < min_streak * 10])

    return df_match_streak, df_match_nostreak

# %%

puuid = "qZHgkSP20VlVqICoXMoFpVDfFk8NV54naBnTqgPEZN6GYVdn-Zjo_dVKWYX0gNVXNscT2EtrVnAieQ"
game_ids = ["EUW1_5414939600", "EUW1_5373474765", "EUW1_5373418712", "EUW1_5373451710", "EUW1_5342672741"]


# beta = filt_matches(test_data,
#                     max_rest=settings["max_rest"],
#                     min_streak=3)
test, test2 = filt_matches(geather_data(puuid, game_ids),
                    max_rest=settings["max_rest"],
                    min_streak=3)
# test.loc[:,["game_start", "time_played", "game_end"]]
# print(beta.to_string())

# %%

for data, loc in zip(["streak_info", "nostreak_info"], ["streak_loc", "nostreak_loc"]):
    print(data, loc)

# %%
@retry(wait=wait_random_exponential(multiplier=1, max=60),
       retry=retry_if_exception_type(ApiError))
def get_summoner_data(regs, tiers, divs, sum_lim, p_patch, r_patch, max_rest, min_streak, streak_loc, nostreak_loc):
    """
    Get puuid's, tier and division, from all regions that are in ranks below master rank.

    Args:
        regs (list): Official registered Riot servers that hosts league of legends.
        tier (list): Tiers below Master rank.
        divs (list): Divisions in roman numerals.
        sum_lim (int): Maximum number of summoner ids to collect per region, tier and division.
        p_patch (str): A patch prior to then r_patch's patch.
        r_patch (str): A more recent patch then p_patch's patch.
        max_rest (int): Rest time in between matches in miliseconds e.g. 3600000 = 1 hour.
        min_streak (int): Minimum games played in a row with less then max_rest between.
        streak_loc (str): location to store match data of game not played in a streak.
        nostreak_loc (str): location to store match data of game played in a streak.
    Returns:
        None
    """

    for reg, tier, div in itertools.product(regs, tiers, divs):
        summs_div_streak = 0
        summs_div_no_streak = 0
        page_nr = 0
        # Keep adding new summoners until the summoner limit has been reached
        while summs_div_streak < sum_lim or summs_div_no_streak < sum_lim:
            page_nr += 1
            summs = lol_watcher.league.entries(reg, "RANKED_SOLO_5x5", tier, div, page_nr)
            # Look into data per summoner
            for sumo in summs:
                if summs_div_streak < sum_lim or summs_div_no_streak < sum_lim:
                    # Get PUUID
                    pid = lol_watcher.summoner.by_id(reg, sumo["summonerId"])["puuid"]

                    # Retrieve all match ID's between two time points
                    match_ids = get_matches(reg,
                                            pid,
                                            adj_patch_time(reg, p_patch),
                                            adj_patch_time(reg, r_patch))
                    # Skip summoner that has no matches in the given time frame
                    if not match_ids:
                        continue

                    # Geather match data of the summoner
                    match_info = geather_data(pid, match_ids)

                    # Add summoner rank information
                    cur_rank = f"{tier}_{div}"
                    match_info["rank"] = cur_rank

                    # Filter matches
                    streak_info, nostreak_info = filt_matches(match_info, max_rest, min_streak)

                    # Store match data in nostreak or streak database
                    if not streak_info.empty:
                        # Store streak data in a tsv file
                        file_true = streak_loc.exists()
                        streak_info.to_csv(streak_loc,
                                           header=not file_true,
                                           mode="a" if file_true else "w",
                                           sep="\t",
                                           index=False)
                        # Increase the streak summoner counter
                        summs_div_streak += 1

                    if not nostreak_info.empty:
                        # Store nonstreak data in a tsv file
                        file_true = streak_loc.exists()
                        nostreak_info.to_csv(nostreak_loc,
                                             header=not file_true,
                                             mode="a" if file_true else "w",
                                             sep="\t",
                                             index=False)
                        # Increase the nostreak summoner counter
                        summs_div_no_streak += 1


# %% [markdown]
# # Global variables and settings

# %%
# Directory locations

# Project folders
proj_dir = Path.cwd().parent

# Raw data storage
data_dir = proj_dir / "data"

# Out dir
out_dir = proj_dir / "out"

# Gobal variables

# Set API key
api_key_loc = data_dir / "dev_api_key.json"

# Enter API key
lol_watcher = LolWatcher(api_key(api_key_loc))

# Read user settings
settings_loc = proj_dir / "settings" / "config.json"
with open(settings_loc, "r") as settings_data:
    settings = json.load(settings_data)

# %% [markdown]
# # Data collection

# %%
# Retrieve the summoner info of n summoners per rank (tier and division)

streak_db_loc = data_dir / "summoner_data_streak_raw.tsv"
nostreak_db_loc = data_dir / "summoner_data_nostreak_raw.tsv"
# TODO: just for testing can be removed later mayeb
overwrite(streak_db_loc)
overwrite(nostreak_db_loc)

get_summoner_data(regs=settings["regions"],
                  tiers=settings["tiers"],
                  divs=settings['divisions'],
                  sum_lim=settings['summoner_limit'],
                  p_patch=settings["prior_patch"],
                  r_patch=settings["recent_patch"],
                  max_rest=settings["max_rest"],
                  min_streak=settings["min_streak"],
                  streak_loc=streak_db_loc,
                  nostreak_loc=nostreak_db_loc)
