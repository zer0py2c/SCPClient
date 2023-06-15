import os
import re
import logging
import paramiko
from scp import SCPClient

base_dir = os.path.abspath(os.path.dirname(__file__))


class SCPClientWorker(object):

    base_timeout, socket_timeout = 30.0, 45.0

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client = None
        self.scp_client = None

    def invoke(self, command="cd /home/zer0py2C && python compress_files.py", end_loginfo="zip compressed!"):
        p = re.compile(end_loginfo)
        self._get_client(use_scp=False)
        channel = self.ssh_client.invoke_shell()
        channel.send(command + "\n")
        while True:
            stdout = channel.recv(1024)
            res = stdout.decode()
            print(res)
            if p.search(res):
                print("invoke finish!")
                break

    def recv_file(self, filename, remote_dir, local_dir):
        remote_path = os.path.join(remote_dir, filename)
        attempts, success = 0, False
        while not success:
            try:
                self.scp_client.get(remote_path, local_dir)
                success = True
            except:
                self.close()
                attempts += 1
                file_path = os.path.join(local_dir, filename)
                os.path.isfile(file_path) and os.remove(file_path)
                self._get_client()
        if success:
            self.end2trans(local_dir, filename)

    def send_file(self, filename, local_dir, remote_dir):
        local_path = os.path.join(local_dir, filename)
        attempts, success = 0, False
        while not success:
            try:
                self.scp_client.put(local_path, remote_dir)
                success = True
            except:
                self.close()
                attempts += 1
                self._get_client()

    def end2trans(self, local_dir, filename, mark="_scp_finished.zip"):
        file_path_old = os.path.join(local_dir, filename)
        file_path_new = os.path.join(local_dir, mark)
        os.remove(file_path_old, file_path_new)

    def _get_client(self, use_scp=True):
        if not isinstance(self.ssh_client, paramiko.SSHClient):
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            ssh_client.connect(self.host, self.port, self.username, self.password, 
                timeout=SCPClientWorker.base_timeout)
            self.ssh_client = ssh_client
        if use_scp:
            scp_client = SCPClient(self.ssh_client.get_transport(), 
                socket_timeout=SCPClientWorker.socket_timeout)
            self.scp_client = scp_client

    def close(self):
        if isinstance(self.ssh_client, paramiko.SSHClient):
            if isinstance(self.scp_client, SCPClient):
                self.scp_client.close()
            self.ssh_client.close()

    @classmethod
    def get_logger(cls, log_path, method_name):
        logging_name = "%s.%s" % (cls.__name__, method_name)
        logger = logging.getLogger(logging_name)
        logger.setLevel(level=logging.DEBUG)
        # file log
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(logging.INFO)
        format_ = "[%(asctime)s] [%(levelname)s] [%(name)s] : [%(message)s]"
        formatter = logging.Formatter(format_)
        handler.setFormatter(formatter)
        # console log
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.addHandler(console)
        return logger
