FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
COPY . /app
RUN pip install -r /app/requirements.txt
