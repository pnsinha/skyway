#!/bin/sh
#SBATCH -job-name=your-run
#SBATCH --account=rcc-aws
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --constraint=g1

echo "Greetings from VM!" > ~/output.txt

source activate pytorch
python training.py >> ~/output.txt
