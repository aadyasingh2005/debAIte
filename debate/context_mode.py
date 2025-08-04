from enum import Enum

class ContextMode(str, Enum):
    FULL        = "full"        # send entire history
    SUMMARIZED  = "summarized"  # send only summary
    HYBRID      = "hybrid"      # summary + sliding window
