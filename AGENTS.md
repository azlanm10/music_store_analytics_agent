You are helping me write a concise PROJECT_CONTEXT.md file for my AI agent project.

I will provide you with three things:  
1. The **purpose of the agent** (what problem it solves and for whom).  
2. A **short summary** of my design choices and how the system meets user needs.  
3. The **architecture diagram** of it (systems, subsystems, components).  

Using this information, generate a **clear and structured Markdown file** that gives overall context about the project.

The file should include:  
- **Project Overview** – what this agent does and why it exists.  
- **System Scope** – what’s in scope and what’s not.  
- **Architecture Summary** – a short description of the system’s main subsystems and how they interact.  
- **Key Inputs and Outputs** – what goes in, what comes out.  
- **Design Rationale** – how the design supports user needs or constraints.  

Do **not** include implementation details, code, or specific instructions about how to build it — the goal is only to capture *context* for development.

Format the output as a Markdown document suitable for saving in @PROJECT_CONTEXT.md 

Purpose: The Agent is a conversational agent that allows users to query the Chinook music store database using natural language in Slack. It is designed to provide responses in a conversational format, allowing users to interact with the data as if they were having a discussion with an assistant.

Short Summary: The agent has 3 subsystems: invoke, engine and output. 
The invoke will handle the requests coming in from the users through Slack; the validator checks if the request is supported and of the same domain as the music store database, and Guardrails will help make sure the requests are safe from unauthorised actions and requests that are not part of the scope or injecting any prompts for that matter. 
The engine, in a nutshell, will process the user's request. The planner will show how the users' query should be executed. Orchestrator is more about the workflow, and Pandas AI Reasoner will generate SQL queries with the help of semantic layers to be executed in the Chinook database. 
The output is the final part of the design wherein the results from the engine are formatted and sent back to Slack in a conversational manner, making it easier for the user to get a grasp on the data