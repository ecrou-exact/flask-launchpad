<img width="676" height="369" alt="image" src="https://github.com/user-attachments/assets/6440edd6-17b7-47c8-a744-fefd296693ca" />


Flask application template

## What's in ?

- Vuejs3

- Blueprints

- Flask-Login

- Flask-SQLAlchemy for databases

- Flask-WTF for forms

- Flask-session for sessions

- Some roles are already created

## Installation

**It is strongly recommended to use a virtual environment**

If you want to know more about virtual environments, [python has you covered](https://docs.python.org/3/tutorial/venv.html)

```bash
pip install -r requirements.txt
python3 app.py -i                            ## Initialize db
```

## Config

Edit `config.py`

- `SECRET_KEY`: Secret key for the app

- `FLASK_URL` : url for the instance

- `FLASK_PORT`: port for the instance

## Launch

```bash
./launch.sh -l
```
