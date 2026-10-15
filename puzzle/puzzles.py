import csv
import random
import zstandard as zstd
import io
from collections import defaultdict
from pathlib import Path
import json
from collections import Counter

class Puzzles:
    def __init__(self, n_puzzles):
        self.MAX_ITERATIONS = 10000000 
        self.FILE_PATH = "puzzles.json.zst"

        self.puzzles_by_rating = self.load_puzzles_from_file(self.FILE_PATH)
        if not self.puzzles_by_rating:
            print("Puzzle file not found. Loading from database instead")
            self.puzzles_by_rating = self.load_puzzles_from_database(n_puzzles)
            json_bytes = json.dumps(self.puzzles_by_rating).encode("utf-8")
            with open(self.FILE_PATH, "wb") as f:    
                f.write(zstd.ZstdCompressor().compress(json_bytes))
        else:
            print("Puzzles loaded from file")

        n_puzzles_loaded = sum([len(puzzles) for rating, puzzles in self.puzzles_by_rating.items()])
        print(f"Number of puzzles loaded = {n_puzzles_loaded}")


        # vvv Counting the themes vvv 
        themes = []
        for rating, puzzles in self.puzzles_by_rating.items():
            for p in puzzles:
                themes.extend(p["themes"])
        counts = Counter(themes)
        #print(counts)
        # ^^^ Counting the themes ^^^

    def load_puzzles_list(self, n_puzzles):
        puzzles = []
        
        assert(n_puzzles <= self.MAX_ITERATIONS)

        with open("lichess_db_puzzle.csv.zst", "rb") as compressed_file:
            decompressor = zstd.ZstdDecompressor()

            with decompressor.stream_reader(compressed_file) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8")
                csv_reader = csv.DictReader(text_stream)

                index = 0
                for iteration, row in enumerate(csv_reader):
                    if iteration >= self.MAX_ITERATIONS:
                        break
                    moves = row["Moves"].split()
                    if len(moves) != 2: # Only keep the one move-puzzles - which have move-length = 2, since first move indicates the prev move before the puzzle begins
                        continue
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
                    index += 1

        return puzzles

    def load_puzzles_from_file(self, file_path):
        path = Path(file_path)
        if path.exists():    
            with open(file_path, "rb") as f:    
                json_bytes = zstd.ZstdDecompressor().decompress(f.read())
                return {int(key): value for key, value in json.loads(json_bytes).items()}
        else:
            return {}
        
    def load_puzzles_from_database(self, n_puzzles):
        puzzles_by_rating = defaultdict(list)

        puzzles = self.load_puzzles_list(n_puzzles)

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
                    if len(puzzle["moves"]) == 2: # One move-puzzles has move-length = 2, since first move indicates the prev move before the puzzle
                        if theme == "none":
                            candidates.append(puzzle)
                        elif theme in puzzle["themes"]:
                            candidates.append(puzzle)
        if candidates:
            return random.choice(candidates)
        else:
            return None









