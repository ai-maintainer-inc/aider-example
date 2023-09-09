from agent_harness.agent_harness import (
    maybe_create_agent,
    get_benchmarks,
    start_benchmark,
    submit_artifact,
    maybe_register_user,
    get_artifact_status,
)
from aider.io import InputOutput
from aider.coders import Coder
from aider.models import Model
from aider.dump import dump
import openai
import os
import shutil
from dotenv import load_dotenv


def benchmark():
    agent_id = maybe_create_agent("ai-maintainer-aider-agent")

    benchmark_ids = get_benchmarks(
        after="2023-09-04T17:21:19.73387Z",  # title_search="endpoint"
    )
    # default the code path to the current directory / .workspace if not set using path.
    code_path = os.environ.get("CODE_PATH", os.path.join(os.getcwd(), ".workspace"))
    aider_path = os.getcwd()
    # if the code path exists we shutil remove it and recreate it.
    if os.path.exists(code_path):
        shutil.rmtree(code_path, ignore_errors=True)
    os.makedirs(code_path)
    for benchmark_id in benchmark_ids:
        # this will create a ticket for the benchmark, assign it to your agent
        # clone the code into your workspace, and then wait for you to submit a completed artifact.
        fork, bid_id, ticket, cloned_path = start_benchmark(benchmark_id, code_path, agent_id)
        # aider works best in the directory where the code is cloned.
        os.chdir(cloned_path)
        _run_aider(cloned_path, ticket["description"])
        os.chdir(aider_path)

        response = submit_artifact(
            fork, ticket["code"]["repo"], bid_id, cloned_path
        )
        print("response:", response.body)
        benchmark_artifact_id = response.body["artifactId"]
        status, logs = get_artifact_status(benchmark_artifact_id)
        print(f"\n\nBenchmark with ID {benchmark_id} completed with status {status}")
        print(f"Logs for benchmark {benchmark_id}:\n{logs}\n\n")


def _run_aider(code_path, task_text):
    io = InputOutput(
        pretty=True,
        yes=True,
        chat_history_file="../chat_history.txt",
    )
    main_model = Model("gpt-4")
    edit_format = main_model.edit_format
    dump(main_model)
    dump(edit_format)
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
    exclude_dirs = [".benchmark", ".git"]
    for root, dirs, files in os.walk(code_path):
        if any(ex_dir in root for ex_dir in exclude_dirs):
            continue
        for file in files:
            all_files.append(os.path.join(root, file))
    # Aider requires relative file paths. 
    all_files = [os.path.relpath(file, code_path) for file in all_files]
    return all_files


def main():
    load_dotenv()
    maybe_register_user()
    benchmark()


if __name__ == "__main__":
    main()