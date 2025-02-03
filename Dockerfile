FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 8000

COPY ./app /code/app

CMD ["uvicorn", "run", "main:app", "--port", "8000"]
