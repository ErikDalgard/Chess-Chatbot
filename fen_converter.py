"""
Convert a BoardReading (the structured output from board_reader.py) into a
FEN string. Fully deterministic: no model calls.

FEN has six fields:
  1. piece placement   (from the reading)
  2. side to move      (from the reading, or a default if unknown)
  3. castling rights   (inferred: king and rook still on their start squares)
  4. en passant square (can't be seen on a board, always "-")
  5. halfmove clock    (can't be seen, always 0)
  6. fullmove number   (can't be seen, always 1)
"""

from typing import Optional

from board_reader import BoardReading, Color, PieceType, SideToMove


PIECE_LETTERS = {
    PieceType.king: "k",
    PieceType.queen: "q",
    PieceType.rook: "r",
    PieceType.bishop: "b",
    PieceType.knight: "n",
    PieceType.pawn: "p",
}

FILES = "abcdefgh"


def reading_to_board(reading: BoardReading) -> dict[str, str]:
    """
    Turn the list of pieces into {square: fen_letter}, e.g. {"e1": "K", "e8": "k"}.
    White pieces are uppercase, black pieces lowercase.
    Raises ValueError if the input wasn't a board or a square is used twice.
    """
    if not reading.is_chess_board:
        raise ValueError("The reading is not a chess board.")

    board: dict[str, str] = {}
    for p in reading.pieces:
        square = p.square.value
        if square in board:
            raise ValueError(f"More than one piece on {square}.")
        letter = PIECE_LETTERS[p.piece]
        board[square] = letter.upper() if p.color == Color.white else letter
    return board


def placement_field(board: dict[str, str]) -> str:
    """Build the first FEN field, from rank 8 down to rank 1."""
    ranks = []
    for rank in range(8, 0, -1):
        row = ""
        empty = 0
        for file in FILES:
            piece = board.get(f"{file}{rank}")
            if piece is None:
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += piece
        if empty:
            row += str(empty)
        ranks.append(row)
    return "/".join(ranks)


def castling_field(board: dict[str, str]) -> str:
    """
    Guess castling rights from piece positions. A side may castle on a wing
    if its king and that wing's rook are still on their starting squares.
    (We can't know if they moved and came back, so this is a best guess.)
    """
    rights = ""
    if board.get("e1") == "K":
        if board.get("h1") == "R":
            rights += "K"
        if board.get("a1") == "R":
            rights += "Q"
    if board.get("e8") == "k":
        if board.get("h8") == "r":
            rights += "k"
        if board.get("a8") == "r":
            rights += "q"
    return rights or "-"


def side_field(reading: BoardReading, default_side: str) -> str:
    if reading.side_to_move == SideToMove.white:
        return "w"
    if reading.side_to_move == SideToMove.black:
        return "b"
    return default_side


def board_to_fen(
    reading: BoardReading,
    side_to_move: Optional[str] = None,
    default_side: str = "w",
) -> str:
    """
    Convert a BoardReading into a full FEN string.

    side_to_move: force "w" or "b" (e.g. if the user told you whose turn it is).
    default_side: used when neither side_to_move nor the reading says whose turn it is.
    """
    for value in (side_to_move, default_side):
        if value is not None and value not in ("w", "b"):
            raise ValueError(f"Side must be 'w' or 'b', got {value!r}.")

    board = reading_to_board(reading)

    placement = placement_field(board)
    side = side_to_move or side_field(reading, default_side)
    castling = castling_field(board)

    return f"{placement} {side} {castling} - 0 1"