# RunBeta
Web app built with Django using the Strava API and geospatial terrain analysis to help you train better and plan safer routes

# For local development:
- Clone the repo
- `cd` into the repo
- Create secrets files
- Start the Docker desktop app
- Build the image with Docker
	- `docker compose up --build`
- While the image is running, open a new terminal window and view the containers that are currently running
	- `docker ps`
- Open a new interactive terminal for a running container with
	- `docker exec -it <container_name> bash`
- Run Django migrate from inside the above container
	- `python manage.py migrate`
	- `python manage.py createsuperuser` (if you want to access the admin site)
- Close the currently running container
	- Type `ctrl+c` in the original window where the container is running
	- (Note: If you want to exit the interactive window inside the container you can type `ctrl+d`)
- Restart the container
	- `docker compose up`
- Open your browser and navigate to `http://127.0.0.1:8000/login` to see the login page
- To stop the container you can run `docker compose down`

# Troubleshooting:
- If you run into Docker + postgres / DB issues and you want to start from scratch:
	- Delete the 'data' folder in the repo that is created when you build the image
	- Run `docker system prune -a` (caution: this deletes all unused images so proceed with care)