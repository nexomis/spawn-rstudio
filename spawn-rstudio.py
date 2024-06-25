import argparse
import os
import subprocess
import getpass
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

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
    return parser.parse_args()

def render_template(args):
    # Load template
    path, filename = os.path.split(args.dockerfile_template)
    env = Environment(loader=FileSystemLoader(path or './'))
    template = env.get_template(filename)

    # Render template with arguments
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

def main():
    args = parse_args()
    rendered_dockerfile = render_template(args)
    build_and_run(rendered_dockerfile, args.image, args)
    print(f"Docker container '{args.name}' is running.")
    print(f"echo 'Server running with the following credentials:'")
    print(f"echo 'Username: {args.username} / {args.uid}'")
    print(f"echo 'Password: {args.password}'")
    print(f"echo 'Access at http://127.0.0.1:{args.port} to use RStudio Server.'")    


if __name__ == "__main__":
    main()
