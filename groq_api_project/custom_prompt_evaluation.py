
from dotenv import load_dotenv
from groq import Groq
from statistics import mean

import json
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def add_user_message(messages: list[dict], content: str) -> None:
  messages.append({
      "role": "user",
      "content": content
  })


def add_assistant_message(messages: list[dict], content: str) -> None:
  messages.append({
      "role": "assistant",
      "content": content
  })


def run_prompt(test_case: str) -> str:
  """Merges the test case into the prompt and runs it through the model."""
  prompt = f"""  Here is a task: {test_case["task"]}
  Please write a Python function that completes the task.
  """

  messages = []
  add_user_message(messages, prompt)
  output = chat(messages)
  return output


def grade_by_model(test_case: str, output: str) -> dict:
  """Grades the output using the model."""

  eval_prompt = f"""
    You are an expert Python code reviewer. 
    Your task is to evaluate the quality of the AI-generated Python code for a specific task.
    
    Original Task:
    <task>
      {test_case["task"]}
    </task>
  
    Solution to evaluate:
    <solution>
      {output}
    </solution>
    
    Provide your evaluation as a structured JSON object with the following fields:
    - "reasoning": A concise explanation of your assessment
    - "score": A number between 1-10

    Respond with only the JSON object, without any additional text or formatting.
    Keep your evaluation concise and direct.
    Example output:
    ```json
    {{
      "reasoning": "The code is well-organized and uses functions effectively, but it lacks error handling and could be optimized for performance.",
      "score": 7
    }}
    ```

    Make sure that the JSON object is valid and can be parsed without errors and contains all required fields - reasoning and score.
    """

  messages = []
  add_user_message(messages, eval_prompt)
  add_assistant_message(messages, "```json")
  eval_response = chat(messages, stop_sequence="```")
  return json.loads(eval_response)


def run_test_case_evaluation(test_case: str):
  """Runs the test case and grades the output."""
  output = run_prompt(test_case)

  model_grade = grade_by_model(test_case, output)
  score = model_grade["score"]
  reasoning = model_grade["reasoning"]

  return {
      "test_case": test_case,
      "output": output,
      "score": score,
      "reasoning": reasoning
  }


def run_evaluation(eval_dataset):
  """Runs all test cases in the evaluation dataset and reports results."""
  results = []
  for test_case in eval_dataset:
    result = run_test_case_evaluation(test_case)
    results.append(result)

  average_score = mean(result["score"] for result in results)
  print(f"Average Score: {average_score:.2f}")

  return results


def chat(messages: list[dict], stop_sequence: str = None) -> str:
  params = {
      "messages": messages,
      "model": os.getenv("GROQ_API_MODEL")
  }

  if stop_sequence:
    params["stop"] = stop_sequence

  response = client.chat.completions.create(**params)
  return response.choices[0].message.content


# conversation history; each dict is one turn
messages: list[dict] = []

# Prompt to generate evaluation dataset.
eval_dataset_prompt = """
  Generate a evaluation dataset for a prompt evaluation.
  The dataset will be used to evaluate prompts that generate
  Python code for a specific task. Generate an array of JSON
  objects each representing a task that requires Python to complete.

  Example output:
  ```json
  [
    {
      "task": "Description of task"
    },
    {
      "task": "Description of task"
    }
  ]
  ```
  * Focus on tasks that can be solved by writing a single Python function.
  * Focus on tasks that do not require writing much code
  Please generate 3 objects,

  Make sure that the JSON object is valid and can be parsed without errors and contains only the field "task".
  """

# Ask the model to generate the evaluation dataset
add_user_message(messages, eval_dataset_prompt)
add_assistant_message(messages, "```json")
eval_dataset = chat(messages, stop_sequence="```")
# Save the evaluation dataset to a JSON file
eval_dataset = json.loads(eval_dataset)
with open("eval_dataset.json", "w") as f:
  json.dump(eval_dataset, f, indent=2)

# Run the evaluation on the generated dataset
results = run_evaluation(eval_dataset)

print("Evaluation Results:")
print(json.dumps(results, indent=2))
