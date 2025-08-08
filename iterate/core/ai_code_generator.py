"""
True AI-powered code generation using OpenAI API.
Provides actual AI-generated code improvements.
"""

import openai
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class AICodeSuggestion:
    """An AI-generated code suggestion."""
    file_path: str
    function_name: str
    suggestion_type: str
    description: str
    original_code: str
    ai_generated_code: str
    confidence: float
    reasoning: str


class AICodeGenerator:
    """True AI-powered code generator using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("⚠️  No OpenAI API key found. AI generation will be disabled.")
    
    def generate_refactoring_suggestion(self, file_path: str, function_code: str, complexity_metrics: Dict[str, Any]) -> Optional[AICodeSuggestion]:
        """Generate AI-powered refactoring suggestion."""
        if not self.api_key:
            return None
        
        prompt = f"""
        Analyze this Python function and provide a refactored version that improves:
        1. Readability
        2. Maintainability
        3. Performance
        4. Code structure

        Function code:
        {function_code}

        Complexity metrics:
        - Cyclomatic complexity: {complexity_metrics.get('cyclomatic_complexity', 'unknown')}
        - Lines of code: {complexity_metrics.get('lines_of_code', 'unknown')}
        - Parameter count: {complexity_metrics.get('parameter_count', 'unknown')}

        Provide:
        1. A refactored version of the function
        2. Explanation of the improvements
        3. Any additional helper functions needed
        4. Best practices applied

        Format the response as:
        REFACTORED_CODE:
        ```python
        [refactored code here]
        ```

        EXPLANATION:
        [explanation of improvements]

        HELPER_FUNCTIONS:
        ```python
        [any helper functions needed]
        ```

        BEST_PRACTICES:
        [list of best practices applied]
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer specializing in code refactoring and best practices."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Debug: Print the AI response for troubleshooting
            print(f"🔍 AI Response Preview: {ai_response[:200]}...")
            
            # Parse the AI response
            refactored_code = self._extract_code_block(ai_response, "REFACTORED_CODE")
            explanation = self._extract_section(ai_response, "EXPLANATION")
            helper_functions = self._extract_code_block(ai_response, "HELPER_FUNCTIONS")
            best_practices = self._extract_section(ai_response, "BEST_PRACTICES")
            
            # If no code was extracted, try to extract any code block
            if not refactored_code:
                refactored_code = self._extract_any_code_block(ai_response)
            
            return AICodeSuggestion(
                file_path=file_path,
                function_name=self._extract_function_name(function_code),
                suggestion_type="ai_refactoring",
                description=f"AI-generated refactoring for complex function",
                original_code=function_code,
                ai_generated_code=refactored_code,
                confidence=0.9,
                reasoning=explanation
            )
            
        except Exception as e:
            print(f"❌ Error generating AI refactoring: {e}")
            return None
    
    def generate_test_suggestion(self, file_path: str, function_code: str, function_name: str) -> Optional[AICodeSuggestion]:
        """Generate AI-powered test suggestion."""
        if not self.api_key:
            return None
        
        prompt = f"""
        Generate comprehensive unit tests for this Python function:

        Function code:
        {function_code}

        Function name: {function_name}

        Provide:
        1. Complete unit tests using unittest framework
        2. Test cases for normal operation
        3. Test cases for edge cases
        4. Test cases for error conditions
        5. Mock examples if needed

        Format the response as:
        TEST_CODE:
        ```python
        [complete test code here]
        ```

        TEST_CASES:
        [explanation of test cases]

        MOCKING:
        [any mocking needed]
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in Python testing and unit test generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            ai_response = response.choices[0].message.content
            
            test_code = self._extract_code_block(ai_response, "TEST_CODE")
            test_cases = self._extract_section(ai_response, "TEST_CASES")
            mocking = self._extract_section(ai_response, "MOCKING")
            
            return AICodeSuggestion(
                file_path=file_path,
                function_name=function_name,
                suggestion_type="ai_test_generation",
                description=f"AI-generated comprehensive tests for {function_name}",
                original_code=function_code,
                ai_generated_code=test_code,
                confidence=0.85,
                reasoning=f"Test cases: {test_cases}\nMocking: {mocking}"
            )
            
        except Exception as e:
            print(f"❌ Error generating AI tests: {e}")
            return None
    
    def generate_documentation_suggestion(self, file_path: str, function_code: str, function_name: str) -> Optional[AICodeSuggestion]:
        """Generate AI-powered documentation suggestion."""
        if not self.api_key:
            return None
        
        prompt = f"""
        Generate comprehensive documentation for this Python function:

        Function code:
        {function_code}

        Function name: {function_name}

        Provide:
        1. Google-style docstring
        2. Parameter descriptions
        3. Return value description
        4. Exception descriptions
        5. Usage examples

        Format the response as:
        DOCSTRING:
        ```python
        [complete docstring here]
        ```

        PARAMETERS:
        [detailed parameter descriptions]

        RETURNS:
        [return value description]

        EXCEPTIONS:
        [exception descriptions]

        EXAMPLES:
        [usage examples]
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in Python documentation and docstring generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            docstring = self._extract_code_block(ai_response, "DOCSTRING")
            parameters = self._extract_section(ai_response, "PARAMETERS")
            returns = self._extract_section(ai_response, "RETURNS")
            exceptions = self._extract_section(ai_response, "EXCEPTIONS")
            examples = self._extract_section(ai_response, "EXAMPLES")
            
            return AICodeSuggestion(
                file_path=file_path,
                function_name=function_name,
                suggestion_type="ai_documentation",
                description=f"AI-generated documentation for {function_name}",
                original_code=function_code,
                ai_generated_code=docstring,
                confidence=0.9,
                reasoning=f"Parameters: {parameters}\nReturns: {returns}\nExceptions: {exceptions}\nExamples: {examples}"
            )
            
        except Exception as e:
            print(f"❌ Error generating AI documentation: {e}")
            return None
    
    def _extract_code_block(self, response: str, section: str) -> str:
        """Extract code block from AI response."""
        try:
            start_marker = f"{section}:\n```python\n"
            end_marker = "\n```"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                return ""
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                return response[start_idx:]
            
            return response[start_idx:end_idx].strip()
        except Exception:
            return ""
    
    def _extract_section(self, response: str, section: str) -> str:
        """Extract text section from AI response."""
        try:
            start_marker = f"{section}:\n"
            end_marker = "\n\n"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                return ""
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                return response[start_idx:]
            
            return response[start_idx:end_idx].strip()
        except Exception:
            return ""
    
    def _extract_function_name(self, code: str) -> str:
        """Extract function name from code."""
        try:
            lines = code.split('\n')
            for line in lines:
                if line.strip().startswith('def '):
                    return line.split('def ')[1].split('(')[0].strip()
        except Exception:
            pass
        return "unknown_function"
    
    def _extract_any_code_block(self, response: str) -> str:
        """Extract any code block from AI response."""
        try:
            # Look for ```python blocks
            start_marker = "```python"
            end_marker = "```"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                # Try without language specification
                start_marker = "```"
                start_idx = response.find(start_marker)
                if start_idx == -1:
                    return ""
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                return response[start_idx:].strip()
            
            return response[start_idx:end_idx].strip()
        except Exception:
            return "" 