.PHONY = build run clean


IMAGE_NAME := aider_harness

HOME := /app


build:
	docker build -t $(IMAGE_NAME) .

# Run Docker container
run:
	@docker run -e OPENAI_API_KEY=$(OPENAI_API_KEY) -v $(shell pwd):$(HOME) --network platform-network $(IMAGE_NAME)

run-debug:
	docker run -v $(shell pwd):$(HOME) --network platform-network --name ${IMAGE_NAME} $(IMAGE_NAME) tail -f /dev/null


# Remove Docker image
clean:
	@docker rmi -f $(IMAGE_NAME)