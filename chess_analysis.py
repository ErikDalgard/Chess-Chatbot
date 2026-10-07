import json
import re
import chess
import chess.svg
import gradio as gr

from analyze_fen import analyze_fen
from board_reader import read_board, check_reading, SideToMove
from fen_converter import board_to_fen


def corrected_turn(text):
    """Recognize a short turn correction, without treating questions as corrections."""
    match = re.fullmatch(
        r"\s*(?:(?:sorry|actually|correction)[,!:]?\s*)*"
        r"(?:(?:it\s+is|it's)\s+)?(white|black)(?:'s)?\s+"
        r"(?:to\s+move|turn(?:\s+to\s+move)?)(?:\s+instead)?[.!]?\s*",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1)[0].lower() if match else None


MOVE_EXPLANATION_INSTRUCTIONS = """
You explain Stockfish analysis to a chess beginner.
Use the supplied FEN as the exact position and the supplied Stockfish analysis
as the source of truth for evaluations, move rankings, and principal variations.
All scores are from White's perspective: positive favors White, negative favors
Black. Numeric scores are centipawns (100 = one pawn); # indicates mate.
Do not invent or replace evaluations, change the move order, or suggest other moves.
For each supplied top move, give its SAN move name and 1-3 concise sentences
explaining its concrete purpose in this position (such as a threat, defense,
piece activity, king safety, or pawn structure). Use the principal variation to
support tactical explanations, accounting for the opponent's best response.
Do not claim a forced win, material gain, or tactic unless the supplied line
supports it. Be clear when an explanation is uncertain. These are the best
moves found within the engine's search, not a proof of optimality.
The evaluation and ranked move list are already displayed, so focus on why
the moves are useful without repeating the full analysis or FEN.
If the supplied move list is empty, explain the terminal position briefly.
""".strip()


def format_analysis(analysis):
    """Return the engine evaluation and ranked moves as display-ready Markdown."""
    evaluation = (
        f"\n\nStockfish evaluation (White's perspective): "
        f"{analysis['position_evaluation_white']}"
        "\nNumeric scores are in centipawns (100 = one pawn); positive favors White, negative favors Black. # indicates mate."
    )
    moves = "\n\nTop next moves:\n" + "\n".join(
        f"{index}. **{move['move']}** — {move['evaluation_after_move_white']}"
        for index, move in enumerate(analysis["top_moves"], start=1)
    )
    return evaluation + moves


def explain_moves(model, fen, analysis, session_id):
    """Stream cumulative explanations, preserving the engine data and chat session."""
    prompt = (
        "Explain the moves in this engine analysis. This is the current position; "
        "it supersedes earlier positions and evaluations in this conversation:\n"
        + json.dumps({"fen": fen, "stockfish_analysis": analysis})
    )
    return model.stream(
        instructions=MOVE_EXPLANATION_INSTRUCTIONS,
        input_text=prompt,
        session_id=session_id,
    )


class ChessAnalysis:
    """Manage image analysis and the latest position for each chat session."""

    def __init__(self, model):
        self.model = model
        self.session_fens = {}
        self.pending_boards = {}

    def preview_board(self, fen, reply, session_id):
        """Show the reconstructed position and wait for confirmation."""
        self.pending_boards[session_id] = (fen, reply)
        svg = chess.svg.board(chess.Board(fen), size=360)
        yield [gr.HTML(svg), reply + "\n\nDoes this board look correct? Reply **yes** to analyze it, or **no** to correct it."]

    def confirm_board(self, text, session_id):
        """Confirm, reject, or revise a pending board before calling Stockfish."""
        fen, reply = self.pending_boards[session_id]
        answer = text.strip().lower().rstrip(".! ")
        if answer in {"yes", "y", "yeah", "yep", "correct", "looks correct", "looks good", "ok", "okay"}:
            self.pending_boards.pop(session_id)
            yield from self.analyze_position(fen, "Board confirmed.", session_id)
        elif answer in {"no", "n", "nope", "incorrect", "wrong"}:
            yield "Please reupload a clearer image, or describe the corrections (for example, ‘the white knight is on f3, not g1’)."
        elif corrected_turn(text) is not None:
            fields = fen.split()
            fields[1] = corrected_turn(text)
            fields[3] = "-"
            fen = " ".join(fields)
            color = "White" if fields[1] == "w" else "Black"
            yield from self.preview_board(fen, f"**{color} to move.**", session_id)
        elif text.strip():
            reading = read_board(
                self.model,
                text=f"Starting position FEN: {fen}\nApply only these user corrections and return the complete updated board: {text}",
            )
            problems = check_reading(reading)
            if problems:
                yield "I couldn't apply the correction reliably. Please reupload the image or clarify: " + "; ".join(problems)
                return
            fen = board_to_fen(reading, default_side=fen.split()[1])
            color = "White" if fen.split()[1] == "w" else "Black"
            yield from self.preview_board(fen, f"Updated board. **{color} to move.**", session_id)
        else:
            yield "Reply yes to confirm the board, or no to correct it."

    def analyze_position(self, fen, reply, session_id):
        """Analyze and remember a position, then stream its explanation."""
        yield reply + "\n\nAnalyzing with Stockfish…"
        try:
            analysis = analyze_fen(fen)
        except ValueError as error:
            yield reply + f"\n\nThe position could not be analyzed: {error}"
            return

        self.session_fens[session_id] = fen
        reply += format_analysis(analysis)
        yield reply + "\n\nExplaining the moves…"
        for explanation in explain_moves(self.model, fen, analysis, session_id):
            yield reply + "\n\nWhy these moves work:\n" + explanation

    def analyze_image(self, image_path, text, session_id):
        """Read an uploaded board and show it for confirmation."""
        self.session_fens.pop(session_id, None)
        self.pending_boards.pop(session_id, None)
        reading = read_board(
            self.model,
            image_path=image_path,
            text=text or None,
        )
        problems = check_reading(reading)

        if problems:
            reply = "I couldn't read the board reliably:\n" + "\n".join(f"- {p}" for p in problems)
        else:
            fen = board_to_fen(reading)
            color = "White" if fen.split()[1] == "w" else "Black"
            reply = f"**{color} to move.**"
            if reading.side_to_move == SideToMove.unknown:
                reply += " (Assumed — say ‘Black to move’ to change it.)"
            if reading.notes:
                reply += f"\nBoard reader note: {reading.notes}"

            yield from self.preview_board(fen, reply, session_id)
            return

        yield reply
        return

    def correct_side(self, side, session_id):
        """Update whose turn it is and stream fresh engine analysis."""
        previous_fen = self.session_fens.get(session_id)
        if previous_fen is None:
            yield "Upload a board image first so I can correct whose turn it is."
            return
        fields = previous_fen.split()
        fields[1] = side
        # An en passant target from the previous turn cannot apply to the new turn.
        fields[3] = "-"
        fen = " ".join(fields)
        color = "White" if side == "w" else "Black"
        reply = f"Corrected to **{color} to move.**"
        yield from self.analyze_position(fen, reply, session_id)
        return
