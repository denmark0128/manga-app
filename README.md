steps to install: 
open powershell then type:

git clone https://github.com/denmark0128/manga-app.git

cd projectone

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

python manage.py runserver
