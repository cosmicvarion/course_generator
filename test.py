from dotenv import load_dotenv
load_dotenv()

from langgraph_chains import generate_outline_async, OutlineState
from langgraph_chains import compiled_outline_graph
import asyncio

# async def test_streaming():
#     async for state in generate_outline_async(OutlineState(title="AI", description="Learn AI")):
#         print(f"Yielded: {state.outline}")  # Should print multiple partial outputs

# asyncio.run(test_streaming())

inputs = {"title": "AI", "description": "AI course"}

async def test_stategraph():
    async for chunk in compiled_outline_graph.astream(inputs, stream_mode="updates"):
        print(chunk)

# asyncio.run(test_stategraph())