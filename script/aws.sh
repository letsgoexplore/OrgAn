rm -rf organ
# git clone https://github.com/zhtluo/organ.git
git clone https://github.com/letsgoexplore/OrgAn.git
cd organ
git pull

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > install-rust.sh
bash install-rust.sh -y
source $HOME/.cargo/env
cargo build --release

# Use new SSH config. Enable if needed.
# sudo mv /home/ubuntu/sshd_config /etc/ssh/sshd_config
# sudo systemctl restart ssh
