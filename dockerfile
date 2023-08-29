# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables for paths
ENV CODE_PATH /app/code
ENV AIDER_PATH /app/aider

RUN apt-get update && apt-get install -y less git


# Create directories
RUN mkdir -p $CODE_PATH && \
    mkdir -p $AIDER_PATH

# Set the working directory in the container to /app
WORKDIR $AIDER_PATH

# Copy the current directory contents into the container at /app
COPY . $AIDER_PATH

# upgrade pip
RUN pip install -e .

# Define the command to run on container start
CMD ["python", "-m", "agent_harness.agent_harness"]
