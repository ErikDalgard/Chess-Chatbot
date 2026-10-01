import chess
import chess.engine
import chess.svg


def confirm_fen(fen):
    """Validate a FEN and return its normalized form and board SVG."""
    if not isinstance(fen, str) or not fen.strip():
        return {"valid": False, "fen": None, "svg": None, "error": "Enter a FEN string."}

    try:
        board = chess.Board(fen.strip())
    except ValueError as error:
        return {"valid": False, "fen": None, "svg": None, "error": str(error)}

    if not board.is_valid():
        return {
            "valid": False,
            "fen": None,
            "svg": None,
            "error": f"Invalid chess position (status: {board.status()})",
        }

    return {
        "valid": True,
        "fen": board.fen(),
        "svg": chess.svg.board(board),
        "error": None,
    }


def analyze_fen(fen, time=1, top_n=3):
    """
    Analyzes a chess position given in FEN notation using the Stockfish engine.

    Input:
        fen: str: A string representing the chess position in Forsyth-Edwards Notation (FEN).
        time: float: The amount of time (in seconds) to allow the engine to analyze the position. Default is 1 second.
        top_n: int: The number of top moves to return. Default is 3

    Return:
        dict: A dictionary containing the evaluation of the position, depth of analysis, and a list of top moves with their evaluations.
    """
    validated = confirm_fen(fen)
    if not validated["valid"]:
        raise ValueError(validated["error"])
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    if time <= 0:
        raise ValueError("time must be greater than 0")

    board = chess.Board(validated["fen"])
    legal_move_count = board.legal_moves.count()
    if legal_move_count == 0:
        outcome = board.outcome(claim_draw=True)
        score = "draw" if outcome is None or outcome.winner is None else "checkmate"
        return {
            "position_evaluation_white": score,
            "depth": 0,
            "top_moves": [],
        }

    with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
        candidate_count = min(top_n, legal_move_count)
        candidate_lines = engine.analyse(
            board,
            chess.engine.Limit(time=time),
            multipv=candidate_count,
        )
        if isinstance(candidate_lines, dict):
            candidate_lines = [candidate_lines]

        position_score = candidate_lines[0]["score"].white()
        top_moves = []
        for line in candidate_lines:
            move = line["pv"][0]
            top_moves.append({
                "move": board.san(move),
                "uci": move.uci(),
                "evaluation_after_move_white": str(line["score"].white()),
                "depth": line.get("depth"),
                "principal_variation": board.variation_san(line.get("pv", [])),
            })

    return {
        "position_evaluation_white": str(position_score),
        "depth": candidate_lines[0].get("depth"),
        "top_moves": top_moves,
    }
