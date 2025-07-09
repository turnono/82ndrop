from google.adk.tools import BaseTool
from ..agent import search_agent

class SearchEnhancementTool(BaseTool):
    """Tool that wraps the search agent for trend enhancement."""
    
    def __init__(self):
        super().__init__(
            name="search_enhancement",
            description="Enhances video concepts with current trends and viral references"
        )
    
    async def __call__(self, input_text: str) -> str:
        """
        Call the search agent to enhance the input with trends.
        
        Args:
            input_text: The video concept to enhance
            
        Returns:
            Enhanced video concept with trends
        """
        # Use the search agent to process the input
        response = await search_agent.process(input_text)
        return response.get("search_enhancement_response", "") 