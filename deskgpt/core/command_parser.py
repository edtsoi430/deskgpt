"""
Command parser and execution engine for DeskGPT
"""
import asyncio
import logging
import time
import uuid
from typing import List

from rich.console import Console
from rich.progress import Progress, TaskID

from .llm_client import LLMClient
from .browser_controller import BrowserController
from ..types.commands import AutomationTask, WebAction, CommandResult, TaskStatus

logger = logging.getLogger(__name__)
console = Console()


class CommandParser:
    """Main command parser and execution engine"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.browser_controller = BrowserController()
    
    async def initialize(self) -> None:
        """Initialize the command parser"""
        await self.browser_controller.initialize()
        logger.info("Command parser initialized")
    
    async def execute_task(self, prompt: str) -> AutomationTask:
        """Execute a complete automation task"""
        task_id = self._generate_task_id()
        start_time = time.time()
        
        task = AutomationTask(
            id=task_id,
            prompt=prompt,
            status=TaskStatus.PENDING
        )
        
        try:
            task.status = TaskStatus.RUNNING
            logger.info(f"Task {task_id} started: '{prompt}'")
            
            # Display task header
            console.print(f"\n🤖 [bold blue]Processing:[/bold blue] \"{prompt}\"")
            console.print("📋 [yellow]Generating actions...[/yellow]")
            
            # Get current page context
            current_url = await self.browser_controller.get_current_url()
            page_content = await self.browser_controller.get_page_content() if current_url else None
            
            # Generate actions from LLM
            actions = await self.llm_client.generate_web_actions(
                prompt, current_url, page_content
            )
            task.actions = actions
            
            # Display generated actions
            console.print(f"🎯 [green]Generated {len(actions)} actions:[/green]")
            for i, action in enumerate(actions, 1):
                console.print(f"  {i}. {self._format_action_description(action)}")
            
            console.print("\n🚀 [bold]Executing actions...[/bold]")
            
            # Execute actions with progress tracking
            with Progress() as progress:
                task_progress = progress.add_task(
                    "[cyan]Executing actions...", 
                    total=len(actions)
                )
                
                for i, action in enumerate(actions):
                    console.print(f"\n⏳ [yellow]Step {i + 1}:[/yellow] {self._format_action_description(action)}")
                    
                    # Execute the action
                    result = await self.browser_controller.execute_action(action)
                    task.results.append(result)
                    
                    # Display result
                    if result.success:
                        console.print(f"✅ [green]Success:[/green] {self._format_result_description(result)}")
                        if result.screenshot:
                            console.print(f"📸 [blue]Screenshot saved:[/blue] {result.screenshot}")
                    else:
                        console.print(f"❌ [red]Failed:[/red] {result.error}")
                        console.print("⚠️  [yellow]Continuing with remaining actions...[/yellow]")
                        logger.error(f"Action {i + 1} failed: {result.error}")
                    
                    progress.update(task_progress, advance=1)
                    
                    # Small delay between actions
                    await asyncio.sleep(1)
            
            # Calculate results
            successful_actions = sum(1 for r in task.results if r.success)
            total_actions = len(task.results)
            duration = time.time() - start_time
            
            # Update task status and log completion
            if successful_actions == total_actions:
                task.status = TaskStatus.COMPLETED
                console.print(f"\n🎉 [bold green]Task completed successfully![/bold green] ({successful_actions}/{total_actions} actions succeeded)")
                logger.info(f"Task {task_id} completed successfully in {duration:.2f}s")
            elif successful_actions > 0:
                task.status = TaskStatus.COMPLETED
                console.print(f"\n⚠️  [yellow]Task completed with some failures.[/yellow] ({successful_actions}/{total_actions} actions succeeded)")
                logger.info(f"Task {task_id} completed with failures in {duration:.2f}s")
            else:
                task.status = TaskStatus.FAILED
                console.print(f"\n💥 [bold red]Task failed - no actions succeeded.[/bold red]")
                logger.error(f"Task {task_id} failed completely in {duration:.2f}s")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            duration = time.time() - start_time
            error_msg = str(e)
            
            console.print(f"\n❌ [red]Task execution failed:[/red] {error_msg}")
            logger.error(f"Task {task_id} failed with error: {error_msg}")
            
            # Add error result
            task.results.append(CommandResult(
                success=False,
                error=error_msg
            ))
        
        return task
    
    def _format_action_description(self, action: WebAction) -> str:
        """Format an action for display"""
        if action.type == "navigate":
            return f"Navigate to {action.url}"
        elif action.type == "click":
            return f"Click element: {action.selector}"
        elif action.type == "type":
            return f"Type \"{action.text}\" into {action.selector}"
        elif action.type == "scroll":
            return f"Scroll {action.scroll_direction or 'down'}"
        elif action.type == "wait":
            return f"Wait {action.wait_time}ms"
        elif action.type == "screenshot":
            return "Take screenshot"
        elif action.type == "extract":
            selector_part = f" from {action.selector}" if action.selector else " from page"
            return f"Extract {action.extract_type}{selector_part}"
        else:
            return f"Unknown action: {action.type}"
    
    def _format_result_description(self, result: CommandResult) -> str:
        """Format a result for display"""
        if not result.data:
            return "Action completed"
        
        data = result.data
        if "url" in data:
            return f"Now at {data['url']}"
        elif "action" in data:
            return data["action"].capitalize()
        elif "filename" in data:
            return f"Screenshot: {data['filename']}"
        elif "extract_type" in data:
            return f"Extracted {data['extract_type']}"
        elif "wait_time" in data:
            return f"Waited {data['wait_time']}ms"
        elif "scroll_amount" in data:
            return f"Scrolled {data['scroll_amount']}px"
        else:
            return "Action completed"
    
    def _generate_task_id(self) -> str:
        """Generate a unique task ID"""
        return f"task-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    
    async def close(self) -> None:
        """Close the command parser and cleanup resources"""
        await self.browser_controller.close()
        logger.info("Command parser closed")