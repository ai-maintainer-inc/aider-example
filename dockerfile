# Use an official Python runtime as a parent image
FROM python:3.9-slim

ENV HOME /app/

RUN apt-get update && apt-get install -y less git universal-ctags

# Create directories
RUN mkdir -p $HOME

# Set the working directory in the container to /app
WORKDIR $HOME

# Copy the current directory contents into the container at /app
COPY . $HOME

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Define the command to run on container start
CMD ["python", "main.py"]
