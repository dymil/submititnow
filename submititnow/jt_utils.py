import os
import glob
import os.path as osp
import json
from pathlib import Path
from dataclasses import dataclass
import argparse
from functools import partial
from typing import Optional
import simple_colors
import pandas as pd
from typing import Union

from experiment_utils import get_default_submititnow_dir

submititnow_root = get_default_submititnow_dir()

experiments_root = submititnow_root / 'experiments'


def get_running_job_ids():
    squeue_rows = os.popen('squeue -u mgor').read().splitlines()[1:]
    return list(map(lambda x: x.strip().split()[0].split('_')[0], squeue_rows))


def list_files(path):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            yield os.path.join(r, file)


def find_job_files(job_id, task_id):
    files = {}
    job_id_tag = f'{job_id}_{task_id}' if task_id is not None else str(job_id)
    for path in list_files(experiments_root):
        if path.endswith('.sh') and str(job_id) in path:
            files['sh'] = path
        elif job_id_tag in path:
            name = ext = path.rsplit('.')[-1]
            if ext == 'pkl':
                tag = name.rsplit('_')[-1]
                files[tag] = path
            else:
                files[ext] = path
    return files


def get_job_filepaths(job_task: str) -> dict[str, str]:
    if '_' in job_task:
        job_id, task_id = job_task.split('_')
    else:
        job_id, task_id = job_task, 0
    return find_job_files(job_id, task_id)


def get_job_filepath(job_task: str, file_type: str) -> str:
    return get_job_filepaths(job_task)[file_type]


def load_job_states(job_id):
    job_id = str(job_id)
    filepaths = get_job_filepaths(job_id)
    running_job_ids = get_running_job_ids()

    if 'out' not in filepaths and 'sh' in filepaths:
        if job_id.split('_')[0] in running_job_ids:
            return 'PENDING'
        else:
            return 'CANCELLED (before starting execution)'

    out_filepath = filepaths['out']
    err_filepath = filepaths['err']

    with open(out_filepath) as fp:
        out_lines = list(filter(lambda l: l.startswith('submitit '), fp.readlines()))

    with open(err_filepath) as fp:
        err_lines = list(filter(lambda l: l.startswith('srun: ') or l.startswith('slurmstepd: '), fp.readlines()))

    prefix, msg = out_lines[-1].split(' - ')

    def get_error_msg():
        return err_lines[-1].split(':', 4)[-1].strip()

    if 'completed successfully' in msg:
        return 'completed successfully'.upper()
    
    elif 'triggered an exception' in msg:
        return 'FAILED: Triggered an Exception'

    if err_lines and 'error' in err_lines[-1]:
        if 'CANCELLED' in err_lines[-1]:
            return 'CANCELLED (terminated by user)'
        else:
            return 'FAILED: ' + get_error_msg()

    if 'Loading' in msg or 'Starting' in msg:
        return 'RUNNING'

    return msg


@dataclass
class JTExp:
    exp_name: str

    @property
    def exp_dir(self):
        return experiments_root / self.exp_name

    @property
    def tracker_file(self):
        return self.exp_dir / 'tracker.csv'

    @property
    def logs_dir(self):
        return self.exp_dir / 'submitit_logs'

    def exists(self):
        return self.exp_dir.exists() and self.tracker_file.exists() and self.logs_dir.exists()

    def get_job_ids(self):
        return list(map(lambda x: x.strip().split()[0].split('_')[0], os.popen(f'squeue -u mgor | grep {self.exp_name}').read().splitlines()[1:]))

    def get_job_states(self):
        job_ids = self.get_job_ids()
        return list(map(load_job_states, job_ids))

    def get_job_states_df(self):
        job_ids = self.get_job_ids()
        job_states = self.get_job_states()
        return pd.DataFrame({'job_id': job_ids, 'state': job_states})

    def show_job_states(self):
        df = self.get_job_states_df()
        print(df)

    def load_csv(self):
        col_names = ['Timestamp', 'Job_Task', 'Job Description']
        df = pd.read_csv(self.tracker_file, delimiter='\t', names=col_names, header=None)
        job_series = df['Job_Task'].map(lambda x: int(str(x).split('_')[0]))
        df.insert(0, 'Job', job_series)
        # df = df.set_index('job', append=True).swaplevel(0,1)
        return df


def load_job_trackers(exp_name: Optional[str] = None):
    dirname = get_default_submititnow_dir()
    file_glob = f'{dirname}/{exp_name}.csv' if exp_name else f'{dirname}/*.csv'
    dfs = [load_csv(filename) for filename in glob.glob(file_glob)]
    return pd.concat(dfs)