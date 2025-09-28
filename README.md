# DeskGPT

🤖 An AI-powered desktop automation tool that uses OpenAI and Playwright to automate web browsing tasks through natural language commands.

## Features

- **Natural Language Processing**: Describe what you want to do in plain English
- **Web Automation**: Navigate websites, click elements, fill forms, and extract content
- **Screenshot Capture**: Automatically saves screenshots of actions
- **Error Handling**: Robust error handling with detailed logging
- **Interactive CLI**: Beautiful command-line interface with Rich formatting
- **Async/Await**: Fast, concurrent execution with Python asyncio

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

3. **Set up OpenAI API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Start DeskGPT**:
   ```bash
   deskgpt
   # or run a single command:
   deskgpt -c "Go to Google and search for Python"
   ```

## Example Commands

- "Go to Google and search for Python documentation"
- "Navigate to GitHub and find the most popular Machine Learning repositories"
- "Open news website and get the latest headlines"
- "Take a screenshot of the current page"
- "Find the contact form on this website"

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection
- Playwright (automatically installs Chromium)

## Architecture

```
deskgpt/
├── core/
│   ├── llm_client.py       # OpenAI API integration
│   ├── browser_controller.py  # Playwright web automation
│   ├── command_parser.py   # Main execution engine
│   └── logger.py           # Logging system with Rich
├── types/
│   └── commands.py         # Pydantic data models
├── config/
│   └── config.py           # Configuration management
└── main.py                 # CLI interface with Click
```

## Installation Options

### Using pip (recommended)
```bash
pip install -e .
playwright install chromium
```

### Development setup
```bash
git clone <repository-url>
cd deskgpt
pip install -r requirements.txt
playwright install chromium
```

## Configuration

Set environment variables in `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
BROWSER_TIMEOUT=30000
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
```

## Security

- API keys are stored in environment variables
- Browser runs in sandboxed mode with Playwright
- No file system access by default
- URL validation before navigation
- Comprehensive error handling and logging
