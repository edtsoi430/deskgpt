"""
OpenAI client for generating web automation actions
"""
import json
import logging
from typing import List, Optional

from openai import OpenAI
from ..config.config import config
from ..types.commands import WebAction, ActionType, ScrollDirection, ExtractType

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with OpenAI to generate web automation actions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.openai_api_key)
    
    async def generate_web_actions(
        self, 
        prompt: str, 
        current_url: Optional[str] = None, 
        page_content: Optional[str] = None
    ) -> List[WebAction]:
        """Generate web actions from natural language prompt"""
        
        system_prompt = self._build_system_prompt(current_url, page_content)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("No response from OpenAI")
            
            actions_data = json.loads(content)
            actions = [WebAction(**action_data) for action_data in actions_data]
            return self._validate_actions(actions)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            logger.error(f"Error generating web actions: {e}")
            raise ValueError(f"Failed to generate actions: {e}")
    
    def _build_system_prompt(self, current_url: Optional[str], page_content: Optional[str]) -> str:
        """Build the system prompt for action generation"""
        
        base_prompt = """You are a web automation assistant. Convert user requests into a sequence of web actions.

Available actions:
- navigate: Go to a URL (requires: url)
- click: Click an element (requires: selector). The selector may be a Playwright selector: CSS (preferred), or fallback engines like "text=..." or "xpath=...".
- type: Type text into an input field (requires: selector, text)
- scroll: Scroll the page (requires: scroll_direction - "up" or "down")
- wait: Wait for a specified time in milliseconds (requires: wait_time)
- screenshot: Take a screenshot
- extract: Extract content from page (requires: extract_type - "text", "html", or "links", optional: selector)

IMPORTANT RULES:
1. Use DOM-aware, stable selectors derived from the provided HTML DOM. Prefer IDs (#id), data-testid/data-test attributes, names, aria-labels, and roles before generic classes or element types.
   - If a reliable CSS selector is not possible, use Playwright engines: text=Exact Button Text, or xpath=//...
2. Always include a screenshot action at the end to show the result
3. Be conservative with wait times - use 1000-3000ms typically
4. For navigation, ensure URLs start https://

Response format: Return ONLY a JSON array of actions, no other text.

Example response:
[
  {"type": "navigate", "url": "https://example.com"},
  {"type": "wait", "wait_time": 2000},
  {"type": "click", "selector": "#search-button"},
  {"type": "screenshot"}
]"""
        
        context_info = []
        if current_url:
            context_info.append(f"Current URL: {current_url}")
        if page_content:
            # Provide a larger preview to include meaningful DOM context for selector derivation
            preview = page_content[:4000] + "..." if len(page_content) > 4000 else page_content
            context_info.append(f"Page content preview: {preview}")
        
        if context_info:
            base_prompt += "\n\nCurrent context:\n" + "\n".join(context_info)
        
        return base_prompt
    
    def _validate_actions(self, actions: List[WebAction]) -> List[WebAction]:
        """Validate and filter actions"""
        valid_actions = []
        
        for action in actions:
            if not self._is_valid_action(action):
                logger.warning(f"Skipping invalid action: {action}")
                continue
            valid_actions.append(action)
        
        return valid_actions
    
    def _is_valid_action(self, action: WebAction) -> bool:
        """Check if an action is valid"""
        if action.type not in ActionType:
            logger.warning(f"Invalid action type: {action.type}")
            return False
        
        # Validate required fields for each action type
        if action.type == ActionType.NAVIGATE and not action.url:
            logger.warning("Navigate action missing URL")
            return False
        
        if action.type in [ActionType.CLICK, ActionType.TYPE] and not action.selector:
            logger.warning(f"{action.type} action missing selector")
            return False
        
        if action.type == ActionType.TYPE and not action.text:
            logger.warning("Type action missing text")
            return False
        
        if action.type == ActionType.SCROLL and action.scroll_direction not in ScrollDirection:
            logger.warning(f"Invalid scroll direction: {action.scroll_direction}")
            return False
        
        if action.type == ActionType.EXTRACT and action.extract_type not in ExtractType:
            logger.warning(f"Invalid extract type: {action.extract_type}")
            return False
        
        return True