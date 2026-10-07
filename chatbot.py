#Importing packages
import gradio as gr
from chess_analysis import ChessAnalysis, corrected_turn
from chess_instructions import SYSTEM_INSTRUCTIONS
from models.factory import create_model



#Setting up model
model = create_model()
chess_analysis = ChessAnalysis(model)


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
        yield from chess_analysis.analyze_image(
            image_paths[0], text, request.session_hash
        )
        return

    if request.session_hash in chess_analysis.pending_boards:
        yield from chess_analysis.confirm_board(text, request.session_hash)
        return

    side = corrected_turn(text)
    if side is not None:
        yield from chess_analysis.correct_side(side, request.session_hash)
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

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
