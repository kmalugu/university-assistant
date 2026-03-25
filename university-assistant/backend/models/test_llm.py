from llm import chain

if __name__ == "__main__":
    response = chain.invoke({
        "input": "What courses are available for AI?"
    })
    print("\nResponse:\n", response)