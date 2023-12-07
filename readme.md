# README

## Running the Project

This project uses Docker for easy setup and running. Follow the steps below to get it up and running on your local machine.

### Prerequisites

- Docker installed on your local machine. If you don't have it installed, you can download it from [here](https://www.docker.com/products/docker-desktop).

### Building the Docker Image

To build the Docker image, navigate to the project directory where the Dockerfile is located and run the following command:

```bash
docker build -t dash-test .
```

This command builds a Docker image using the Dockerfile in the current directory and tags it as "dash-test".

### Running the Application in Google Cloud vs Locally

When running this application in Google Cloud, it uses a Unix socket to connect to the database. However, when running the application locally, you'll need to have a Cloud SQL Proxy setup.

For instructions on how to set up the Cloud SQL Proxy, please refer to the top-level documentation our [GitHub page](https://github.com/stiftelsen-effekt).

### Running the Docker Image

To run the Docker image with environment variables, use the following command:

```bash
docker run -p 8050:8050 -e DB_USER=analysis -e DB_PASSWORD=Password dash-test
```

Replace Password in DB_PASSWORD with the password for the Analysis user.

This command runs the "dash-test" Docker image and maps the container's port 8050 to your local machine's port 8050. It also sets the specified environment variables.

Now, you should be able to access the application at `http://localhost:8050`.