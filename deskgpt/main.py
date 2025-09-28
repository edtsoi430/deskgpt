"""
Main CLI interface for DeskGPT
"""
import asyncio
import signal
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config.config import config, validate_config
from .core.command_parser import CommandParser
from .core.logger import setup_logging

console = Console()


class DeskGPT:
    """Main DeskGPT application class"""
    
    def __init__(self):
        self.command_parser = CommandParser()
        self.running = True
    
    async def initialize(self) -> None:
        """Initialize DeskGPT"""
        try:
            validate_config(config)
            await self.command_parser.initialize()
            console.print("🚀 [bold green]DeskGPT initialized successfully![/bold green]")
        except Exception as e:
            console.print(f"❌ [bold red]Failed to initialize DeskGPT:[/bold red] {e}")
            sys.exit(1)
    
    def show_welcome(self) -> None:
        """Display welcome message"""
        welcome_text = Text()
        welcome_text.append("🤖 Welcome to ", style="white")
        welcome_text.append("DeskGPT", style="bold blue")
        welcome_text.append(" - AI Web Automation Assistant", style="white")
        
        welcome_panel = Panel(
            welcome_text,
            title="DeskGPT v1.0.0",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(welcome_panel)
        
        console.print("\n[bold]Commands:[/bold]")
        console.print("  • Type any web automation task in natural language")
        console.print("  • Type 'help' for more information")
        console.print("  • Type 'exit' or press Ctrl+C to quit")
        
        console.print("\n[bold]Examples:[/bold]")
        console.print("  → \"Go to Google and search for TypeScript documentation\"")
        console.print("  → \"Navigate to GitHub and find the most popular Python repositories\"")
        console.print("  → \"Open news website and get the latest headlines\"")
        console.print()
    
    def show_help(self) -> None:
        """Display help information"""
        help_text = """
[bold blue]DeskGPT Help[/bold blue]

DeskGPT uses OpenAI to understand your requests and automate web browsing tasks.

[bold]Supported Actions:[/bold]
  • Navigate to websites
  • Click on elements
  • Type text into forms
  • Scroll pages
  • Take screenshots
  • Extract content from pages

[bold]Tips:[/bold]
  • Be specific about what you want to accomplish
  • Screenshots are automatically saved to ./screenshots/
  • The browser runs in visible mode so you can see what happens
  • Use natural language - DeskGPT will figure out the steps

[bold]Configuration:[/bold]
  • Set OPENAI_API_KEY in your environment or .env file
  • Adjust browser settings in config files if needed

[bold]Examples:[/bold]
  → "Take a screenshot of the current page"
  → "Search for 'machine learning' on Wikipedia"
  → "Find the contact form on this website and fill it out"
"""
        console.print(Panel(help_text, border_style="yellow"))
    
    async def run_interactive(self) -> None:
        """Run interactive CLI mode"""
        self.show_welcome()
        
        while self.running:
            try:
                # Get user input
                prompt = console.input("\n🤖 [bold blue]What would you like me to do?[/bold blue] ")
                
                if not prompt or prompt.isspace():
                    continue
                
                command = prompt.strip().lower()
                
                # Handle special commands
                if command in ['exit', 'quit', 'q']:
                    console.print("\n👋 [yellow]Goodbye![/yellow]")
                    break
                
                if command == 'help':
                    self.show_help()
                    continue
                
                # Execute the automation task
                try:
                    console.print("─" * 60)
                    await self.command_parser.execute_task(prompt)
                    console.print("─" * 60)
                except KeyboardInterrupt:
                    console.print("\n⚠️  [yellow]Task interrupted by user[/yellow]")
                except Exception as e:
                    console.print(f"❌ [red]Error executing task:[/red] {e}")
                
            except KeyboardInterrupt:
                console.print("\n\n🛑 [yellow]Shutting down DeskGPT...[/yellow]")
                break
            except EOFError:
                console.print("\n\n👋 [yellow]Goodbye![/yellow]")
                break
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            await self.command_parser.close()
            console.print("🧹 [green]Cleanup complete[/green]")
        except Exception as e:
            console.print(f"⚠️  [yellow]Cleanup error:[/yellow] {e}")


@click.command()
@click.option(
    '--log-level', 
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARN', 'ERROR'], case_sensitive=False),
    help='Set logging level'
)
@click.option(
    '--log-file',
    type=click.Path(),
    help='Log file path (optional)'
)
@click.option(
    '--command',
    '-c',
    help='Execute a single command and exit'
)
def main(log_level: str, log_file: str, command: str) -> None:
    """DeskGPT - AI-powered web automation assistant"""
    
    # Setup logging
    setup_logging(log_level, log_file)
    
    # Create and run DeskGPT
    app = DeskGPT()
    
    async def run_app():
        # Setup signal handlers
        def signal_handler(signum, frame):
            console.print("\n\n🛑 [yellow]Received interrupt signal, shutting down...[/yellow]")
            app.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            await app.initialize()
            
            if command:
                # Execute single command
                console.print("─" * 60)
                await app.command_parser.execute_task(command)
                console.print("─" * 60)
            else:
                # Run interactive mode
                await app.run_interactive()
                
        finally:
            await app.cleanup()
    
    # Install playwright browsers if needed
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            console.print("⚠️  [yellow]Note: Run 'playwright install chromium' if you encounter browser issues[/yellow]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("⚠️  [yellow]Note: Run 'playwright install chromium' if you encounter browser issues[/yellow]")
    
    # Run the application
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ [bold red]Fatal error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()