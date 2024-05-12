from dataclasses import dataclass


@dataclass
class Page:
    id: str
    story_id: str
    page_number: int
    image_url: str
    story_text: str
    new_story_text: str
    new_image_description: str
    new_image_url: str
    
    
@dataclass
class Story:
    id: str
    title: str
    url: str
    pages: list[Page]
