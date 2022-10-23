# syntax=docker/dockerfile:1
FROM python:3 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# Install GDAL libraries and psql client so we can use ```python manage.py dbshell```
RUN apt-get update &&\
    apt-get install -y binutils libproj-dev gdal-bin postgresql-client