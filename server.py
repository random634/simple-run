import os
import time
import asyncio
from json import loads, dumps
from sanic import Sanic
from sanic.response import json

# 1. 执行命令
# 2. 命令输出到文件
# 3. 读取输出

app = Sanic("SimpleRun")

app.static("/statics", "statics/", name="statics")

job_root_dir = os.path.join(os.path.dirname(__file__), "jobs")


@app.get("/")
@app.ext.template("job-list.html")
async def main_page(request):
    return {"content": "Job list page"}


@app.get("/job-edit/<name:str>")
@app.ext.template("job-edit.html")
async def job_edit_page(request, name):
    return {"content": "Job edit page", "jobName": name}


@app.get("/job-run/<name:str>")
@app.ext.template("job-run.html")
async def job_run_page(request, name):
    return {"content": "Job run page", "jobName": name}


@app.get("/job-log/<nameAndLogIdx:str>")
@app.ext.template("job-log.html")
async def job_log_page(request, nameAndLogIdx):
    [name, idx] = nameAndLogIdx.split(":")
    return {"content": "Job log page", "jobName": name, "logIdx": idx}


@app.get("/help")
@app.ext.template("help.html")
async def help_page(request):
    return {"content": "Help page"}


@app.post("/data/job_list")
async def data_job_list(request):
    job_list = []
    for root, dirs, files in os.walk(job_root_dir):
        for file in files:
            # if os.path.splitext(file)[-1] == ".json":
            if file == "config.json":
                job_config_file = open(os.path.join(root, file), "r")
                job_config = job_config_file.read()
                job_info = loads(job_config)
                job_config_file.close()
                job_list.append(
                    {"name": job_info.get("name"), "desc": job_info.get("desc")}
                )

    job_list.sort(key=lambda x: x.get("name"))

    return json({"code": 0, "result": job_list})


@app.post("/data/job_info")
async def data_job_info(request):
    job_name = request.json.get("name")

    if job_name == "new":
        return json(
            {
                "code": 0,
                "result": {
                    "name": job_name,
                    "desc": "",
                    "params": [],
                    "content": "",
                },
            }
        )
    else:
        job_config_path = os.path.join(job_root_dir, job_name, "config.json")
        if not os.path.exists(job_config_path):
            return json({"code": 1, "message": "job not exist: " + job_name})
        else:
            job_config_file = open(job_config_path, "r")
            job_config = job_config_file.read()
            job_info = loads(job_config)
            job_config_file.close()
            return json({"code": 0, "result": job_info})


@app.post("/data/job_log_list")
async def data_job_log_list(request):
    job_name = request.json.get("name")
    job_dir = os.path.join(job_root_dir, job_name)
    if not os.path.exists(job_dir):
        return json({"code": 1, "message": "job not exist: " + job_name})

    job_idx = 0
    job_next_exec_idx_path = os.path.join(job_dir, "next_exec_idx")
    if os.path.exists(job_next_exec_idx_path):
        job_next_exec_idx_file = open(job_next_exec_idx_path, "r")
        job_next_exec_idx_info = job_next_exec_idx_file.read()
        job_idx = int(job_next_exec_idx_info)
        job_next_exec_idx_file.close()

    if job_idx <= 0:
        return json(
            {
                "code": 0,
                "result": {
                    "name": job_name,
                    "logs": [],
                },
            }
        )
    else:
        logs = []
        for i in range(job_idx - 1, 0, -1):
            log_path = os.path.join(job_dir, f"exec{i}.log")
            if os.path.exists(log_path):
                logs.append({"log_idx": i})
        return json(
            {
                "code": 0,
                "result": {
                    "name": job_name,
                    "logs": logs,
                },
            }
        )


@app.post("/data/job_log_detail")
async def data_job_log_detail(request):
    job_name = request.json.get("name")
    job_log_idx = request.json.get("log_idx")
    job_dir = os.path.join(job_root_dir, job_name)
    if not os.path.exists(job_dir):
        return json({"code": 1, "message": "job not exist: " + job_name})

    log_path = os.path.join(job_dir, f"exec{job_log_idx}.log")
    if not os.path.exists(log_path):
        return json({"code": 1, "message": "job log not exist: " + job_log_idx})

    log_file = open(log_path, "r")
    log_content = log_file.read()
    log_file.close()

    return json(
        {
            "code": 0,
            "result": {
                "log_idx": job_log_idx,
                "log_content": log_content,
            },
        }
    )


@app.post("/update/job_info")
async def update_job_info(request):
    job_name = request.json.get("name")
    if job_name == "new":
        return json({"code": 1, "message": "job name new is reserved"})
    else:
        job_dir = os.path.join(job_root_dir, job_name)
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)
        job_config_file = open(os.path.join(job_dir, "config.json"), "w+")
        job_config_file.write(dumps(request.json, separators=(",", ":")))
        job_config_file.close()
        return json({"code": 0, "result": request.json})


@app.post("/run/job")
async def run_job(request):
    job_name = request.json.get("name")
    job_params = request.json.get("params")
    job_dir = os.path.join(job_root_dir, job_name)
    if not os.path.exists(job_dir):
        return json({"code": 1, "message": "job not exist: " + job_name})

    job_config_path = os.path.join(job_dir, "config.json")
    if not os.path.exists(job_config_path):
        return json({"code": 1, "message": "job not exist: " + job_name})

    job_config_file = open(job_config_path, "r")
    job_config = job_config_file.read()
    job_info = loads(job_config)
    job_config_file.close()

    shell_src = job_info.get("content")
    for param in job_params:
        if param.get("name") is None:
            continue
        if param.get("name") == "":
            continue
        if param.get("val") is None:
            continue
        shell_src = str.replace(
            shell_src, "$" + param.get("name"), str(param.get("val"))
        )

    shell_exec_idx = 1
    job_next_exec_idx_path = os.path.join(job_dir, "next_exec_idx")
    if os.path.exists(job_next_exec_idx_path):
        job_next_exec_idx_file = open(job_next_exec_idx_path, "r")
        job_next_exec_idx_info = job_next_exec_idx_file.read()
        shell_exec_idx = int(job_next_exec_idx_info)
        job_next_exec_idx_file.close()

    job_next_exec_idx = shell_exec_idx + 1
    job_next_exec_idx_file = open(job_next_exec_idx_path, "w+")
    job_next_exec_idx_file.write(str(job_next_exec_idx))
    job_next_exec_idx_file.close()

    job_log_file = open(os.path.join(job_dir, f"exec{shell_exec_idx}.log"), "w+")

    job_log_file.write("-----------------------------------\n")
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    job_log_file.write(f"exec time: {current_time}\n")
    job_log_file.write("------------ run shell ------------\n")
    job_log_file.write(shell_src + "\n")
    job_log_file.write("-----------------------------------\n")
    job_log_file.flush()
    proc = await asyncio.create_subprocess_shell(
        shell_src, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    # Read output.
    job_log_file.write(f"stdout:\n")
    job_log_file.flush()
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        job_log_file.write(line.decode("utf-8"))
        job_log_file.flush()

    stdout, stderr = await proc.communicate()

    if stdout:
        job_log_file.write(stdout.decode("utf-8"))
        job_log_file.flush()
    if stderr:
        job_log_file.write(f"stderr:\n")
        job_log_file.write(stderr.decode("utf-8"))
        job_log_file.flush()

    job_log_file.write(f"result code: {proc.returncode}\n")
    job_log_file.flush()
    job_log_file.close()

    if proc.returncode != 0:
        return json({"code": proc.returncode, "result": stderr.decode("utf-8")})
    else:
        return json({"code": 0, "result": "success"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
