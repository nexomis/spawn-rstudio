import argparse
import os
import subprocess
import getpass
from pathlib import Path
from jinja2 import Template

DOCKERFILE_TEMPLATE = """
FROM {{image}}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \\
    apt install -y wget sudo

RUN useradd -m -s /bin/bash -u {{uid}} -U {{username}} \\
    && echo "{{username}}:{{password}}" | chpasswd

RUN if [ -z "$(which rstudio-server)" ]; then \\
        apt install -y gdebi-core \\
        && . /etc/os-release \\
        && wget https://download2.rstudio.org/server/${VERSION_CODENAME}/amd64/rstudio-server-2023.12.1-402-amd64.deb \\
        && gdebi -n rstudio-server-2023.12.1-402-amd64.deb; \\
    else \\
        echo "RStudio Server is already installed."; \\
    fi

RUN echo "" >> $(Rscript -e 'cat(R.home())')/etc/Renviron.site \\
  && cat /etc/environment >> $(Rscript -e 'cat(R.home())')/etc/Renviron.site

RUN echo '{{username}} ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/{{username}} \\
 && echo "auth-required-user-group={{username}}" >> /etc/rstudio/rserver.conf \\
 && echo "#!/bin/bash" > /home/{{username}}/entrypoint.sh \\
 && echo "sudo service rstudio-server start" >> /home/{{username}}/entrypoint.sh \\
 && echo "echo 'Server running with the following credentials:'" >> /home/{{username}}/entrypoint.sh \\
 && echo "echo 'Username: {{username}}'" >> /home/{{username}}/entrypoint.sh \\
 && echo "echo 'Password: {{password}}'" >> /home/{{username}}/entrypoint.sh \\
 && echo "echo 'Access at http://127.0.0.1:{{port}} to use RStudio Server.'" >> /home/{{username}}/entrypoint.sh \\ && echo "sleep infinity" >> /home/{{username}}/entrypoint.sh \\
 && chmod +x /home/{{username}}/entrypoint.sh

EXPOSE {{port}}

ENTRYPOINT ["/home/{{username}}/entrypoint.sh"]
CMD []

"""

def parse_args():
    parser = argparse.ArgumentParser(description='Build and run a Docker container from a Jinja2 templated Dockerfile.')
    parser.add_argument('--image', required=True, help='Base image for the Docker container')
    parser.add_argument('--password', required=True, help='Password for the user in the Docker container')
    parser.add_argument('--name', default="local_rstudio", help='Username for the Docker container (default: local_rstudio)')
    parser.add_argument('--username', default=getpass.getuser(), help='Username for the Docker container (default: current user)')
    parser.add_argument('--uid', default=os.getuid(), type=int, help='User ID for the Docker container (default: UID of current user)')
    parser.add_argument('--port', default=8042, type=int, help='Port to expose on the Docker container (default: 4242)')
    parser.add_argument('--volumes', required = True, type=str, help='Comma-separated list of volumes to mount, home directly may not work.')
    parser.add_argument('--dockerfile_template', default='Dockerfile.j2', help='Path to the Dockerfile Jinja2 template (default: Dockerfile.j2 in current directory)')
    parser.add_argument('--force', action='store_true', help='Force stopping and removal of an existing container if it exists')
    return parser.parse_args()

def render_template(args):
    # Load template
    template = Template(DOCKERFILE_TEMPLATE)
    return template.render(image=args.image, password=args.password, username=args.username, uid=args.uid, port=args.port)

def build_and_run(rendered_dockerfile, image_name, args):
    # Save the rendered Dockerfile
    temp_dockerfile_path = 'Dockerfile.temp'
    with open(temp_dockerfile_path, 'w') as file:
        file.write(rendered_dockerfile)

    # Build the Docker image
    subprocess.run(['docker', 'build', '-t', args.name, '-f', temp_dockerfile_path, '.'], check=True)

    docker_command = ['docker', 'run', '-d', '-u', f'{args.uid}:{args.uid}', '-w', f'/home/{args.username}', '--name', args.name, '-p', f"{args.port}:8787"]
    volumes = args.volumes.split(",")
    for volume in volumes:
        docker_command.extend(["-v",f"{volume}:{volume}"])
    docker_command.append(args.name)
    # Run the Docker container in detached mode
    subprocess.run(docker_command, check=True)

def check_running_container(args):
    running_result = subprocess.run(
        ['docker', 'ps', '-q', '--filter', f'name={args.name}'],
        capture_output=True, text=True)
    running_container_id = running_result.stdout.strip()

    existing_result = subprocess.run(
        ['docker', 'ps', '-aq', '--filter', f'name={args.name}'],
        capture_output=True, text=True)
    existing_container_id = existing_result.stdout.strip()

    if existing_container_id != "":
        print(f"Warning: A container named '{args.name}' is already running.")
        if args.force:
            print(f"Stopping and removing the container '{args.name}'.")
            if running_container_id == existing_container_id:
                subprocess.run(['docker', 'stop', args.name], check=True)
            subprocess.run(['docker', 'rm', args.name], check=True)
        else:
            print(f"Use --force to stop and remove the existing container.")
            exit()

def main():
    args = parse_args()
    rendered_dockerfile = render_template(args)
    check_running_container(args)
    build_and_run(rendered_dockerfile, args.image, args)
    print(f"Docker container '{args.name}' is running.")
    print(f"echo 'Server running with the following credentials:'")
    print(f"echo 'Username: {args.username} / {args.uid}'")
    print(f"echo 'Password: {args.password}'")
    print(f"echo 'Access at http://127.0.0.1:{args.port} to use RStudio Server.'")    


if __name__ == "__main__":
    main()

