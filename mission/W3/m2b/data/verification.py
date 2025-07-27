import subprocess
import os

CONFIGURATIONS = {
    "core-site": {
        "fs.defaultFS": "hdfs://namenode:9000",
        "hadoop.tmp.dir": "/tmp/hadoop",
        "io.file.buffer.size": "131072",
    },
    "hdfs-site": {
        "dfs.replication": "2",
        "dfs.blocksize": "134217728",
        "dfs.namenode.name.dir": "/hadoop/dfs/name",
    },
    "mapred-site": {
        "mapreduce.framework.name": "yarn",
        "mapreduce.jobhistory.address": "namenode:10020",
        "mapreduce.task.io.sort.mb": "256",
    },
    "yarn-site": {
        "yarn.resourcemanager.address": "namenode:8032",
        "yarn.nodemanager.resource.memory-mb": "8192",
        "yarn.scheduler.minimum-allocation-mb": "1024",
    }
}

COMMAND_PREFIX = ["hdfs", "getconf", "-confKey"]
DIR_NAME = "/tmp/"
TEST_LOCAL_FILE = DIR_NAME + "hadoop_config_check_testfile.txt"
HDFS_TEST_PATH = DIR_NAME + "hadoop_config_check_testfile.txt"


def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        return None


def get_config_value(command):
    return run_cmd(command)


def check_configurations():
    replication_check_value = None

    for site, configs in CONFIGURATIONS.items():
        for key, expected_value in configs.items():
            cmd = COMMAND_PREFIX + [key]
            actual_value = get_config_value(cmd)

            if actual_value is None:
                print(f"FAIL: {cmd} -> (unable to fetch value)")
            elif actual_value == expected_value:
                print(f"PASS: {cmd} -> {actual_value}")
            else:
                print(f"FAIL: {cmd} -> {actual_value} (expected {expected_value})")

            if key == "dfs.replication":
                replication_check_value = actual_value


EXPECTED_REPLICATION = run_cmd(COMMAND_PREFIX + ["dfs.replication"])


def create_local_test_file():
    try:
        with open(TEST_LOCAL_FILE, "w") as f:
            f.write("test")
        return True
    except Exception as e:
        return False

HDFS_COMMAND_PREFIX = ["hdfs", "dfs"]

def create_dir_on_hdfs():
    return run_cmd(HDFS_COMMAND_PREFIX + ["-mkdir", DIR_NAME])

def upload_to_hdfs():
    return run_cmd(HDFS_COMMAND_PREFIX + ["-put", TEST_LOCAL_FILE, HDFS_TEST_PATH])


def get_replication_from_hdfs():
    return run_cmd(HDFS_COMMAND_PREFIX + ["-stat", "%r", HDFS_TEST_PATH])


def delete_test_file():
    run_cmd(HDFS_COMMAND_PREFIX + ["-rm", "-f", HDFS_TEST_PATH])
    if os.path.exists(TEST_LOCAL_FILE):
        os.remove(TEST_LOCAL_FILE)


def check_replication_factor_by_test_file():
    if create_dir_on_hdfs():
        print("FAIL: Could not create directory on hdfs")
    
    if not create_local_test_file():
        print("FAIL: Could not create local test file")
        return

    if upload_to_hdfs() is None:
        print("FAIL: Could not upload test file to HDFS")
        delete_test_file()
        return

    actual_replication = get_replication_from_hdfs()

    if actual_replication is None:
        print("FAIL: Could not retrieve replication factor from HDFS")
    elif actual_replication == EXPECTED_REPLICATION:
        print(f"PASS: Replication factor is {actual_replication}")
    else:
        print(f"FAIL: Replication factor is {actual_replication} (expected {EXPECTED_REPLICATION})")

    delete_test_file()


if __name__ == "__main__":
    check_configurations()
    check_replication_factor_by_test_file()
