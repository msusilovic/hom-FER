import math
import random
from collections import deque

from util import solution_to_string, parse_instance_csv, eval_solution, points_price_sort, check_club_constraint, \
    select_starting_11, divide_by_positions

GK = 'GK'
MID = 'MID'
DEF = 'DEF'
FW = 'FW'

MAX_BUDGET = 100.
MAX_POSITIONS = {GK: 2, MID: 5, DEF: 5, FW: 3}


def random_search(players, outfile):
    """
    Finds a random feasible solution to use as initial solution.

    :param players: all available players
    :return:        list fo starting 11, list of substitute players and remaining budget
    """
    budget = MAX_BUDGET
    selected_15 = set()
    positions_cnt = {GK: 0, MID: 0, DEF: 0, FW: 0}
    random.shuffle(players)

    while len(selected_15) < 15:
        for player in players:
            if len(selected_15) == 15:  # all 15 players selected
                break
            if player not in selected_15 and positions_cnt[player.position] < MAX_POSITIONS[
                player.position] and check_club_constraint(selected_15, player.club):
                if player.price > budget:
                    # remove a random selected player
                    selected = list(selected_15)
                    selected.sort(key=lambda x: x.price, reverse=True)
                    removed_player = selected[0]
                    selected_15.remove(removed_player)  # remove the most expensive player
                    positions_cnt[removed_player.position] = positions_cnt[removed_player.position] - 1
                    budget += removed_player.price
                else:
                    selected_15.add(player)
                    positions_cnt[player.position] = positions_cnt[player.position] + 1
                    budget -= player.price

    starting_11, bench = select_starting_11(selected_15)
    solution_to_string(starting_11, bench, outfile)
    return starting_11, bench, budget


def greedy_search(players, outfile):
    """
    Implementation of a greedy algorithm to choose 15 players for a team.
    4 cheapest players are drafted as substitutes, then the remaining 11 are chosen by points.

    :param players: all available players
    :return:        list fo starting 11, list of substitute players and remaining budget
    """
    budget = MAX_BUDGET
    selected_15 = set()
    positions_cnt = {GK: 0, MID: 0, DEF: 0, FW: 0}
    players.sort(key=(lambda p: p.price))

    # draft 4 cheapest players as substitutes - one must be GK
    while len(selected_15) < 4:
        for player in players:
            if len(selected_15) == 4:
                break
            if check_club_constraint(selected_15, player.club):
                if player.position == 'GK':
                    if positions_cnt['GK'] < 1:
                        selected_15.add(player)
                        positions_cnt['GK'] = 1
                        budget -= player.price
                else:
                    if (positions_cnt['GK'] < 1 and len(selected_15) < 3) or (
                            positions_cnt['GK'] == 1 and len(selected_15) < 4):
                        selected_15.add(player)
                        positions_cnt[player.position] = positions_cnt[player.position] + 1
                        budget -= player.price

    # draft remaining 11
    players.sort(key=points_price_sort, reverse=True)
    for player in players:
        if len(selected_15) == 15:  # all 15 players selected
            break
        if player not in selected_15 and positions_cnt[player.position] < MAX_POSITIONS[
            player.position] and check_club_constraint(selected_15, player.club):
            if player.price > budget:
                # remove most expensive player so far
                sorted_selected = list(selected_15)
                sorted_selected.sort(key=lambda x: x.price, reverse=True)
                removed_player = sorted_selected[0]
                selected_15.remove(removed_player)  # remove the most expensive player
                positions_cnt[removed_player.position] = positions_cnt[removed_player.position] - 1
                budget += removed_player.price
            if player.price <= budget:
                # try adding the player again
                selected_15.add(player)
                positions_cnt[player.position] = positions_cnt[player.position] + 1
                budget -= player.price

    starting_11, bench = select_starting_11(selected_15)
    solution_to_string(starting_11, bench, outfile)
    return starting_11, bench, budget


def local_search(instance, starting_11, bench, budget, outfile):
    """
    Implementation of a  search algorithm to find local optimum of fantasy football draft problem from given starting solution.

    :param instance:        list containing all available players
    :param starting_11:     initial starting 11 players
    :param bench:           substitute 4 players
    :param budget:          remaining budget for initial team

    :return:                improved list of 11 staring players and 4 players on bench
    """

    by_positions = divide_by_positions(instance)

    iteration = 0
    improved = True

    while improved:
        improved = False
        iteration += 1
        for i in range(11):
            player = starting_11[i]
            # pick 3 alternatives for current player which have more points
            alternatives = [x for x in by_positions[player.position] if x.points > player.points][-3:]
            for candidate in alternatives:
                if candidate in starting_11 or candidate in bench:
                    continue
                if (budget + player.price >= candidate.price) and (check_club_constraint([*starting_11, *bench],
                                                                                         candidate.club) or player.club == candidate.club):
                    improved = True
                    starting_11[i] = candidate
                    budget += player.price
                    budget -= candidate.price
                    break

    solution_to_string(starting_11, bench, outfile)
    return starting_11, bench


