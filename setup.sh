#source ~/.bashrc
#false | conda create -n deform python=3.11 pytorch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 pytorch-cuda=12.1 pyg -c pytorch -c nvidia -c pyg
#conda activate deform
#python -m pip install -U matplotlib tqdm wandb open3d
#python -m pip install --upgrade https://github.com/unlimblue/KNN_CUDA/releases/download/0.2/KNN_CUDA-0.2-py3-none-any.whl

# setup.sh
source ~/.bashrc || source ~/.zshrc  # Ensure conda is initialized
eval "$(conda shell.zsh hook)"       # Ensure Conda is in the shell session

# Create environment if it doesn't exist
if ! conda info --envs | grep -q deform; then
    conda create -n deform python=3.11 pytorch==2.5.0 torchvision==0.20.0 \
    torchaudio==2.5.0 pytorch-cuda=12.1 pyg -c pytorch -c nvidia -c pyg -y
fi

# Activate environment
conda activate deform

# Install Python packages
python -m pip install -U matplotlib tqdm wandb open3d
python -m pip install --upgrade https://github.com/unlimblue/KNN_CUDA/releases/download/0.2/KNN_CUDA-0.2-py3-none-any.whl
