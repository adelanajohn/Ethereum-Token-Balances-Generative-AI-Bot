import boto3
import json

bedrock=boto3.client(service_name="bedrock-runtime")
client = boto3.client('managedblockchain-query')

# Define a Python function that calls the LLM
def get_response(prompt_data, system_prompt):   
    payload={
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "temperature": 0.8,
        "messages": [
            {
                "role": "user",
                "content": [{ "type": "text", "text": prompt_data}]
            }
        ],
        "system": system_prompt
    }
    
    body=json.dumps(payload)
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
    response=bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    response_body=json.loads(response.get("body").read())
    response_text=response_body.get("content")[0].get("text")
    return response_text

# Define a function that calls the AMB Query ListTokenBalances API to list all token balances owned by an address (either a contract address or a wallet address)
def list_token_balances(contract_address):
    response = client.list_token_balances(
        tokenFilter={
            'contractAddress': contract_address,
            'network': 'ETHEREUM_MAINNET'
        }
    )
    token_balances_dict = {} # Token balances dictionary
    if response['tokenBalances']:
        token_balances_list = response['tokenBalances']
        for balance_dict in token_balances_list:
            token_balances_dict.update({balance_dict['ownerIdentifier']['address']: balance_dict['balance']})            
    return token_balances_dict

# Contract address
c_address = "0x..." # Replace with an actual contract address

# Prompt statement
prompt_data = f'''
    Please list token balances in contract {c_address}
'''

# Create a description of the list_token_balances action so that LLM knows how to use it. This includes the tool name, description, and parameters
tool_description = """
    <tool_description>
        <tool_name>list_token_balances</tool_name>
        <description>
            Function for listing token balances in ethereum contracts
        <parameters>
            <parameter>
                <name>contract_address</name>
                <type>str</type>
                <description>Ethereum contract address</description>
            </parameter>
        </parameters>
    </tool_description>    
"""

# Create a system prompt that instructs the LLM on how to invoke the list_token_balances function based on the user's query.
system_prompt = f"""
In this environment you have access to a set of tools you can use to answer the user's question.

You may call them like this:
<function_calls>
    <invoke>
        <tool_name>$TOOL_NAME</tool_name>
        <parameters>
            <$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>
            ...
        </parameters>
    </invoke>
</function_calls>

Here are the tools available:
<tools>{tool_description}</tools>
"""

# Invoke the list_token_balances function
token_balances = list_token_balances(c_address)

function_results = f"""
<function_results>
  <result>
    <tool_name>list_token_balances</tool_name>
    <stdout>{token_balances}</stdout>
  </result>
</function_results>
"""

# Invoke the LLM with the prompt statement and system prompt
function_calling_message = get_response(prompt_data, system_prompt)

# Append the result of the list_token_balances function call to the LLM call
partial_assistant_message = function_calling_message + function_results

# Update the system prompt with the partial assistant message
updated_system_prompt = f"""{system_prompt}
Here is the result of the function call:
{partial_assistant_message}
Based on this result, please provide a response to the original question.
"""

# Print the LLM response
print(get_response(prompt_data, updated_system_prompt))