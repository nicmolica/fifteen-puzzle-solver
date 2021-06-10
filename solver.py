import sys
import numpy as np
from queue import PriorityQueue
from timeit import default_timer as timer

SIDE = 4
BLANK = 0

CORRECT_BOARD = """1 2 3 4
5 6 7 8
9 10 11 12
13 14 15 -"""

OTHER_CORRECT_BOARD = """1 5 9 13
2 6 10 14
3 7 11 15
4 8 12 -"""

CORRECT_LOCATIONS = {1: (0,0), 2: (0,1), 3: (0,2), 4: (0,3), \
                    5: (1,0), 6: (1,1), 7: (1,2), 8: (1,3), \
                    9: (2,0), 10: (2,1), 11: (2,2), 12: (2,3), \
                    13: (3,0), 14: (3,1), 15: (3,2)}

class NumberPuzzle:
    def __init__(self):
        self.tiles = np.zeros((SIDE, SIDE))
        self.blank = (0, 0)
        self.parent = None
        self.layer = 0
        self.heuristic_value = 0

    def copy(self):
        copy = NumberPuzzle()
        copy.tiles = np.copy(self.tiles)
        copy.blank = self.blank
        copy.parent = self
        copy.heuristic_value = 0
        copy.layer = self.layer
        return copy

    def __eq__(self, other):
        return np.array_equal(self.tiles, other.tiles)

    def __hash__(self):
        return hash(bytes(self.tiles))

    def __lt__(self, other):
        return self.heuristic_value < other.heuristic_value

    def __str__(self):
        output = ""
        for i in range(SIDE):
            for j in range(SIDE):
                if j > 0:
                    output += " "
                if self.tiles[i][j] == BLANK:
                    output += "-"
                else:
                    output += str(int(self.tiles[i][j]))
            output += "\n" if i != SIDE - 1 else ""
        return output

    def populate_board(self, tiles):
        try:
            rows = tiles.splitlines()
            for i in range(len(rows)):
                columns = rows[i].split()
                for j in range(len(columns)):
                    if columns[j] == "-":
                        self.tiles[i][j] = BLANK
                        self.blank = (i, j)
                    else:
                        self.tiles[i][j] = int(columns[j])
            if not self.has_valid_board():
                raise RuntimeError("Invalid board layout.")
        except:
            exit_message = """Invalid board layout. Board should follow the syntax below:
            1 2 3 4
            5 6 7 8
            9 10 11 12
            13 14 15 -"""
            sys.exit(exit_message)

    def has_valid_board(self):
        for i in range(0, 16):
            if i not in self.tiles or len(np.where(self.tiles == i)[0]) > 1:
                return False
        return True

    def solved(self):
         # TODO remove this
        if str(self) == OTHER_CORRECT_BOARD:
            print("inverted board")
            exit(1)
        return str(self) == CORRECT_BOARD

    def calculate_heuristic(self, src, dest):
        return self.layer + self.manhattan_heuristic(src, dest)

    def manhattan_heuristic(self, src, dest):
        # TODO in description of this method, talk about optimizations
        if not self.parent:
            total_manhattan = 0
            for i in range(SIDE):
                for j in range(SIDE):
                    val = self.tiles[i][j]
                    if not val == 0:
                        x = CORRECT_LOCATIONS[val][0]
                        y = CORRECT_LOCATIONS[val][1]
                        total_manhattan += abs(x - j) + abs(y - i)
            print(total_manhattan)
            return total_manhattan
        else:
            # optimization to only calculate the change in manhattan distance for the tile we actually moved
            val = self.tiles[dest[0]][dest[1]]
            x = CORRECT_LOCATIONS[val][0]
            y = CORRECT_LOCATIONS[val][1]
            self_manhattan = abs(y - dest[0]) + abs(x - dest[1])
            parent_manhattan = abs(y - src[0]) + abs(x - src[1])
            manhattan_diff = self_manhattan - parent_manhattan
            return self.parent.heuristic_value - self.parent.layer + manhattan_diff

    """
    def inversion_heuristic(self, src, dest):
        # TODO in description of this method, talk about optimizations
        flat_board = self.tiles.flatten('F')
        inversions = 0
        for i in range(len(flat_board)):
            for j in range(i + 1, len(flat_board)):
                if flat_board[i] > flat_board[j] and flat_board[j] != BLANK:
                    inversions += 1
        return inversions
    """

    def inversion_heuristic(self, src, dest):
        # TODO in description of this method, talk about optimizations

        if not self.parent:
            # if we have no parent, do all the work of calculating initial heuristic
            flat_board = self.tiles.flatten()
            print(flat_board)
            inversions = 0
            for i in range(len(flat_board)):
                for j in range(i + 1, len(flat_board)):
                    if flat_board[i] > flat_board[j] and flat_board[j] != BLANK:
                        inversions += 1
        elif src[0] == dest[0]:
            # optimization to keep heuristic identical if moving horizontally
            inversions = self.parent.heuristic_value - self.parent.layer
        else:
            # optimization to only calculate heuristic change for the tile we actually moved
            sx, sy, dx, dy = src[0], src[1], dest[0], dest[1]
            print("sy: " + str(sy) + ", sx: " + str(sx) + ", dy: " + str(dy) + ", dx: " + str(dx))
            val = self.tiles[dy][dx]
            down = sy < dy
            start, end = sx + sy * 4, dx + dy * 4
            flat = self.tiles.flatten()
            tiles_between = flat[start + 1:end] if down else flat[end + 1:start]
            print(str(val) + (" down" if down else " up"))
            print(tiles_between)
            print("prev:\n" + str(self.parent))
            print("current:\n" + str(self))
            if down:
                inversions = sum(map(lambda x: 1 if x < val else -1, tiles_between))
            else:
                inversions = sum(map(lambda x: 1 if x > val else -1, tiles_between))
            print(inversions)
            inversions += self.parent.heuristic_value - self.parent.layer
        return inversions

    def solve(self):
        self.calculate_heuristic(None, None)
        c = set()
        q = PriorityQueue()
        q.put(self)
        while not q.empty():
            a = q.get()
            if a.solved():
                path = a.path_to_here()
                c.add(a)
                return path, len(c)
            c.add(a)
            for move in a.determine_legal_moves():
                if move not in c:
                    q.put(move)
        return None, len(c)

    def move_tile(self, tile):
        dest_y = self.blank[0]
        dest_x = self.blank[1]
        src_y = tile[0]
        src_x = tile[1]
        self.tiles[dest_y][dest_x] = self.tiles[src_y][src_x]
        self.tiles[src_y][src_x] = BLANK
        self.blank = (src_y, src_x)
        self.layer += 1
        self.heuristic_value = self.calculate_heuristic((src_y, src_x), (dest_y, dest_x))

    def determine_legal_moves(self):
        moves = set()
        if self.blank[0] > 0:
            down = self.copy()
            down.move_tile((self.blank[0] - 1, self.blank[1]))
            moves.add(down)
        if self.blank[0] < SIDE - 1:
            up = self.copy()
            up.move_tile((self.blank[0] + 1, self.blank[1]))
            moves.add(up)
        if self.blank[1] > 0:
            right = self.copy()
            right.move_tile((self.blank[0], self.blank[1] - 1))
            moves.add(right)
        if self.blank[1] < SIDE - 1:
            left = self.copy()
            left.move_tile((self.blank[0], self.blank[1] + 1))
            moves.add(left)
        return moves

    def path_to_here(self):
        """Returns list of NumberPuzzles giving the move sequence to get here.
        """
        path = []
        current = self
        while not current is None:
            path.insert(0, current)
            current = current.parent
        return path

