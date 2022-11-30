# :rocket: Submit it Now! :rocket:

&nbsp;![License](https://img.shields.io/github/license/maharshi95/submititnow)
&nbsp;[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
&nbsp;[![Supported Python Versions](https://img.shields.io/badge/python-3.8+-blue)](https://pypi.org/project/rich/)
&nbsp;[![Twitter Follow](https://img.shields.io/twitter/follow/maharshigor.svg?style=social)](https://twitter.com/maharshigor)


A _makeshift_ toolkit, built on top of [submitit](https://github.com/facebookincubator/submitit), to launch SLURM jobs over a range of hyperparameters from the command line. It is designed to be used with existing python scripts and interactively monitor their status.


__`submititnow` provides two command-line tools:__
* `slaunch` to launch a python script as SLURM job(s).
* `jt` (job-tracker) to interactively monitor the jobs.

__It also provides a cleaner [`experiment_utils.Experiment`](submititnow/experiment_utils.py#162) API to create, launch and monitor an experiment, or a group of job(s), from python scripts with customized parameter-sweeping configurations.__

## `slaunch` : Launching a python script over SLURM

Let's say you have a python script [`examples/annotate_queries.py`](examples/annotate_queries.py) that can be run using following command:

```bash
python examples/annotate_queries.py --model='BERT-LARGE-uncased' \
    --dataset='NaturalQuestions' --fold='dev'
```
You can launch a job that runs this script over a SLURM cluster using following:
```bash
slaunch examples/annotate_queries.py \
    --slurm_mem="16g" --slurm_gres="gpu:rtxa4000:1" \
    --model='BERT-LARGE-uncased' --dataset='NaturalQuestions' --fold='dev'
```

### __Launching multiple jobs with parameter-sweep__

```bash
slaunch examples/annotate_queries.py \
    --slurm_mem="16g" --slurm_gres="gpu:rtxa4000:1" \
    --sweep fold model \
    --model 'BERT-LARGE-uncased' 'Roberta-uncased' 'T5-cased-small' \
    --dataset='NaturalQuestions' --fold 'dev' 'train'
```
This will launch a total of 6 jobs with following configuration:

![Slaunch Terminal Response](docs/imgs/slaunch_annotate_queries.png)

### __Any constraints on the target python script that we launch?__
The target python script must have the following format:

```python
import argparse

# User defined functions and classes

def main(args: argparse.Namespace):
    # Code goes here
    pass


def add_arguments(parser = None):
    parser = parser or argparse.ArgumentParser()
    # Return the parser after populating it with arguments.
    return parser


if __name__ == '__main__':
    parser = add_arguments()
    main(parser.parse_args())

```

## **`jt`** : &nbsp; Looking up info on previously launched experiments:

As instructed in the screenshot of the Launch response, user can utilize the `jt` (short of `job-tracker`) command to monitor the job progress.

### **`jt jobs EXP_NAME [EXP_ID]`**

Executing `jt jobs examples.annotate_queries 227720` will give following response:

![jt jobs EXP_NAME EXP_ID Terminal Response](docs/imgs/jt_annotate_queries_expid.png)

In fact, user can also lookup all `examples.annotate_queries` jobs simply by removing the `[EXP_ID]` from the previous command:
```
jt jobs examples.annotate_queries
```
![jt jobs EXP_NAME Terminal Response](docs/imgs/jt_annotate_queries.png)

### **`jt {err, out} JOB_ID`**
__Looking up stderr and stdout of a Job__

Executing `jt out 227720_2` reveals the `stdout` output of the corresponding Job:

![jt out JOB_ID Terminal Response](docs/imgs/jt_out_job_id.png)
Similar is case for `jt err 227720_2` which reveals `stderr` logs.

### **`jt sh JOB_ID`**
__Looking up SLURM SBATCH shell file of a Job__

submitit tool internally create an SBATCH shell script per experiment to launch the jobs on SLURM cluster. This command helps inspect this `submission.sh` file.

Executing `jt sh 227720_2` reveals the following:

![jt out JOB_ID Terminal Response](docs/imgs/jt_sh_job_id.png)

### **`jt ls`**
Finally, user can use `jt ls` to simply list the experiments maintains by the `submititnow` tool.

<img src="docs/imgs/jt_ls.png"  width=30%>

Outputs of this command can be further used to interact using `jt jobs` command.

## __Installing__
Python 3.8+ is required.

```bash
pip install -U git+https://github.com/maharshi95/submititnow.git
```
