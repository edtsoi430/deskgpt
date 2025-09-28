"""
Browser automation controller using Playwright
"""
import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright

from ..config.config import config
from ..types.commands import WebAction, CommandResult, ActionType, ScrollDirection, ExtractType

logger = logging.getLogger(__name__)


class BrowserController:
    """Controller for web automation using Playwright"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshot_dir = Path("./screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize the browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=config.browser.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create new page
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({
                'width': config.browser.viewport_width,
                'height': config.browser.viewport_height
            })
            
            # Set default timeout
            self.page.set_default_timeout(config.browser.timeout)
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.close()
            raise
    
    async def execute_action(self, action: WebAction) -> CommandResult:
        """Execute a single web action"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        try:
            if action.type == ActionType.NAVIGATE:
                return await self._navigate(action.url)
            elif action.type == ActionType.CLICK:
                return await self._click(action.selector)
            elif action.type == ActionType.TYPE:
                return await self._type(action.selector, action.text)
            elif action.type == ActionType.SCROLL:
                return await self._scroll(action.scroll_direction or ScrollDirection.DOWN)
            elif action.type == ActionType.WAIT:
                return await self._wait(action.wait_time or 1000)
            elif action.type == ActionType.SCREENSHOT:
                return await self._screenshot()
            elif action.type == ActionType.EXTRACT:
                return await self._extract(
                    action.extract_type or ExtractType.TEXT, 
                    action.selector
                )
            else:
                return CommandResult(
                    success=False,
                    error=f"Unknown action type: {action.type}"
                )
                
        except Exception as e:
            logger.error(f"Error executing action {action.type}: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )
    
    async def _navigate(self, url: str) -> CommandResult:
        """Navigate to a URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        await self.page.goto(url, wait_until='networkidle')
        current_url = self.page.url
        
        return CommandResult(
            success=True,
            data={"url": current_url, "action": "navigated"}
        )
    
    async def _click(self, selector: str) -> CommandResult:
        """Click on an element with robust selector fallbacks.
        Supports Playwright engines: CSS (default), text=..., xpath=...
        """
        try:
            # Try as-is (CSS or engine provided by LLM)
            await self.page.wait_for_selector(selector, timeout=7000)
            await self.page.click(selector)
        except Exception:
            # Fallback heuristics
            clicked = False
            errors: List[str] = []

            # If it looks like a text string without engine prefix, try text= selectors
            if not selector.startswith(("text=", "xpath=", "css=")):
                text_candidate = selector.strip().strip('"\'')
                try:
                    await self.page.get_by_text(text_candidate, exact=True).click(timeout=5000)
                    clicked = True
                except Exception as e:
                    errors.append(f"text exact failed: {e}")
                    try:
                        await self.page.get_by_text(text_candidate).click(timeout=5000)
                        clicked = True
                    except Exception as e2:
                        errors.append(f"text partial failed: {e2}")

            # Try xpath engine if input seems like XPath or as a last resort
            if not clicked:
                xpath_selector = selector if selector.startswith("xpath=") else f"xpath={selector}"
                try:
                    await self.page.locator(xpath_selector).first.click(timeout=5000)
                    clicked = True
                except Exception as e:
                    errors.append(f"xpath failed: {e}")

            # Try role/button if it looks like a button-like label
            if not clicked:
                try:
                    await self.page.get_by_role("button", name=selector, exact=True).click(timeout=5000)
                    clicked = True
                except Exception as e:
                    errors.append(f"role button exact failed: {e}")

            if not clicked:
                raise RuntimeError("Failed to click element with provided selector and fallbacks. " + "; ".join(errors))

        await asyncio.sleep(1)
        return CommandResult(
            success=True,
            data={"selector": selector, "action": "clicked"}
        )
    
    async def _type(self, selector: str, text: str) -> CommandResult:
        """Type text into an input field"""
        await self.page.wait_for_selector(selector, timeout=10000)
        
        # Clear existing text and type new text
        await self.page.click(selector)
        await self.page.keyboard.press('Control+KeyA')
        await self.page.fill(selector, text)
        
        return CommandResult(
            success=True,
            data={"selector": selector, "text": text, "action": "typed"}
        )
    
    async def _scroll(self, direction: ScrollDirection) -> CommandResult:
        """Scroll the page"""
        scroll_amount = 500 if direction == ScrollDirection.DOWN else -500
        
        await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(1)
        
        return CommandResult(
            success=True,
            data={"direction": direction.value, "scroll_amount": scroll_amount}
        )
    
    async def _wait(self, milliseconds: int) -> CommandResult:
        """Wait for a specified amount of time"""
        await asyncio.sleep(milliseconds / 1000.0)
        
        return CommandResult(
            success=True,
            data={"wait_time": milliseconds}
        )
    
    async def _screenshot(self) -> CommandResult:
        """Take a screenshot"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot-{timestamp}.png"
        filepath = self.screenshot_dir / filename
        
        await self.page.screenshot(path=str(filepath), full_page=True)
        
        return CommandResult(
            success=True,
            data={"filename": filename, "path": str(filepath)},
            screenshot=str(filepath)
        )
    
    async def _extract(self, extract_type: ExtractType, selector: Optional[str] = None) -> CommandResult:
        """Extract content from the page"""
        data = None
        
        if extract_type == ExtractType.TEXT:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    data = await element.text_content()
            else:
                data = await self.page.evaluate("document.body.textContent")
                
        elif extract_type == ExtractType.HTML:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    data = await element.inner_html()
            else:
                data = await self.page.content()
                
        elif extract_type == ExtractType.LINKS:
            links = await self.page.evaluate("""
                Array.from(document.querySelectorAll('a')).map(link => ({
                    text: link.textContent?.trim(),
                    href: link.href,
                    title: link.title
                }))
            """)
            data = links
        
        return CommandResult(
            success=True,
            data={"extract_type": extract_type.value, "content": data}
        )
    
    async def get_current_url(self) -> str:
        """Get the current page URL"""
        return self.page.url if self.page else ""
    
    async def get_page_content(self) -> str:
        """Get the current page text content"""
        if not self.page:
            return ""
        
        try:
            # Return full HTML content for DOM-aware planning
            content = await self.page.content()
            return content or ""
        except Exception as e:
            logger.warning(f"Failed to get page content: {e}")
            return ""
    
    async def close(self) -> None:
        """Close the browser and cleanup resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            raise