def print_steps(path):
    if path is None:
        print("No path found")
    else:
        print("{} steps".format(len(path)-1))
        for state in path:
            print(state)

def solve_and_print(puzzle_string):
    puzzle = NumberPuzzle()
    puzzle.populate_board(puzzle_string)
    solution_steps, explored = puzzle.solve()
    print("{} nodes explored".format(explored))
    print_steps(solution_steps)

def is_solvable(puzzle_string):
    puzzle = NumberPuzzle()
    puzzle.populate_board(puzzle_string)
    return (SIDE - puzzle.blank[0]) % 2 != puzzle.inversion_heuristic(None, None) % 2

zero_moves = """1 2 3 4
5 6 7 8
9 10 11 12
13 14 15 -"""

one_move = """1 2 3 4
5 6 7 8
9 10 11 12
13 14 - 15"""

six_moves = """1 2 3 4
5 10 6 8
- 9 7 12
13 14 11 15"""

sixteen_moves = """10 2 4 8
1 5 3 -
9 7 6 12
13 14 11 15"""

forty_moves = """4 3 - 11
2 1 6 8
13 9 7 15
10 14 12 5"""

unsolvable = """3 9 1 15
14 11 4 6
13 - 10 12
2 7 8 5"""

eighty_moves = """- 12 9 13
15 11 10 14
8 3 6 2
4 7 5 1"""

start = timer()
if is_solvable(six_moves):
    solve_and_print(six_moves)
else:
    print("This puzzle is not solvable.")
end = timer()
print(end - start)