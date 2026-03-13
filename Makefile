.PHONY: test test-fast install-dev

# Run the full test suite (one-liner per DoD)
test:
	./scripts/test.sh

# Quick run without coverage (faster feedback during development)
test-fast:
	DISCORD_TOKEN=$${DISCORD_TOKEN:-dev-dummy-token} pytest -p no:cov -q

# Install test dependencies into the active virtualenv
install-dev:
	pip install pytest pytest-asyncio pytest-cov python-dotenv
