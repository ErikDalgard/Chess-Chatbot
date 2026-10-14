import csv
import random
import zstandard as zstd
import io
from collections import defaultdict

class Puzzles:
    def __init__(self, n_puzzles):
        self.puzzles_by_rating = self.load_puzzles_by_rating(n_puzzles)

    def load_puzzles(self, n_puzzles):
        puzzles = []
        max_iterations = 100000
        assert(n_puzzles <= max_iterations)

        with open("lichess_db_puzzle.csv.zst", "rb") as compressed_file:
            decompressor = zstd.ZstdDecompressor()

            with decompressor.stream_reader(compressed_file) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8")
                csv_reader = csv.DictReader(text_stream)

                for index, row in enumerate(csv_reader):
                    if index >= max_iterations:
                        break
                    item = {
                        "id": row["PuzzleId"],
                        "fen": row["FEN"],
                        "moves": row["Moves"].split(),
                        "rating": int(row["Rating"]),
                        "popularity": int(row["Popularity"]),
                        "themes": row["Themes"].split(),
                    }

                    if index < n_puzzles:
                        puzzles.append(item)
                    else:
                        replacement_index = random.randint(0, index)

                        if replacement_index < n_puzzles:
                            puzzles[replacement_index] = item
        return puzzles
    
    def load_puzzles_by_rating(self, n_puzzles):
        puzzles_by_rating = defaultdict(list)

        puzzles = self.load_puzzles(n_puzzles)

        for puzzle in puzzles:
            rating = int(puzzle["rating"])
            bucket = rating // 100 * 100
            puzzles_by_rating[bucket].append(puzzle)
        return puzzles_by_rating

    # Retrieves the most popular one-move puzzle with rating [rating_lower_bound, rating_upper_bound+99)
    def retrieve_puzzle(self, rating_lower_bound, rating_upper_bound, theme):
        candidates = []
        for rating, puzzles in self.puzzles_by_rating.items():
            if rating >= rating_lower_bound and rating <= rating_upper_bound:
                for puzzle in puzzles:
                    if theme in puzzle["themes"] and len(puzzle["moves"]) == 2: # One move-puzzles has move-length = 2, since first move indicates the prev move before the puzzle
                        candidates.append(puzzle)
        if candidates:
            best_match = max(candidates, key=lambda p: p["popularity"])
        else:
            best_match = None
        print(best_match)
        print(candidates[:-10])
        print(len(candidates))
        return best_match









