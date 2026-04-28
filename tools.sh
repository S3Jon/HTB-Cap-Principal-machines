#!/bin/bash
sudo apt update && sudo apt install pipx git && pipx ensurepath && pipx install git+https://github.com/Pennyw0rth/NetExec && sudo apt install python3-argcomplete && register-python-argcomplete nxc >> ~/.bashrc
