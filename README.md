# Project

### Setup

Requirements:

* Docker
* `.env`
* `requirements.txt`

Start the container:

```bash
docker compose up --build
```

### Run chatbot

```bash
docker compose exec jupyter python /home/jovyan/work/app.py
```

Then open:

```text
http://localhost:7860
```

Jupyter is available at:

```text
http://localhost:8888
```
