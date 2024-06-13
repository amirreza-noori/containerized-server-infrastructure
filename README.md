# Containerized Server Infrastructure (Nginx + Gitlab/Jenkins/Github + Portainer)

This repository suggests a configuration to monitor and manage domains on a containerized web host.

Different configurations could be selected by editing the docker-compose.yml file in the root of the project. Just disable what you don't want by converting the line to the comment.

## Configuration

By the following step configuration.

### Install Docker and Docker-Compose

Install Docker on the operating system from [docker website](https://docs.docker.com/engine/install/).

Clone the repository and use docker compose in the root of the project.

```bash
git clone https://github.com/amirreza-noori/containerized-server-infrastructure.git
cd containerized-server-infrastructure
docker compose up -d --build
```

### Nginx Proxy Manager

Go to Cloudflare and add an `A` record for `*` domains that point to the host IP.

Open `<host-ip>:65510` in the browser. Use `admin@example.com` as email and `changeme` as password. Please change the default email and password after the first login.

Go to the `Proxy Hosts` part and add your domains and service as following:

```txt
<subdomain-for-jenkins>.<domain>
http://jenkins:8080

<subdomain-for-nginx>.<domain>
http://nginx-proxy-manager:81

<subdomain-for-portainer>.<domain>
https://portainer:9443

<subdomain-for-gitlab>.<domain>
http://gitlab:80
```

### Continuous Integration and Continuous Deployment (CI/CD)

In this part two options are available:

1. using Github and Jenkins for CI/CD
2. using self-hosted Gitlab and its runner

### Github/Jenkins

Build your repository in GitHub and add a `Jenkins` file in the project root (example file).

Open `https://<subdomain-for-jenkins>.<domain>` in your browser. Do the installation with Wizard. After installation click on `New Item`. In the pipeline part select to read Jenkins file from the repository address.

Then go to GitHub, open the `settings` of the project, click on `webhook`, and add the `https://<subdomain-for-jenkins>.<domain>/github-webhook/`.

### Self-hosted Gitlab

To use this method uncomment `./gitlab/docker-compose.yml` in the `docker-compose.yml`

To use this method uncomment `./gitlab/docker-compose.yml` in the `docker-compose.yml` file. Use [this article](https://www.czerniga.it/2021/11/14/how-to-install-gitlab-using-docker-compose/) and follow the `GitLab Lunching` part.

### Portainer

Portainer is a good monitoring tool for docker. No configuration is required, just open the subdomain and use it.
