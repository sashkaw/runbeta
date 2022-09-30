# RunBeta
Web app built with Django using the Strava API and geospatial terrain analysis to help you train better and plan safer routes

# For local development:

- Clone the repo
- Create a virtual environment in the same folder.
- Start virtual environment
- Install required packages with `pip install -r requirements.txt`
- Create a secrets file
- Create an sqlite database and add the credentials to settings.py
- Run migrations and create admin account:
	- `python manage.py migrate`
	- `python manage.py createsuperuser`
	- `python manage.py makemigrations mapdata`
	- `python manage.py migrate`
- Start development server with `python manage.py runserver`
- Open your browser and navigate to `http://127.0.0.1:8000/mapdata/` to see the homepage