def is_tabu(solution, tabu_list):
    for tabu in tabu_list:
        if set(solution) - set(tabu) == set():
            return True
    return False


def tabu_search(instance, starting_11, bench, budget, outfile, tenure=25):
    """
    Implementation of a tabu search algorithm for finding a solution to a fantasy football draft problem.

    :param instance:        list containing all available players
    :param starting_11:     initial starting 11 players
    :param bench:           substitute 4 players
    :param budget:          remaining budget for initial team
    :param tenure:          length of tabu list

    :return:                improved list of 11 staring players and 4 players on bench
    """
    by_positions = divide_by_positions(instance)
    tabu_list = deque(maxlen=tenure)
    best_solution = None
    best_score = 0

    tabu_list.append(starting_11)

    for iteration in range(400):
        for i in range(11):
            player = starting_11[i]

            # pick 6 alternatives for current player which are neighbors by price
            index = by_positions[player.position].index(player)
            min_idx = max(0, index - 3)
            max_idx = min(index + 3, len(by_positions[player.position]) - 1)
            alternatives = by_positions[player.position][min_idx:max_idx + 1]
            alternatives.remove(player)

            for candidate in alternatives:
                if (budget + player.price >= candidate.price) and (check_club_constraint([*starting_11, *bench],
                                                                                         candidate.club) or player.club == candidate.club):

                    possible_solution = starting_11[:]
                    possible_solution[i] = candidate

                    if not is_tabu(possible_solution, tabu_list):
                        starting_11 = possible_solution
                        tabu_list.append(starting_11)

                        budget += player.price
                        budget -= candidate.price
                        score = eval_solution(starting_11)

                        if score > best_score:
                            best_score = score
                            best_solution = possible_solution

                        break

    solution_to_string(best_solution, bench, outfile)
    return starting_11, bench


def simulated_annealing(instance, starting_11, bench, budget, t0, outfile):
    """
    Implementation of simulated annealing algorithm for fantasy football problem.

    :param instance:        all players
    :param starting_11:     list of starting 11 players
    :param bench:           list of substitute players
    :param budget:          remaining budget for buying players
    :param t0:              starting temperature
    :param outfile:         file to write solutions to
    :return:                list of selected 11 players and list of substitute players
    """
    t = t0
    by_positions = divide_by_positions(instance)

    # init solutions s_best and s
    current_solution = starting_11[:]
    current_score = eval_solution(current_solution)
    best_solution = starting_11
    best_score = current_score

    iter = 1

    while t > 0.01:
        iter += 1

        for i in range(11):
            # generate neighbor satisfying constraints
            player = current_solution[i]

            index = by_positions[player.position].index(player)
            min_idx = max(0, index - 3)
            max_idx = min(index + 3, len(by_positions[player.position]) - 1)
            indices = list(range(min_idx, max_idx))
            indices.remove(index)
            random.shuffle(indices)

            neighbor = None
            for idx in indices:
                candidate = by_positions[player.position][idx]
                if candidate in current_solution or candidate in bench:
                    break
                if (budget + player.price >= candidate.price) and (check_club_constraint([*current_solution, *bench],
                                                                                         candidate.club) or player.club == candidate.club):
                    neighbor = candidate
                    break
            if not neighbor:
                continue

            # s'
            possible_solution = current_solution[:]
            possible_solution[i] = neighbor

            score = eval_solution(possible_solution)
            if score > current_score:
                p = 1
            else:
                dt = current_score - score
                p = math.exp(-dt / t)

            # accept solution
            if random.random() < p:
                budget += player.price
                budget -= neighbor.price
                current_solution = possible_solution
                current_score = eval_solution(current_solution)

                budget = round(budget, 1)

            if current_score > best_score:
                best_score = current_score
                best_solution = current_solution

        t = 0.99 * t

    solution_to_string(best_solution, bench, outfile)
    return best_solution, bench


if __name__ == "__main__":
    instance = parse_instance_csv('../instances/instance1.csv')
    starting_11, bench, budget = random_search(instance, 'solutions/random1.txt')
    starting_11, bench = tabu_search(instance, starting_11, bench, budget, 'solutions/tabu1.txt', tenure=30)
