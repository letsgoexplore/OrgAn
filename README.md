# OrgAn: Organizational Anonymity with Low Latency

This is a prototype implementation of the OrgAn protocol proposed in the paper 'OrgAn: Organizational Anonymity with Low Latency'. 
The protocol follows a client/relay/server model, where the setup server provides secret shares of a publicly known value to the clients. The clients in the organisation communicate anonymously through the relay with the outside world. The communication proceeds in Base and Bulk rounds. 

The clients use Base round for slot selection and Bulk round to forward their messages in the chosen slots. Each client computes randomness to mask the slot messages as a polynomial ring element using a almost key-homomorphic PRF output. The relay collects all the messages from all the clients in a Base round, computes the Newton's sum equation system and solves it to obtain a random permutation of client input values. This permutation is used to select slots in the Bulk round. Clients choose a 64 bit random value for slot selection in the Base round. In the Bulk round, a client can forward 226 bits of message per allotted slot.  

If you want to view the original ReadMe, please forward to https://github.com/zhtluo/organ.git. Hear, we mainly focus on how to do evaluation.

## 0 Declaration of Change with original

### 0.1 Previous problems

There are some inconvenience of previous code:

- Explanation not clear enough

- No time for ssh confimation, if first time connect with aws server

Here, we want to measure client scale more than 200, and we encounter several problem:

- Previous ssh session is not enough

- Some file cannot be send in one time

### 0.2 Change

- (Add) first_setup.sh : give time for ssh confirmation, save duplicate caluculation of private ip

- (Add) send_shares.sh : resend the file

- (Change) setup.sh : add resend mechanism

- (Style) more comment

## 1 Installation

To test out the repo, either use the package from Docker, or install all dependencies manually.

### 1.1 Pull from Docker

```
docker pull ghcr.io/zhtluo/organ:latest
docker run -it ghcr.io/zhtluo/organ:latest 
```

## 2 Steps to repeat the benchmarks reported in the paper

### 2.1 What can you measure?

You can measure all client num(64, 111, 123 ...)

### 2.2 High-level Procedure

1. change config (client num you want to measure) in `script/config` and the shell script in `script`(they are noted with "CHANGE", you can search for it)

2. update `script/ip.txt` and `organ,pem`

3. check `script/sshd_config` to ensure ssh config

4. `bash ./script/first-setup.sh ./script/ip.txt` to setup params

5. `bash ./script/setup.sh ./script/ip.txt` to generate shares and send to aws server

6. (optional) `bash ./script/send_share.sh ./script/ip.txt` in case some files is not sent successfully

7. `bash ./script/run.sh ./script/ip.txt` to run the test, and send back the result

8. `./script/extract.sh` to culculate the outcome

### 2.3 Details

Details for the above "High-level Procedure":

1. You can search for `CHANGE`, where should be like:

```shell
# script/setup.sh L8
# CHANGE: You can modify your number here
TEST_SET=("50" "100" "150" "200")
```

Then you can change the client list you want to test.

2.  Set up AWS and add the node IPs into a `<Your IP address filename.txt>` file, one per line with the first IP being the IP of the relay node.
    
  - Reminder from Jason: if you want to use 5 aws ec2 to simulate 100 client, remember to fill 100 ip with replicate into `<Your IP address filename.txt>`.
  
  - The scripts (eg: `run.sh`, `setup.sh`) from the folder `scripts` use an `~/organ.pem` as the SSH keypair to access the AWS machines. Modify it to reflect your keys.

3.  You may need to modify `MaxSessions 200` and `MaxStartups 200:30:250`.

5.  Run `bash ./script/setup.sh <Your IP address filename.txt>` to build the prototype on each of the machines. Note you may have to modify `./script/get_pvt_ip.sh` to recognize your subnet if your private network address is different from `172.31.*.*`.

7.  Run `bash ./script/run.sh <Your IP address filename.txt>` to run all the tests and fetch the log under `./log/`.

8.  You may analyze the log anyway you want. For simplicity a code snippet is provided under `./script/extract.sh`.

## Further details on the options available for the protocol configuration. 

The configuration `.json` files of local test `./script_local/config` or AWS network tests in `/script/config/<no of clients>/` offer the below variables which can be changed from the default values specified (also viewable in `/src/config.rs`)  are stated below. Each test is accompanied with a `.json` file that specifies the setting for that run. An example of the file should look like this:

```
{
  "server_addr": "127.0.0.1:8001",
  "client_size": 5,
  "base_params": {
    "p": {
      "radix": 16,
      "value": "ffffffffffffffc5"
    },
    "q": {
      "radix": 16,
      "value": "fffffffffffffffffffdd"
    },
    "ring_v": {
      "order": {
        "radix": 16,
        "value": "39000000000000000000000001"
      },
      "root": {
        "radix": 16,
        "value": "1e8593afe765eb54ad28c5a71a"
      },
      "scale": {
        "radix": 16,
        "value": "1000000000000000000000000"
      }
    },
    "vector_len": 2048,
    "bits": 64,
    "group_nid": 714
  },
  "bulk_params": {
    "p": {
      "radix": 16,
      "value": "3fffffffffffffffffffffffffffffffffffffffffffffffffffffffb"
    },
    "q": {
      "radix": 16,
      "value": "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
    },
    "ring_v": {
      "order": {
        "radix": 16,
        "value": "1c000000000000000000000000000000000000000000000000000000000000000000000001"
      },
      "root": {
        "radix": 10,
        "value": "2187"
      },
      "scale": {
        "radix": 16,
        "value": "4000000000000000000000000000000000000000000000000000000000000000000000000"
      }
    },
    "vector_len": 8192,
    "bits": 226,
    "group_nid": 733
  },
  "round": 10,
  "slot_per_round": 3,
  "do_blame": false,
  "do_unzip": false,
  "do_delay": false,
  "do_ping": false
}
```

1. `server_addr`: The address of the relay and the port used. **Must be included.**
1. `client_size`: The number of clients. **Must be included.**
1. `base_params`: The parameters for the Base round, including `p`, `q`, `v`, the length of the vector in the communication `vector_len`, number of bits per round `bits`, and the ECC group id for the blame protocol as specified by OpenSSL `group_nid`. If omitted, the default value will be used.
1. `bulk_params`: The parameters for the Bulk round, same as the Base round. If omitted, the default value will be used.
1. `round`: The total number of rounds to run. **Must be included.**
1. `slot_per_round`: How many slots does each client use per Bulk round. This is the total message length divided by 226 (rounded to the next integer). **Must be included.** 
1. `do_blame`: Whether or not to test blame protocol by running it every round. Defaults to false.
1. `do_unzip`: Whether or not to unzip and compute PRF values on-demand. Defaults to false.
1. `do_delay`: Whether or not to delay before sending message. Useful in measuring optimal round trip time. Defaults to false.
1. `do_ping`: Whether or not to simulate the real environment by performing a ping after the bulk round. Defaults to false.

## Generate documentation

Run
```
cargo doc
```
to generate documentation on the code.

## License

This project is licensed under GNU General Public License v3.0. See `LICENSE` for details.