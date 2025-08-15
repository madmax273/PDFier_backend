#!/usr/bin/env bash
# Install Rust
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
