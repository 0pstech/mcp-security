curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new directory for our project
uv init project_name
cd project_name

# Create virtual environment and activate it
uv venv
source .venv/bin/activate

# Install dependencies
uv add "mcp[cli]" httpx

# Create our server file
touch project_name.py