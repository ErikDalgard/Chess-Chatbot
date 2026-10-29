"""Load and retrieve one-move puzzles from the Lichess-derived corpus."""

import csv
import random
import zstandard as zstd
import io
from collections import defaultdict
from pathlib import Path
import json


class Puzzles:
    """In-memory puzzle index keyed by rating bucket (width 100)."""

    def __init__(self, n_puzzles):
        self.MAX_ITERATIONS = 10000000
        self.FILE_PATH = "puzzles.json.zst"
        self.CSV_PATH = "lichess_db_puzzle.csv.zst"

        self.puzzles_by_rating = self.load_puzzles_from_file(self.FILE_PATH)
        if not self.puzzles_by_rating:
            print("Puzzle cache not found. Building from Lichess CSV dump instead.")
            self.puzzles_by_rating = self.load_puzzles_from_database(n_puzzles)
            json_bytes = json.dumps(self.puzzles_by_rating).encode("utf-8")
            with open(self.FILE_PATH, "wb") as f:
                f.write(zstd.ZstdCompressor().compress(json_bytes))
        else:
            print("Puzzles loaded from file")

        n_puzzles_loaded = sum(len(puzzles) for puzzles in self.puzzles_by_rating.values())
        print(f"Number of puzzles loaded = {n_puzzles_loaded}")

    def load_puzzles_list(self, n_puzzles):
        puzzles = []

        assert n_puzzles <= self.MAX_ITERATIONS

        csv_path = Path(self.CSV_PATH)
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing puzzle data. Place `{self.FILE_PATH}` in the project root, "
                f"or provide `{self.CSV_PATH}` to build the cache."
            )

        with open(csv_path, "rb") as compressed_file:
            decompressor = zstd.ZstdDecompressor()

            with decompressor.stream_reader(compressed_file) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8")
                csv_reader = csv.DictReader(text_stream)

                index = 0
                for iteration, row in enumerate(csv_reader):
                    if iteration >= self.MAX_ITERATIONS:
                        break
                    moves = row["Moves"].split()
                    # One-move puzzles: last move + one solution move
                    if len(moves) != 2:
                        continue
                    item = {
                        "id": row["PuzzleId"],
                        "fen": row["FEN"],
                        "moves": moves,
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
                    index += 1

        return puzzles

    def load_puzzles_from_file(self, file_path):
        path = Path(file_path)
        if path.exists():
            with open(file_path, "rb") as f:
                json_bytes = zstd.ZstdDecompressor().decompress(f.read())
                return {int(key): value for key, value in json.loads(json_bytes).items()}
        return {}

    def load_puzzles_from_database(self, n_puzzles):
        puzzles_by_rating = defaultdict(list)

        puzzles = self.load_puzzles_list(n_puzzles)

        for puzzle in puzzles:
            rating = int(puzzle["rating"])
            bucket = rating // 100 * 100
            puzzles_by_rating[bucket].append(puzzle)
        return puzzles_by_rating

    def retrieve_puzzle(self, rating_lower_bound, rating_upper_bound, theme):
        """Return a random one-move puzzle in the rating window, optionally filtered by theme."""
        candidates = []
        for rating, puzzles in self.puzzles_by_rating.items():
            if rating_lower_bound <= rating <= rating_upper_bound:
                for puzzle in puzzles:
                    if len(puzzle["moves"]) != 2:
                        continue
                    if theme == "none" or theme in puzzle["themes"]:
                        candidates.append(puzzle)
        if candidates:
            return random.choice(candidates)
        return None
