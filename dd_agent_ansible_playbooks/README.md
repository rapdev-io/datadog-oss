# Experian Ansible Demo

The purpose of this repository is to setup a demo of Ansible for Experian. It is a minimalistic approach as a POC to show them how it works.

## Setup

There are a few prerequisites that need to be addressed prior to running the Ansible code.

First of all - Install Ansible. Follow the instructions here: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html

Second of all - we need servers. Clone the https://github.com/rapdev-io/experian_terraform if they don't exist, `terraform init`, and then `terraform apply` should do the trick.
The SQL server will already have SQL installed and running, nginx is just an ubuntu server. When they are up and running, grab the public IPs of the servers and enter them under
`ansible_host` for the corresponding server in `inventory.yaml`.

Third of all - you'll need Nick's ec2 key. Ask them for it. In the `inventory.yaml` file, change the path of the private key file, because you're (probably) not `nickv` if you're reading this.

## Executing a Playbook

There are three playbooks provided here:
1. `datadog_playbook.yaml` installs the Datadog agent on both machines
2. `nginx_playbook.yaml` installs nginx on the webserver
3. `sqlserver_playbook.yaml` sets up the Datadog sqlserver user

The Datadog agent sets up configurations based on whats in that playbook, as well as the variables that are found in the `group_vars` directory. This way, we can install the `windows_service` and `sqlserver`
integrations for the Windows server, and `nginx` integration for the webserver, while keeping that information separate.

The ngnix playbook installs nginx and updates the config file, and restart nginx. Useful for demonstrating how changes care made.

The sqlserver playbook will fail, and that's intentional. It fails because the user is already created. The idea here is to show how failures are descriptive and useful.

To run any of these, run the following command:
```
ansible-playbook -i inventory.yaml -e @vault --ask-vault-pass playbooks/$playbook.yaml
```
where `$playbook.yaml` is substituted with one of the available playbooks. This command will prompt you for a password to decrypt the vault file with passwords. Hint: the password is `test`.

## Running the Demo

1. Prior to the demo, use the terraform repo above to rebuild the instances so we can have a fresh start
2. Run `ansible-playbook -i inventory.yaml -e @vault --ask-vault-pass playbooks/datadog_playbook.yaml` playbook
3. While this is running in the terminal showing it working, walk through the different portions of the repository
    a. Starting with the inventory, explain how grouping works and how variables within the inventory work
    b. Move into the Datadog playbook; show that some global configuration is present
    c. Move to the group vars to show how integrations are setup; also note that the sqlserver is running a different agent version
    d. Move through the other playbooks; show how the nginx playbook installs nginx, copies configs, and makes sure it's running. Show how the sql playbook creates a user with powershell
4. When the primary playbook has finished, jump over to datadog and search for the hosts prefixed with "nickv"; show that integrations are already running
5. Explain how the vault works

## Creating Secrets using Ansible Vault

To create secrets using ansible vault create a file and store your secrets in a key value format:

```
vault_dd_api_key: "********************"
````
Then run the following command to encrypt the file

```
ansible-vault encrypt vault.yml
```
You will be prompted to provide a password so that you can access the file. DO NOT loose this password or you will be unable to reopen the vault. 

To edit or view the vault run the following command
```
ansible-vault edit vault
```