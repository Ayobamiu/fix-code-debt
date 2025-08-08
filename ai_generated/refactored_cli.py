# AI-Generated Refactored Code
# Original file: /Users/usmanayobami/Documents/side projects/fix-code-debt/iterate/cli.py
# Function: ' in content:
# Confidence: 90.0%
# Reasoning: The refactored code is simpler and more readable. The special case for `n == 0` is not necessary because the loop correctly handles this case by not executing at all when `n == 0`. Also, the variable name `result` is more descriptive than `f`, making the code easier to understand. The `result *= i` is a more concise way to write `result = result * i`.

def factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
