from puzzle.puzzles import Puzzles

from pydantic import BaseModel, Field
from models.gateway_adapter import Tool
import chess
import chess.svg
import gradio as gr
from enum import Enum


class Theme(str, Enum):
    NONE = "none"
    MATE = "mate"
    MATE_IN_1 = "mateIn1"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"
    KINGSIDE_ATTACK = "kingsideAttack"
    MASTER = "master"
    OPENING = "opening"
    HANGING_PIECE = "hangingPiece"
    BACK_RANK_MATE = "backRankMate"
    ROOK_ENDGAME = "rookEndgame"
    ATTACKING_F2F7 = "attackingF2F7"
    OPERA_MATE = "operaMate"
    PILLSBURYS_MATE = "pillsburysMate"
    QUEENSIDE_ATTACK = "queensideAttack"
    SMOTHERED_MATE = "smotheredMate"
    PIN = "pin"
    QUEEN_ENDGAME = "queenEndgame"
    EPAULETTE_MATE = "epauletteMate"
    QUEEN_ROOK_ENDGAME = "queenRookEndgame"
    ADVANCED_PAWN = "advancedPawn"
    CORNER_MATE = "cornerMate"
    DISCOVERED_CHECK = "discoveredCheck"
    PROMOTION = "promotion"
    DOUBLE_CHECK = "doubleCheck"
    MORPHYS_MATE = "morphysMate"
    BLIND_SWINE_MATE = "blindSwineMate"
    TRIANGLE_MATE = "triangleMate"
    ARABIAN_MATE = "arabianMate"
    DOVETAIL_MATE = "dovetailMate"
    BODEN_MATE = "bodenMate"
    DOUBLE_BISHOP_MATE = "doubleBishopMate"
    DISCOVERED_ATTACK = "discoveredAttack"
    ANASTASIA_MATE = "anastasiaMate"
    BISHOP_ENDGAME = "bishopEndgame"
    KILL_BOX_MATE = "killBoxMate"
    ADVANTAGE = "advantage"
    KNIGHT_ENDGAME = "knightEndgame"
    VUKOVIC_MATE = "vukovicMate"
    CRUSHING = "crushing"
    BALESTRA_MATE = "balestraMate"
    EQUALITY = "equality"
    PAWN_ENDGAME = "pawnEndgame"


class GetPuzzleArgs(BaseModel):
    rating: int = Field(
        description="The rating of the chess puzzle (has same scale as normal chess rating)"
    )
    theme: Theme = Field(
            description='The theme of the puzzle or "none" if no particular theme is requested.'
        )

puzzles = Puzzles(250000)
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
                    "This function also displays the chess puzzle as a visual chess board to the user, so no need for you to output the fen or try to explain the actual board setup." 
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
        
        



