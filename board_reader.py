"""
Turn a chess board (image or text) into a structured list of piece placements
using Gemini structured output. The result is designed so a separate,
deterministic function can convert it into a FEN string.
"""

from enum import Enum
from typing import Optional

from google import genai
from pydantic import BaseModel, Field
from models.interface import Model

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

# All 64 squares as an enum, so the model can only answer with valid squares.
Square = Enum(
    "Square",
    {f"{f}{r}": f"{f}{r}" for r in range(1, 9) for f in "abcdefgh"},
    type=str,
)


class Color(str, Enum):
    white = "white"
    black = "black"


class PieceType(str, Enum):
    king = "king"
    queen = "queen"
    rook = "rook"
    bishop = "bishop"
    knight = "knight"
    pawn = "pawn"


class SideToMove(str, Enum):
    white = "white"
    black = "black"
    unknown = "unknown"


class Orientation(str, Enum):
    white_at_bottom = "white_at_bottom"
    black_at_bottom = "black_at_bottom"
    unknown = "unknown"


class Piece(BaseModel):
    square: Square = Field(description="Square the piece stands on, e.g. 'e4'.")
    color: Color
    piece: PieceType


class BoardReading(BaseModel):
    is_chess_board: bool = Field(
        description="True only if the input shows or describes a chess position."
    )
    orientation: Orientation = Field(
        description="Which side is at the bottom of the image. Use 'unknown' for text input."
    )
    side_to_move: SideToMove = Field(
        description="Whose turn it is, only if clearly indicated. Otherwise 'unknown'."
    )
    pieces: list[Piece] = Field(
        description="Every piece on the board, one entry per occupied square. Empty if not a board."
    )
    notes: str = Field(
        description="Short note on anything unclear (blurry squares, hidden pieces). Empty if none."
    )


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

BOARD_READER_INSTRUCTIONS = """
You read chess positions and report exactly where every piece is.

- First decide whether the input is a chess position. If it is not, set
  is_chess_board to false and return an empty pieces list.
- Work out the board orientation before naming squares. Use the coordinate
  labels if visible. Otherwise remember that a1 is a dark square in the
  bottom-left corner from White's side.
- Squares use files a-h (left to right from White's side) and ranks 1-8
  (White's side is rank 1).
- List every occupied square exactly once. Do not list empty squares.
- Report only what you see. Do not add or move pieces to make the position
  look legal or familiar.
- Set side_to_move only if it is clearly indicated (text, arrow, highlight).
- Use notes to mention any square you are unsure about.
""".strip()


# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------

def read_board(
    model: Model,
    image_path: Optional[str] = None,
    text: Optional[str] = None,
) -> BoardReading:
    """
    Send a board image and/or text to Gemini and get back a BoardReading.

    Pass image_path for a screenshot or photo of a board, text for a written
    description, or both (e.g. an image plus "white to move").
    """
    if image_path is None and text is None:
        raise ValueError("Provide image_path, text, or both.")

    if image_path is None:
        return model.parse_text(BoardReading, prompt=text, instructions=BOARD_READER_INSTRUCTIONS)
    else:
        return model.parse_image(image_path, BoardReading, prompt=text, instructions=BOARD_READER_INSTRUCTIONS)


def check_reading(reading: BoardReading) -> list[str]:
    """
    Basic sanity checks on a reading. Returns a list of problems
    (empty list means it looks fine). Does not modify the reading.
    """
    problems = []
    if not reading.is_chess_board:
        return ["Input was not recognised as a chess board."]

    squares = [p.square for p in reading.pieces]
    duplicates = {s.value for s in squares if squares.count(s) > 1}
    if duplicates:
        problems.append(f"More than one piece on: {', '.join(sorted(duplicates))}")

    for color in Color:
        kings = sum(
            1 for p in reading.pieces
            if p.color == color and p.piece == PieceType.king
        )
        if kings != 1:
            problems.append(f"{color.value} has {kings} kings (expected 1).")

    for p in reading.pieces:
        if p.piece == PieceType.pawn and p.square.value[1] in "18":
            problems.append(f"Pawn on {p.square.value} (pawns can't be on rank 1 or 8).")

    return problems


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    API_KEY = os.environ["GEMINI_API_KEY"]

    client = genai.Client(api_key="GEMINI_API_KEY")
    reading = read_board(client, "gemini-3.8-flash", image_path="board.png")

    print(reading.model_dump_json(indent=2))
    for problem in check_reading(reading):
        print("Warning:", problem)