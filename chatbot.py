#Importing packages
import os
from google import genai
import gradio as gr
from collections import defaultdict
import json
from board_reader import read_board, check_reading
from fen_converter import board_to_fen
from models.factory import create_model



#Setting up model
model = create_model()

#System instrictuins
# System instructions
SYSTEM_INSTRUCTIONS = """
You are a friendly and knowledgeable chess assistant. You can play chess
against the user, analyze positions, explain openings and strategy, and
help players improve.

When playing a game:
- Ask the user which color they want if they haven't said.
- Use standard algebraic notation (e.g. e4, Nf3, O-O, exd5, e8=Q).
- Keep careful track of the position. Before each move, mentally replay
  the move list so far and make sure your move is legal.
- State your move clearly on its own line, like: "My move: Nf6".
- If the user makes an illegal or unclear move, explain why politely and
  ask them to try again.
- Announce check, checkmate, stalemate, and draws when they happen.
- After your move, add one short sentence about the idea behind it,
  unless the user asks you to stay silent.

When analyzing or teaching:
- Adjust your explanations to the user's level. Assume a beginner unless
  they show otherwise.
- Explain the "why" behind moves: piece activity, king safety, pawn
  structure, tactics, and plans.
- If the user gives a FEN or PGN, use it as the exact position.
- Be honest when a position is complicated or you are unsure. Never
  invent evaluations or claim certainty you don't have.

General:
- Keep answers concise and conversational.
- Stay focused on chess. If asked about unrelated topics, gently steer
  back to chess.
"""



IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


#UI input function
def input2output(inputs, history, request:gr.Request):
    text = inputs.get("text", "")
    files = inputs.get("files", [])

    # Board reading: if the user uploaded an image, read the position
    image_paths = [
        f if isinstance(f, str) else f["path"]
        for f in files
    ]
    image_paths = [p for p in image_paths if p.lower().endswith(IMAGE_EXTENSIONS)]

    if image_paths:
        reading = read_board(
            model,
            image_path=image_paths[0],
            text=text or None,
        )
        problems = check_reading(reading)

        if problems:
            reply = "I couldn't read the board reliably:\n" + "\n".join(f"- {p}" for p in problems)
        else:
            fen = board_to_fen(reading)
            print(fen)
            reply = f"Position (FEN):\n```\n{fen}\n```"

        yield reply
        return
        # Normal chat
    if not text.strip():
        yield "Type a message or upload a chess board image."
        return
    stream = model.stream(instructions=SYSTEM_INSTRUCTIONS, input_text=text, session_id=request.session_hash)
    for event in stream:
        yield event
    



#Running UI
with gr.Blocks() as demo:
    gr.ChatInterface(input2output, 
                            multimodal = True,
                            description="",
                            examples = [
                                {"text": "Let's play a game, I'll be white", "files": []},
                                {"text": "Explain the Sicilian Defense", "files": []},
                            ],

                    )

demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
# demo.launch(theme=gr.themes.Soft())
#demo.launch(debug=True, share=False, inline=True, debug=True)