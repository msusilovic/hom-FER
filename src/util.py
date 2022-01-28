from dataclasses import dataclass

GK = 'GK'
MID = 'MID'
DEF = 'DEF'
FW = 'FW'


@dataclass(unsafe_hash=True)
class Player:
    ID: int
    position: str
    name: str
    club: str
    points: int
    price: float


def parse_instance_csv(filepath):
    """
    Parses info of available players from a .csv file.

    :param filepath:    file with players info
    :return:            list of Player objects
    """
    instance = open(filepath, 'r', encoding='cp1252')
    players = []
    for line in instance.readlines():
        ID, position, name, club, points, price = line.strip().split(',')
        players.append(Player(int(ID), position, name, club, int(points), float(price)))
    instance.close()
    return players


def solution_to_string(starting_11, bench, filepath):
    """
    Converts solution of fantasy football draft problem to string and writes to file.

    :param starting_11: drafted starting 11 players
    :param bench:       4 players drafted as substitue players
    :param filepath:    file to write solution to

    :return:            None
    """
    starting_string = ''
    for i in range(10):
        starting_string += str(starting_11[i].ID) + ","
    starting_string += str(starting_11[10].ID)
    bench_string = ''
    for i in range(0, 3):
        bench_string += str(bench[i].ID) + ","
    bench_string += str(bench[3].ID)

    text_file = open(filepath, "w")
    text_file.write(starting_string + "\n")
    text_file.write(bench_string)
    text_file.close()


def eval_solution(players):
    """
    Evaluate solution as sum of players' points.

    :param players: list of drafted players
    :return:        sum of drafted players' points
    """
    sum = 0
    for player in players:
        sum += player.points
    return sum


def points_price_sort(x):
    """
    Sort criterion for sorting players by points ascending and price descending.

    :param x: player
    :return: value of player's points and negative value of player price
    """
    return x.points, -x.price


def check_club_constraint(selected, club):
    """
    Check if maximum number of players from a single club (2) has been drafted in a team.

    :param selected: drafted players
    :param club:     name of a club
    :return:         True if max value of players from one club has not been reached, false otherwise
    """

    cnt = 0
    for player in selected:
        if player.club == club:
            cnt += 1
    return cnt <= 2


def divide_by_positions(players):
    """
    Divides all players into 4 categories according to their position. Players are sorted by points descending and price ascending

    :param players: list of all players
    :return:        dictionary of players by positions
    """
    players.sort(key=points_price_sort, reverse=True)
    gks = [x for x in players if x.position == GK]
    mids = [x for x in players if x.position == MID]
    fws = [x for x in players if x.position == FW]
    defs = [x for x in players if x.position == DEF]

    return {GK: gks, MID: mids, DEF: defs, FW: fws}


def select_starting_11(selected_15):
    """
    Select 15 best players from drafted players

    :param selected_15: drafted players
    :return:            list of starting 11 players and list of substitute players
    """
    # select starting 11
    starting_11 = []
    bench = []
    selected_list = sorted(list(selected_15), key=points_price_sort, reverse=True)

    # satisfy 1 GK constraint
    goalkeepers = [x for x in selected_list if x.position == GK]
    starting_11.append(goalkeepers[0])
    bench.append(goalkeepers[1])
    selected_15 = selected_15 - set(goalkeepers)

    # satisfy at least one FW constraint
    forward = [x for x in selected_list if x.position == FW][0]
    starting_11.append(forward)
    selected_15.remove(forward)

    # satisfy at least 3 DEF constraint
    defenders = [x for x in selected_list if x.position == DEF][:3]
    starting_11 += defenders
    selected_15 -= set(defenders)

    # fill remaining spots in starting 11 with better players
    remaining = sorted(list(selected_15), key=points_price_sort, reverse=True)
    starting_11 += remaining[:6]
    bench += remaining[6:]

    return starting_11, bench
