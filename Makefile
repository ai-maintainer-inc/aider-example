.PHONY = build run clean


IMAGE_NAME := aider_harness

HOME := /app


build:
	docker build -t $(IMAGE_NAME) .

# Run Docker container
run:
	@docker run -e OPENAI_API_KEY=$(OPENAI_API_KEY) -v $(shell pwd):$(HOME) $(IMAGE_NAME)

# Remove Docker image
clean:
	@docker rmi -f $(IMAGE_NAME)