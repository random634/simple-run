import os
import asyncio


async def run(cmd):
    log_path = os.path.join(os.path.dirname(__file__), "jobs", "1.log")
    log_file = open(log_path, "w+")

    log_file.write("exec cmd: \n")
    log_file.write(cmd)
    log_file.flush()

    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    # Read output.
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        print(line)
        print(line.decode("utf-8").strip())
        log_file.write(line.decode("utf-8"))
        log_file.flush()

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        print(f"[stdout]\n{stdout.decode('utf-8')}")
    if stderr:
        print(f"[stderr]\n{stderr.decode('utf-8')}")
        log_file.write(stderr.decode("utf-8"))
    log_file.close()


if __name__ == "__main__":
    print(str(True))
    cmd = """ls /eee
"""
    asyncio.run(run(cmd))
