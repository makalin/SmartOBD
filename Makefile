# SmartOBD Makefile

.PHONY: help install test lint clean build docker-build docker-run docker-stop

# Default target
help:
	@echo "SmartOBD - Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker containers"
	@echo "  setup        - Initial setup"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	python -m pytest tests/ -v

# Run linting
lint:
	black smartobd/ --check
	flake8 smartobd/
	mypy smartobd/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python setup.py sdist bdist_wheel

# Build Docker image
docker-build:
	docker build -t smartobd .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker containers
docker-stop:
	docker-compose down

# Initial setup
setup:
	mkdir -p data logs models exports
	cp config.yaml config_local.yaml
	@echo "Setup complete! Edit config_local.yaml with your settings."

# Development server
dev:
	python smartobd.py --dashboard --debug

# Production server
prod:
	python smartobd.py --monitor

# Connect to OBD
connect:
	python smartobd.py --connect

# Export data
export:
	python smartobd.py --export

# Database backup
backup:
	cp data/smartobd.db data/smartobd_backup_$(shell date +%Y%m%d_%H%M%S).db

# Database restore
restore:
	@echo "Usage: make restore BACKUP_FILE=data/smartobd_backup_YYYYMMDD_HHMMSS.db"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE"; exit 1; fi
	cp $(BACKUP_FILE) data/smartobd.db

# Show logs
logs:
	tail -f logs/smartobd.log

# Show status
status:
	python smartobd.py --status 