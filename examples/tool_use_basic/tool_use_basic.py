from pyexpat.errors import messages
from dotenv import load_dotenv
import os
import requests
from copy import deepcopy
import json
from typing import Literal

load_dotenv()

provider = "WILDCARD"
MODEL = "gpt-5-mini"
BASE_URL = os.environ[f"{provider}_BASE_URL"]
API_KEY = os.environ[f"{provider}_API_KEY"]

# 用户输入
def render_yellow(text: str) -> str:
    """Render text in yellow color for terminal output."""
    return f"\033[33m{text}\033[0m"

# 当前 conversation_messages 里的新增内容
def render_red(text: str) -> str:
    return f"\033[31m{text}\033[0m"

# 中间过程
def render_green(text: str) -> str:
    return f"\033[32m{text}\033[0m"

def print_message(message: dict, color: Literal["red", "green"]) -> None:
    need_keys = ["content", "tool_calls", "tool_call_id"]
    role = message["role"]
    output_data = {key: message[key] for key in need_keys if key in message}
    output_data = f"[{role}] {json.dumps(output_data, ensure_ascii=False)}"
    if color == "red":
        print(render_red(output_data))
    elif color == "green":
        print(render_green(output_data))

def call_llm(payload: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    response = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def get_weather(location: str) -> str:
    return f"{location} 的天气是晴, 35摄氏度"

def main():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a given location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g., San Francisco, CA",
                        },
                    },
                    "required": ["location"],
                },
            }
        }
    ]
    common_payload = {
        "model": MODEL,
        # "messages": [],
        "tools": tools,
        "tool_choice": "auto",  # 模型自动判断是否需要进行工具调用
    }

    conversation_messages = []
    conversation_messages.append(
        {"role": "system", "content": "You are a helpful assistant."},
    )
    # SystemMessage
    print_message(conversation_messages[-1], "red")

    while True:
        user_input = input(render_yellow("请输入问题: "))
        if user_input.lower() == "exit":
            break
        conversation_messages.append({"role": "user", "content": user_input})
        # HumanMessage
        print_message(conversation_messages[-1], "red")

        max_iterations = 5
        current_iteration = 0

        messages = deepcopy(conversation_messages)
        while current_iteration < max_iterations:   
            response = call_llm({**common_payload, "messages": messages})
            choice_tool_call = response["choices"][0]["finish_reason"] == "tool_calls"
            llm_output_message = response["choices"][0]['message']
            if choice_tool_call:
                # llm_output_message:
                # {
                #     'annotations': [],
                #     'content': None,
                #     'refusal': None,
                #     'role': 'assistant',
                #     'tool_calls': [
                #         {
                #             'function': {
                #                 'arguments': '{"location":"Shenzhen, China"}',
                #                 'name': 'get_weather'
                #             },
                #             'id': 'call_3zTZjpp77BqkfbCgs4Oz0WgG',
                #             'type': 'function'
                #         }
                #     ]
                # }

                # AIMessage with tool_calls
                messages.append(llm_output_message)
                print_message(messages[-1], "green")

                for tool_call in llm_output_message["tool_calls"]:
                    tool_name = tool_call['function']["name"]
                    tool_args = json.loads(tool_call['function']["arguments"])

                    if tool_name == "get_weather":
                        tool_response = get_weather(**tool_args)
                        # ToolMessage: 工具执行结果
                        messages.append(
                            {
                                "role": "tool",
                                "content": str(tool_response),
                                "tool_call_id": tool_call["id"]
                            }
                        )
                        print_message(messages[-1], "green")
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
            else:
                # AIMessage
                conversation_messages.append(response['choices'][0]['message'])
                print_message(conversation_messages[-1], "red")
                break
            
            current_iteration += 1
            if current_iteration == max_iterations and choice_tool_call:
                conversation_messages.append("已多次使用工具调用但未得到最终回答，请您换个问法")
                print_message(conversation_messages[-1], "red")

if __name__ == "__main__":
    main()
    # 深圳今天的天气怎样