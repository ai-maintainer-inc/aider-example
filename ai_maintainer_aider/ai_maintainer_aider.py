"""Main module."""
# import the agent harness so we can get benchmarks and execute them.
from agent_harness.agent_harness import (
    register_user,
    register_agent,
    get_benchmark_ids,
    start_benchmark,
    ask_question,
    submit_artifact,
    PythonClientUser,
    fetch_users_agents,
)

# import the aider code so we can have the agent make changes to the code
from aider.io import InputOutput
from aider.coders import Coder
from aider.models import Model
from aider.dump import dump
import openai

# import ability to get env variables
import os
import glob


def get_or_make_user(username, password, email, host):
    """Get or make a user."""
    client = register_user(username, password, email, host)
    if not client:
        client = PythonClientUser(username, password, host)
    return client


def benchmark(client):
    agents = fetch_users_agents(client)["agents"]
    print("agents:", agents)
    agent_id = None
    for agent in agents:
        if agent["agentName"] == "ai-maintainer-aider-agent":
            agent_id = agent["agentId"]
            break

    if not agent_id:
        agent_id = register_agent(client, "ai-maintainer-aider-agent")

    benchmark_ids = get_benchmark_ids(client)
    code_path = os.environ.get("CODE_PATH")
    if not code_path:
        # code_path = "/tmp/code"
        raise Exception("CODE_PATH environment variable not set!")
    for benchmark_id in benchmark_ids:
        # this will create a ticket for the benchmark, assign it to your agent
        # clone the code into your workspace, and then wait for you to submit a completed artifact.
        fork, bid_id, ticket = start_benchmark(
            client, benchmark_id, code_path, agent_id
        )

        # get agent questions then submit them with
        # ask_question(client, ticket_id, question)
        # ask question functionality currently always returns "No"
        # we will be supporting this functionality in our next release.
        # aider doesn't support that functionality yet so it isn't implemented here.

        # get the task text and run the agent
        task_text = ticket["description"]
        aider_path = os.environ.get("AIDER_PATH")
        _run_aider(code_path, aider_path, task_text)

        submit_artifact(client, fork, bid_id, code_path)
        # Our evaluation harness will automatically evaluate your code and give you a score, which you will be able to find in our UI
        # at AI-Maintainer.com :)


def _run_aider(code_path, aider_path, task_text):
    io = InputOutput(
        pretty=True,
        yes=True,
        chat_history_file="chat_history.txt",
    )

    main_model = Model("gpt-4")
    edit_format = main_model.edit_format

    dump(main_model)
    dump(edit_format)
    fnames = _get_files_with_exts(code_path, aider_path, ["py", "md"])
    show_fnames = ",".join(map(str, fnames))
    print("fnames:", show_fnames)

    openai.api_key = os.environ["OPENAI_API_KEY"]

    coder = Coder.create(
        main_model,
        edit_format,
        io,
        fnames=fnames,
        use_git=False,
        stream=False,
        pretty=False,
        verbose=True,
    )
    coder.run(with_message=task_text)


def _get_files_with_exts(
    code_path,
    aider_path,
    exts,
):
    # Get all Python files in the code_path directory
    all_files = []
    for ext in exts:
        all_files.extend(
            glob.glob(
                f"{code_path}/**/*.{ext}",
                recursive=True,
            )
        )
    # Make the file paths relative to the code_path
    all_files = [os.path.relpath(file, aider_path) for file in all_files]
    print(all_files)
    return all_files


def main():
    """Main function."""
    username = "aider_user5"
    password = "aider_user5"
    email = "aider_email@email.com"
    host = "http://marketplace-api:8080/api/v1"
    client = get_or_make_user(username, password, email, host)
    benchmark(client)


if __name__ == "__main__":
    main()
