from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema, OutputFixingParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
import os

import sys
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    PromptTemplate
)
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)

def main(build_output_file):
    with open(build_output_file, "r") as f:
        build_output = f.read()

    # Process the build_output as needed
    print(build_output)

    text = build_output

    human_message_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template="Can you find the filename where this error comes from: {error}?  If you do, please reply with the filename only, if not please reply with no.",
            input_variables=["error"],
        )
    )

    chat_prompt_template = ChatPromptTemplate.from_messages([human_message_prompt])
    chat = ChatOpenAI(temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"])
    chain = LLMChain(llm=chat, prompt=chat_prompt_template)
    filename = chain.run(build_output);

    if filename == "no":
        print("No filename found")
        return
    
    print("Filename found: " + filename)

    # Read file
    with open(filename, "r") as f:
        file_text = f.read()

    # Process the file_text as needed
    # print(file_text)

    response_schemas = [
        ResponseSchema(name="fix_found", description="boolean true false value if the fix was found or not."),
        ResponseSchema(name="fixed_content", description="the updated contents containing the fix.")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    human_message_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template="\nPlease respond with the fixed code ONLY. \n{format_instructions}.\n Content: {file}\n Error: {error}.",
            input_variables=["file", "error"],
            partial_variables={"format_instructions": format_instructions}
        )
    )

    chat_prompt_template = ChatPromptTemplate.from_messages([human_message_prompt])
    # print(chat_prompt_template)
    chat = ChatOpenAI(temperature=0)
    chain = LLMChain(llm=chat, prompt=chat_prompt_template)
    fixed_code = chain.run({'file':file_text, 'error': build_output});
    print(fixed_code)

    try:
        parsed = output_parser.parse(fixed_code)
        print(parsed)
    except:
        new_parser = OutputFixingParser.from_llm(parser = output_parser, llm = chat);
        parsed = new_parser.parse(fixed_code)
        print(parsed)
        return
    # if fixed_code == "no":
    #     print("No fix found")
    #     return

    if parsed["fix_found"] == "false":
        print("No fix found")
        return
    
    print("Fix found: " + parsed["fixed_content"])
    # Write file
    with open(filename, "w") as f:
        f.write(parsed["fixed_content"])
    
    # Process the fixed_code as needed
    # detect ``` as end and start and get whats between
    # print("Fix found: " + fixed_code)

    # Write file
    # with open(filename, "w") as f:
    #     f.write(fixed_code)


if __name__ == "__main__":
    build_output_file = sys.argv[1]
    main(build_output_file)
