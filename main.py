from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel
from anthropic.types import Message
from anthropic.types import ToolUseBlock
from anthropic.types import TextBlock


load_dotenv()


client=Anthropic()
model='claude-sonnet-4-5'


def add_user_message(conversation,user_message):
    user_message={"role":"user","content":user_message if isinstance(user_message,Message) else user_message}
    conversation.append(user_message)
    

def add_assistant_message(conversation,assistant_message):
    assistant_message={"role":"user","content":assistant_message if isinstance(assistant_message,Message) else assistant_message}
    conversation.append(assistant_message)

def call_llm(
        messages,
        max_tokens=1200,
        tools=None,
        streaming=False,
        system=None,
        model=model,):
    params={"messages":messages,
        "model":model,
        "max_tokens":max_tokens,
        "model":model,
        "tool_choice":{"type": "any"}
    }
    if tools:
        params["tools"]=tools
    if streaming:
        params["streaming"]=True,
    if system:
        params["system"]=system
    response=client.messages.create(**params)
    return response

    

    #Tool for the websearch
websearch_tool={
    "type":"web_search_20260209",
    "name":"web_search",
    "max_uses":3,
}

#Tool to read file
def read_file(file_name):
    try:
        with open(file_name,'+r') as f:
            file_content=f.read()
        return "read_file_status: FILE READ SUCCESSFUL here are the file read contents : {file_content}"
    except FileNotFoundError as e:
        return f"read_file_status: FILE READ FAILED {str(e)} "
    
    
read_file_schema={
        "name": "read_file",
        "description": "Reads the full text content of a local file from disk and returns it as a string. Use this when you need to access information stored in a local .txt or .md file. Only use this for files you know exist on disk. Returns the raw string content of the file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The name or relative path of the file to read. For example: 'notes.txt' or 'data/report.md'"
                }
            },
            "required": ["file_name"]
        }
    }

#Tool for writing in the file
def write_file(file_name,content):
    try:
        with open(file_name,'w') as f:
            f.write(content)
        return "write_file_status: WRITE READ WAS SUCCESSFUL"
    except FileNotFoundError as e:
        return f"write_file_status: WRITE READ FAILED {str(e)} "
    

write_file_schema={
        "name": "write_file",
        "description": "Writes the given text content to a local file on disk. Use this to save reports, summaries, or any text output. If the file already exists, it will be completely overwritten. Use this as the final step when you are ready to produce the output report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The name or relative path of the file to write to. For example: 'report.md' or 'output/summary.txt'"
                },
                "content": {
                    "type": "string",
                    "description": "The full text content to write into the file."
                }
            },
            "required": ["file_name", "content"]
        }
    }


tool_lookup={
    "read_file":read_file,
    "write_file":write_file
}


def tool_executor(tool_block):
    tool=tool_lookup(tool_block.name)
    tool_response=tool(**tool_block.input)
    return tool_response

agent_loop_messages=[]
user_message=input()
print(user_message)
add_user_message(agent_loop_messages,user_message)
while True:
    response=call_llm(agent_loop_messages,tools=[read_file_schema,write_file_schema,websearch_tool])
    print(response)
    if(response.stop_reason=='end_turn'):
        for block in response.content:
            if isinstance(block,TextBlock):
                print(block.text)
        break
    if(response.stop_reason=='tool_use'):
        for block in response.content:
            if isinstance(block,TextBlock):
                print(block.text)
            if isinstance(block,ToolUseBlock):
                tool_executor_response=tool_executor(block)
                print(block)
                add_user_message(agent_loop_messages,tool_executor)
print("okay bye bye the task has been completed")   

       
