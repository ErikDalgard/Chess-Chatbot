#Importing packages
import os
from google import genai
import gradio as gr
from collections import defaultdict
import json
from analyze_fen import analyze_fen, confirm_fen


#Setting up model
API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)
default_model = ""


#System instrictuins
SYSTEM_INSTRUCTIONS = """
"""

#Chat history
chats = defaultdict(lambda: None)



#UI input function
def input2output(inputs, history, request:gr.Request):
    stream_input = ""



    #Streaming the response
    stream = client.interactions.create(
        model = default_model,
        system_instruction=SYSTEM_INSTRUCTIONS,
        input=stream_input,
        stream=True
    )


#Running UI
with gr.Blocks() as demo:
    gr.ChatInterface(input2output, 
                            multimodal = True,
                            description="",
                            examples = [
                                        {"text": "", "files": []},
                                        {"text": "", "files": []},
                            ]

                    )
demo.launch(theme=gr.themes.Soft())
