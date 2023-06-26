import math
import random


def exponential_backoff(attempt: int, base_delay: float) -> float:
    """
    Exponential backoff starting with 200ms +- 0...40ms jitter
    """
    delay = math.pow(2, attempt) * base_delay / 2.0
    random_sum = delay * 0.1 * random.random()
    return delay + random_sum
