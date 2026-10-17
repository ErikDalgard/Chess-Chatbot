# Chess Coach

A chess assistant with a Gradio interface for analyzing board screenshots, practicing puzzles, and learning chess concepts.

## Features

- **Position analysis:** Upload a board screenshot (PNG, JPG, JPEG, or WebP). The assistant reconstructs the position and displays a chessboard for you to confirm or correct before analysis. Stockfish evaluates the confirmed position and finds up to three candidate moves, which the model explains.
- **Chess puzzles:** Request a puzzle by rating or theme, such as a beginner puzzle around rating 800 or a mate-in-one. Puzzles appear on a visual chessboard. Ask for hints, suggest a solution, or request the answer.
- **Chess explanations:** Ask about rules, openings, tactics, and strategy, with conversational follow-up questions.
- **Chat interface:** Streamed replies, board image uploads, and example prompts in a themed Chess Coach UI.

Puzzle requests use a dedicated puzzle assistant; image uploads go to position analysis. The included dataset contains 250,000 one-move puzzles in `puzzles.json.zst`. Keep this file in the project root. If it is missing, the loader attempts to build it from `lichess_db_puzzle.csv.zst`, which is not included.

The upload flow analyzes a single position, rather than reviewing an entire game. Ordinary text questions go to the language model; Stockfish analysis runs after an uploaded board is confirmed.

## Setup

Requirements:

- Docker with Docker Compose.
- A `.env` file in the project root with the selected model provider and API key.

The model factory reads `LLM_PROVIDER` (`gateway` or `gemini`), `LLM_MODEL`, and the corresponding `GATEWAY_API_KEY` or `GEMINI_API_KEY`. For example, configure the gateway provider with:

```dotenv
LLM_PROVIDER=gateway
LLM_MODEL=your-gateway-model-id
GATEWAY_API_KEY=your-api-key
DEVICE=cpu
```

Replace the model ID with one available through your gateway that supports image input and tool calling. 

Run the following commands from the project root. Start the container:

```bash
docker compose up --build
```

## Run the chatbot

In a second terminal, run:

```bash
docker compose exec -w /home/jovyan/work jupyter python chatbot.py
```

Open http://localhost:7860 in your browser.

