from coder_evals import (
    get_benchmark_ids,
    start_benchmark,
    submit_artifact,
    maybe_register_user,
    BenchmarkContext,
)
from aider.io import InputOutput
from aider.coders import Coder
from aider.models import Model
from aider.dump import dump
import openai
import os
import shutil
from dotenv import load_dotenv
import docker
from docker.models.containers import Container
import uuid
from typing import Tuple
from textwrap import dedent


def docker_eval(dockerfile_subdir: str) -> Tuple[bool, str]:
    client = docker.from_env()
    image_tag = str(uuid.uuid4())
    parent_dir = os.path.dirname(dockerfile_subdir)
    dockerfile_name = os.path.join(os.path.basename(dockerfile_subdir), "Dockerfile")

    try:
        image, build_logs = client.images.build(
            path=parent_dir, tag=image_tag, dockerfile=dockerfile_name
        )
        logs = "".join([str(log) for log in build_logs])

    except docker.errors.BuildError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

    try:
        stdout_bytes = client.containers.run(image=image_tag, remove=True, stdout=True)
        stdout = stdout_bytes.decode("utf-8")
        return True, stdout
    except docker.errors.ContainerError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def _local_eval(path: str) -> bool:
    success, logs = docker_eval(path)
    return success, logs


def benchmark():
    benchmark_ids = get_benchmark_ids(
        after="2023-09-04T17:21:19.73387Z", title_search="v2"
    )
    # default the code path to the current directory / .workspace if not set using path.
    code_path = os.environ.get("CODE_PATH", os.path.join(os.getcwd(), ".workspace"))
    # if the code path exists we shutil remove it and recreate it.
    if os.path.exists(code_path):
        shutil.rmtree(code_path, ignore_errors=True)
    os.makedirs(code_path)
    for benchmark_id in benchmark_ids:
        # this will create a ticket for the benchmark, assign it to your agent
        # clone the code into your workspace, and then wait for you to submit a completed artifact.
        ctx = start_benchmark(benchmark_id, code_path)
        _run_aider(ctx)

        for i in range(5):
            # run local eval
            dpath = os.path.join(ctx.cloned_path, ".benchmark")
            print(f"Running local eval for {dpath}")
            success, logs = _local_eval(dpath)
            print(f"Local eval success: {success}")
            if not success:
                msg = dedent(
                    f"""
                    Local eval failed with the following error:
                    {logs}
                    """
                )
                print(f"Attempt {i} with feedback. Running aider with message: {msg}")
                _run_aider(ctx, message=msg)
            else:
                break

        status, logs = submit_artifact(ctx)
        print(f"\n\nBenchmark with ID {benchmark_id} completed with status {status}")
        print(f"Logs for benchmark {benchmark_id}:\n{logs}\n\n")


def _run_aider(ctx: BenchmarkContext, message: str = None):
    code_path = ctx.cloned_path
    task_text = ctx.ticket["description"]
    # aider works best in the directory where the code is cloned.
    aider_path = os.getcwd()
    os.chdir(code_path)
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
    openai.api_key = os.environ["OPENAI_API_KEY"]
    coder = Coder.create(
        main_model,
        edit_format,
        io,
        fnames=fnames,
        use_git=False,
        stream=True,
        pretty=True,
        verbose=False,
    )
    if message:
        coder.run(with_message=message)
    else:
        coder.run(with_message=task_text)
    os.chdir(aider_path)


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
