# CebraEM

## Installation

### Installing Miniconda

1. Download Miniconda: https://docs.anaconda.com/free/miniconda/miniconda-install/
Choose the installer based on your operating system (Windows, macOS, or Linux) and download it. Once the download is complete, run the installer. F
During the installation process, you might be asked whether you want to add Miniconda to your PATH. It's recommended to select this option as it allows you to run Conda and Python commands from any directory in your terminal or command prompt. Open a new terminal or command prompt window and type conda --version. If Miniconda was installed successfully, you should see the version number of Conda printed in the terminal.

2. Installing Mamba
Open a Terminal or Command Prompt:
```
conda install -c conda-forge mamba
```
This command tells Conda to install Mamba from the conda-forge channel.
With Miniconda or Mamba installed, you can now create Python environments, install packages, and manage your Python projects with ease. 

For the following descriptions an installation of Mamba is assumed (otherwise just replace "mamba" -> "conda")

### CebraEM conda environment

The following commands install CebraEM as well as all dependencies except pytorch
```
mamba create -y -n cebra-em-env -c conda-forge python=3.9 vigra
conda activate cebra-em-env
```

For pytorch you will need to determine your Cuda version and select the correct installation call. 
Please refer to https://pytorch.org/get-started/locally/ for further information.
As an example, for our system with Cuda version 11, we installed pytorch successfully using this pip install command: 

```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```


### Testing the installation

The following script runs the main steps of the CebraEM pipeline using a small test dataset.

```
conda activate cebra-em-env
python test_installation.py
```

Possible errors:

```
ModuleNotFoundError: No module named 'torch'
```

The installation of pytorch is missing or did not work properly. 
Run ```nvidia-smi``` to determine your Cuda version and refer to https://pytorch.org/get-started/locally/ to determine 
the proper pytorch installation commands

## CebraEM

[CebraEM readme](cebra-em/README.md)

Contains:
 - Usage of CebraEM

## CebraANN

[CebraANN readme](cebra-ann/README.md)

Contains:
 - Specific installation for the cebra-ann package in case CebraANN needs to be run on a separate machine
 - Usage of CebraANN

## CebraNET

[CebraNET readme](CebraNET_README.md)
