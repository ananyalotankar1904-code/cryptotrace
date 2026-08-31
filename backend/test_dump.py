import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.trace import TracePathItem

t = TracePathItem(**{'from': 'a', 'to': 'b', 'asset': 'ETH', 'value': 1.0, 'transaction_hash': '0x', 'block_number': 1, 'category': 'ext', 'hop': 1})
print("by_alias=True:")
print(t.model_dump(by_alias=True))
print("by_alias=False:")
print(t.model_dump(by_alias=False))
