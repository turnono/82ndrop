"""Tool for generating images using Firebase AI."""
from google.adk.tools import Tool
from firebase_admin import ai

class ImageGenerationTool(Tool):
    """Tool to generate an image from a text prompt."""

    def __init__(self):
        super().__init__(
            name="image_generation_tool",
            description="Generates an image based on a textual description.",
        )

    def _run(self, prompt: str) -> str:
        """Generates an image and returns a message with the image URL."""
        try:
            model = ai.get_generative_model(
                model_name="imagen-3.0-generate-002",
            )
            result = model.generate_images(prompt=prompt)
            
            if result.images:
                # For simplicity, returning a placeholder URL.
                # In a real scenario, you'd upload the image and return the actual URL.
                image_url = f"https://firebasestorage.googleapis.com/v0/b/{result.images[0]._image._gcs_uri.bucket}/o/{result.images[0]._image._gcs_uri.path}?alt=media"
                return f"Image generated successfully! You can view it here: {image_url}"
            else:
                return "Image generation failed. No images were returned."
        except Exception as e:
            return f"An error occurred during image generation: {e}"
