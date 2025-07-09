from google.adk.tools import BaseTool
from vertexai.preview.reasoning_engines import AdkApp
from ..agent import search_agent

class SearchEnhancementTool(BaseTool):
    """Tool that wraps the search agent for trend enhancement."""
    
    def __init__(self):
        super().__init__(
            name="search_enhancement",
            description="Enhances video concepts with current trends and viral references"
        )
        self.app = AdkApp(agent=search_agent)
    
    async def __call__(self, input_text: str) -> str:
        """
        Call the search agent to enhance the input with trends.
        
        Args:
            input_text: The video concept to enhance
            
        Returns:
            Enhanced video concept with trends
        """
        # Use the search agent to process the input
        response = None
        for event in self.app.stream_query(user_id="test_user", message=input_text):
            response = event
        return response.get("content", {}).get("parts", [{}])[0].get("text", "") 