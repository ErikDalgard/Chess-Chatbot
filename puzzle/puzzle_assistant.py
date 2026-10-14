from puzzle.puzzles import Puzzles

from pydantic import BaseModel, Field
from models.gateway_adapter import Tool
import chess
import chess.svg
import gradio as gr

class WeatherArgs(BaseModel):
    location: int = Field(
        description="Player id (you have to ask the user of his id)"
    )

def get_rating(location: int):
    return {
        "rating": 10*location
    }

puzzles = Puzzles(10000)

class WeatherArgs(BaseModel):
    location: int = Field(
        description="Player id (you have to ask the user of his id)"
    )

puzzle_board = None
def get_puzzle(rating, theme):
    puzzle = puzzles.retrieve_puzzle(rating_lower_bound=rating - 100, rating_upper_bound=rating+50, theme=theme)

    moves = puzzle["moves"]
    assert(len(moves)==2)

    last_move = moves[0]
    solution_move = moves[-1]

    # Make the first move
    puzzle_board = chess.Board(puzzle["fen"])
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

    # board = chess.Board(puzzle["fen"])
    # move_text = puzzle["moves"][0]
    # move = chess.Move.from_uci(move_text)
    # if move not in board.legal_moves:        
    #     raise ValueError(f"Illegal move: {move_text}")
    # board.push(move)   

    # svg = chess.svg.board(board, size=360)
    # yield [gr.HTML(svg), reply]


class PuzzleAssistant:
    def __init__(self, model):
        self.model = model

        self.instructions = """ 
        You are a chess puzzle assistant.
        - Keep answers concise and conversational.
        """

        self.tools = [
            Tool(get_rating, WeatherArgs, name="get_rating", description=(
            "Get the player's rating given the player's id. "
            "Use this tool when the user asks about his/her rating"
        )),
            Tool(get_rating, WeatherArgs, name="get_rating", description=(
                    "Get the player's rating given the player's id. "
                    "Use this tool when the user asks about his/her rating"
                ))]



    def input2output(self, text, image_paths, session_id):
        if image_paths:
            return "change_mode"

        puzzle = get_puzzle(1000, "mate")
        if puzzle_board:
            yield display_puzzle(puzzle_board)
        puzzle_board = None
            #yield [gr.HTML(svg), reply]
        #yield from self.model.stream_tools(self.instructions, text, session_id, self.tools, max_depth=2)
        
        



