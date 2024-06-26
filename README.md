# Spawn-rstudio

This Python script automates the process of building and running a Docker container for RStudio Server using a Jinja2-templated Dockerfile. It is designed to be flexible, allowing custom configurations through command line arguments.

## Prerequisites

- **Docker**: Ensure Docker is installed and running on your system.
- **Python 3**: Python 3.6 or higher is required to run the script.
- **Jinja2**: Required for templating Dockerfiles. Install using pip:
  ```
  pip install Jinja2
  ```

## Usage

```bash
python spawn-rstudio.py --image <base_image> --password <password> --volumes <volume_list>
```
- `--image`: The base image for the Docker container (tested with Ubuntu 22-based only).
- `--password`: Password for the user within the Docker container.
- `--volumes`: Comma-separated list of volumes to mount (ensure proper mapping and permissions).
- Additional optional arguments can be viewed using `-h`.

## Example command
```bash
python spawn-rstudio.py --image rocker/r-ver:4 --password your_password --volumes "/path/to/local:/path/in/container"
```

## Important Considerations

- **Operating System**: This script has been tested only with Ubuntu 22 based images.
- **Port Availability**: The default port is 8042. Ensure that this port is not in use on your machine before running the script.
- **Volume Mapping**: Be cautious with volume mappings; improper mappings or permissions might lead to errors or data loss.
- **Docker Context**: This script expects the Docker daemon running as the system's service. Usage with other Docker contexts, like Docker Desktop, might result in unexpected behavior.

## Troubleshooting

If you encounter issues related to Docker contexts or configurations, ensure:
- The Docker service is active and properly configured on your system.
- Your user has the necessary permissions to interact with Docker.
- The specified volumes and ports do not conflict with existing containers or system settings.

For detailed error logs, run Docker commands manually based on the output commands provided by the script.
