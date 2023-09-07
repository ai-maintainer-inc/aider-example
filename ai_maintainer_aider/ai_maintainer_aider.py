"""Main module."""
# import the agent harness so we can get benchmarks and execute them.
from agent_harness.agent_harness import (
    register_user,
    register_agent,
    get_benchmarks,
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
import time


def get_or_make_user(username, password, email, host, git_host):
    """Get or make a user."""
    client = register_user(username, password, email, host, git_host)
    if not client:
        client = PythonClientUser(username, password, host, git_host)
    return client


def benchmark(client):
    agents = fetch_users_agents(client)
    print("agents:", agents)
    agent_id = None
    for agent in agents:
        if agent["agentName"] == "ai-maintainer-aider-agent":
            agent_id = agent["agentId"]
            break

    if not agent_id:
        agent_id = register_agent(client, "ai-maintainer-aider-agent")

    benchmark_ids = get_benchmarks(
        client,
        after="2023-09-04T17:21:19.73387Z",  # title_search="endpoint"
    )
    code_path = os.environ.get("CODE_PATH")
    if not code_path:
        # code_path = "/tmp/code"
        raise Exception("CODE_PATH environment variable not set!")
    for benchmark_id in benchmark_ids:
        # this will create a ticket for the benchmark, assign it to your agent
        # clone the code into your workspace, and then wait for you to submit a completed artifact.
        # remove all folders and files in the code_path:
        # for f in glob.glob(f"{code_path}/*"):
        #     if os.path.isdir(f):
        #         os.rmdir(f)
        #     else:
        #         os.remove(f)
        fork, bid_id, ticket, cloned_path = start_benchmark(
            client, benchmark_id, code_path, agent_id
        )
        print("cloned_path: ", cloned_path)

        # get agent questions then submit them with
        # ask_question(client, ticket_id, question)
        # ask question functionality currently always returns "No"
        # we will be supporting this functionality in our next release.
        # aider doesn't support that functionality yet so it isn't implemented here.

        # get the task text and run the agent
        task_text = ticket["description"]
        aider_path = os.environ.get("AIDER_PATH", None)
        if not aider_path:
            raise Exception("AIDER_PATH environment variable not set!")
        print("AiderPath: ", aider_path)
        # change the working directory so relative file paths are right to cloned_path
        os.chdir(cloned_path)
        _run_aider(".", aider_path, task_text)
        os.chdir(aider_path)

        response = submit_artifact(
            client, fork, ticket["code"]["repo"], bid_id, cloned_path
        )
        benchmark_artifact_id = response.body["artifactId"]
        # print(f"response: {response.body}")
        check_artifact_status(client, benchmark_artifact_id)


def check_artifact_status(client, benchmark_artifact_id):
    # get operator agents
    response = client.instance.get_agents()
    agents = list(response.body["agents"])
    agent_id = agents[0]["agentId"]

    # poll for benchmark artifact status
    query_params = {
        "agentId": agent_id,
        "artifactId": benchmark_artifact_id,
    }

    status = None
    for i in range(12):
        response = client.instance.get_agent_artifacts(query_params=query_params)
        artifacts = list(response.body["artifacts"])
        if len(artifacts) == 0:
            raise ValueError("No artifacts were created.")
        elif artifacts[0]["status"] == "pending":
            print("Waiting for evaluator. Sleeping for 5 seconds")
            time.sleep(5)
            continue

        status = artifacts[0]["status"]
        break

    if not status:
        raise ValueError("Failed to get benchmark artifact status")

    print(
        f"\n\nARTIFACT_ID: {benchmark_artifact_id} finished with status: {status}\n\n"
    )


def _run_aider(code_path, aider_path, task_text):
    io = InputOutput(
        pretty=True,
        yes=True,
        chat_history_file="../chat_history.txt",
    )

    main_model = Model("gpt-4")
    edit_format = main_model.edit_format

    dump(main_model)
    dump(edit_format)
    # get all files recursively in code_path by absolute path:
    fnames = _get_files(code_path)
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
        verbose=False,
    )
    coder.run(with_message=task_text)


def _get_files(code_path):
    all_files = []

    # List of directories to skip
    exclude_dirs = [".benchmark", ".git"]

    # Walk through the code_path and get all files, excluding ones in specified directories
    for root, dirs, files in os.walk(code_path):
        if any(ex_dir in root for ex_dir in exclude_dirs):
            continue
        for file in files:
            all_files.append(os.path.join(root, file))

    # Make the file paths relative to the aider_path
    all_files = [os.path.relpath(file, code_path) for file in all_files]

    return all_files


def main():
    """Main function."""
    username = "dschonholtz"
    password = "default_secure!"
    email = "douglas@ai-maintainer.com"
    host = "https://platform.ai-maintainer.com/api/v1"
    git_host = "https://git.ai-maintainer.com"
    client = get_or_make_user(username, password, email, host, git_host)
    benchmark(client)


if __name__ == "__main__":
    main()
