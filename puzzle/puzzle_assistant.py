from puzzle.puzzles import Puzzles

from pydantic import BaseModel, Field
from models.gateway_adapter import Tool
import chess
import chess.svg
import gradio as gr
from enum import Enum



class WeatherArgs(BaseModel):
    location: int = Field(
        description="Player id (you have to ask the user of his id)"
    )

def get_rating(location: int):
    return {
        "rating": 10*location
    }

puzzles = Puzzles(10000)

for rating, puzzles in puzzles.puzzles_by_rating.items():
    print(len(puzzles))

class WeatherArgs(BaseModel):
    location: int = Field(
        description="Player id (you have to ask the user of his id)"
    )

from enum import Enum

class Theme(str, Enum):
    NONE = "none"
    ENDGAME = "endgame"
    MIDDLEGAME = "middlegame"
    CRUSHING = "crushing"
    MATE = "mate"
    ADVANTAGE = "advantage"
    LONG = "long"
    ONE_MOVE = "oneMove"
    MATE_IN_1 = "mateIn1"
    MASTER = "master"
    FORK = "fork"
    KINGSIDE_ATTACK = "kingsideAttack"
    VERY_LONG = "veryLong"
    SACRIFICE = "sacrifice"
    ADVANCED_PAWN = "advancedPawn"
    DEFENSIVE_MOVE = "defensiveMove"
    PIN = "pin"
    ROOK_ENDGAME = "rookEndgame"
    DISCOVERED_ATTACK = "discoveredAttack"
    OPENING = "opening"
    DEFLECTION = "deflection"
    QUIET_MOVE = "quietMove"
    PAWN_ENDGAME = "pawnEndgame"
    ATTRACTION = "attraction"
    HANGING_PIECE = "hangingPiece"
    BACK_RANK_MATE = "backRankMate"
    EXPOSED_KING = "exposedKing"
    PROMOTION = "promotion"
    SKEWER = "skewer"
    DISCOVERED_CHECK = "discoveredCheck"
    QUEENSIDE_ATTACK = "queensideAttack"
    BISHOP_ENDGAME = "bishopEndgame"
    # CLEARANCE = "clearance"
    # MASTER_VS_MASTER = "masterVsMaster"
    # QUEEN_ENDGAME = "queenEndgame"
    # INTERMEZZO = "intermezzo"
    # TRAPPED_PIECE = "trappedPiece"
    # OPERA_MATE = "operaMate"
    # ZUGZWANG = "zugzwang"
    # PILLSBURYS_MATE = "pillsburysMate"
    # KNIGHT_ENDGAME = "knightEndgame"
    # QUEEN_ROOK_ENDGAME = "queenRookEndgame"
    # ATTACKING_F2F7 = "attackingF2F7"
    # CAPTURING_DEFENDER = "capturingDefender"
    # DOUBLE_CHECK = "doubleCheck"
    # SMOTHERED_MATE = "smotheredMate"
    # EPAULETTE_MATE = "epauletteMate"
    # INTERFERENCE = "interference"
    # X_RAY_ATTACK = "xRayAttack"
    # EQUALITY = "equality"
    # CORNER_MATE = "cornerMate"
    # HOOK_MATE = "hookMate"
    # SWALLOWSTAIL_MATE = "swallowstailMate"
    # EN_PASSANT = "enPassant"
    # ANASTASIA_MATE = "anastasiaMate"
    # TRIANGLE_MATE = "triangleMate"
    # ARABIAN_MATE = "arabianMate"
    # COLLINEAR_MOVE = "collinearMove"
    # MORPHYS_MATE = "morphysMate"
    # KILL_BOX_MATE = "killBoxMate"
    # BLIND_SWINE_MATE = "blindSwineMate"



class GetPuzzleArgs(BaseModel):
    rating: int = Field(
        description="The rating of the chess puzzle (has same scale as normal chess rating)"
    )
    theme: Theme = Field(
            description='The theme of the puzzle or "none" if no particular theme is requested.'
        )


puzzle_board = None
display_puzzle_board = False

def get_puzzle(rating, theme):
    puzzle = puzzles.retrieve_puzzle(rating_lower_bound=rating - 100, rating_upper_bound=rating+50, theme=theme)
    if not puzzle:
        return "Wasn't able to retrieve a puzzle with those inputs"
    moves = puzzle["moves"]
    assert(len(moves)==2)

    last_move = moves[0]
    solution_move = moves[-1]

    global puzzle_board
    global display_puzzle_board

    # Make the first move
    puzzle_board = chess.Board(puzzle["fen"])
    # Display the puzzle board
    display_puzzle_board = True
    move = chess.Move.from_uci(last_move)
    if move not in puzzle_board.legal_moves:        
        raise ValueError(f"Illegal move: {last_move}")
    puzzle_board.push(move)  

    return {
        "id": puzzle["id"],
        "fen": puzzle_board.fen(),
        "last move": last_move,
        "solution move": solution_move,
        "rating": puzzle["rating"],
        "popularity": puzzle["popularity"],
        "themes": puzzle["themes"],
        }

def display_puzzle(reply, board):
    svg = chess.svg.board(board, size=360)
    yield [gr.HTML(svg), reply]


class PuzzleAssistant:
    def __init__(self, model):
        self.model = model

        self.instructions = """ 
        You are a chess puzzle assistant. When you retrieve a chess puzzle, don't give away the solution unless the player
        asks for it. If you are not able to retrieve a puzzle with the given get_puzzle tool, tell the user so and do NOT make up your own puzzle.
        When the user gives a suggestion for the solution, always check with the solution given by the tool. If the user says queen e4, assume the user
        means to move the piece of the color for who's turn it is.
        - Keep answers concise and conversational.
        """

        self.tools = [
            Tool(get_puzzle, GetPuzzleArgs, name="get_puzzle", description=(
                    "Retrieves a chess puzzle, given a rating and a theme."
                    "If no particular theme is requested, theme could be set to 'none'"
                    "This function also displays the chess puzzle as a visual chess board to the user, so no need for you to output the fen." 
                    "Please say who's turn it is, and what the last move played was."
                    "Use this tool when the user asks for a chess puzzle."
                ))]



    def input2output(self, text, image_paths, session_id):
        if image_paths:
            return "change_mode"

        stream = self.model.stream_tools(self.instructions, text, session_id, self.tools, max_depth=2)

        global display_puzzle_board

        for output_text in stream:
            if puzzle_board and display_puzzle_board:
                yield from display_puzzle(output_text, puzzle_board)
            else:
                yield output_text

        # Do not display the puzzle board, unless a new puzzle_board is loaded
        display_puzzle_board = False
        
        



