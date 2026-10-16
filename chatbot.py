#Importing packages
import gradio as gr
from chess_analysis import ChessAnalysis, corrected_turn
from chess_instructions import SYSTEM_INSTRUCTIONS
from models.factory import create_model
from puzzle.puzzle_assistant import PuzzleAssistant
from enum import Enum


#Setting up model
model = create_model()
chess_analysis = ChessAnalysis(model)


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

puzzle_assistant = PuzzleAssistant(model)
# puzzle_assistant.test()

class Mode(str, Enum):
    CHESS_ASSISTANT = "chess_assistant"
    PUZZLE_ASSISTANT = "puzzle_assistant"

mode = Mode.CHESS_ASSISTANT
CHESS_ASSISTANT_SESSION_ID = 1 
PUZZLE_ASSISTANT_SESSION_ID = 2 # Use a different session for the puzzle assistant

def change_mode():
    global mode
    if mode == Mode.PUZZLE_ASSISTANT:
        yield "Redirecting to the general chess assistant..."
        mode = Mode.CHESS_ASSISTANT
        model.clear_history(PUZZLE_ASSISTANT_SESSION_ID)
    else:
        yield "Redirecting to the puzzle chess assistant..."
        mode = Mode.PUZZLE_ASSISTANT
        model.clear_history(CHESS_ASSISTANT_SESSION_ID)






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

    global mode
    if mode == Mode.PUZZLE_ASSISTANT:
        stream = puzzle_assistant.input2output(text, image_paths, PUZZLE_ASSISTANT_SESSION_ID)
        for event in stream:
            if event["flag"]:
                if event["flag"] == "change_mode":
                    yield from change_mode()
                    yield from input2output(inputs, history, request)
                    return
            else:
                yield event["content"]
        return
    elif mode == Mode.CHESS_ASSISTANT:
        # Switch to puzzle assistant mode if the puzzle assistant says so and if there are no images uploaded
        if not image_paths and puzzle_assistant.switch_to_puzzle_mode(text):
            yield from change_mode()
            yield from input2output(inputs, history, request)
            return


    if image_paths:
        yield from chess_analysis.analyze_image(
            image_paths[0], text, CHESS_ASSISTANT_SESSION_ID
        )
        return

    if CHESS_ASSISTANT_SESSION_ID in chess_analysis.pending_boards:
        yield from chess_analysis.confirm_board(text, CHESS_ASSISTANT_SESSION_ID)
        return

    side = corrected_turn(text)
    if side is not None:
        yield from chess_analysis.correct_side(side, CHESS_ASSISTANT_SESSION_ID)
        return

    # Normal chat
    if not text.strip():
        yield "Type a message or upload a chess board image."
        return
    stream = model.stream(instructions=SYSTEM_INSTRUCTIONS, input_text=text, session_id=CHESS_ASSISTANT_SESSION_ID)
    for event in stream:
        yield event
    

#Running UI
"""with gr.Blocks() as demo:
    gr.ChatInterface(input2output, 
                            multimodal = True,
                            description="",
                            examples = [
                                {"text": "Let's play a game, I'll be white", "files": []},
                                {"text": "Explain the Sicilian Defense", "files": []},
                            ],

                    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())"""

#Running UI
import os

PAWN = os.path.join(os.path.dirname(__file__), "pawn.png")

theme = gr.themes.Soft(primary_hue="emerald", neutral_hue="stone").set(
    body_background_fill="#e6eee1",          # page background (light mode)
    body_background_fill_dark="#18211a",     # page background (dark mode)
    block_background_fill="#f6f9f3",         # panels, like the chat area
    block_background_fill_dark="#222d24",
    background_fill_primary="#f6f9f3",
    background_fill_primary_dark="#222d24",
)

with gr.Blocks(title="Chess Coach") as demo:
    gr.ChatInterface(
        input2output,
        multimodal=True,
        title="♞ Chess Coach",
        description="Ask about openings and strategy, play a game, or upload a screenshot of a board to get the best move explained.",
        chatbot=gr.Chatbot(
            height=560,
            avatar_images=(None, PAWN),   # (user, bot)
            placeholder="**Upload a board or ask a chess question to get started.**",
        ),
        examples=[
            {"text": "Let's play a game, I'll be white", "files": []},
            {"text": "Explain the Sicilian Defense", "files": []},
        ],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=theme)
