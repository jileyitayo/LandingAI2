from typing import List
import asyncio
from app.services.react_models import PageStructure
from concurrent.futures import ThreadPoolExecutor

class ParallelGenerator:
    """Generate multiple components in parallel"""
    
    async def generate_pages_parallel(self, pages: List[PageStructure]):
        """Generate all pages concurrently"""
        
        tasks = []
        for page in pages:
            task = asyncio.create_task(
                self._generate_page_async(page)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return self._combine_results(results)