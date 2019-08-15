# https://stevensmacroapp.herokuapp.com/
Daily food log to track calories/macronutrients against set goals.

# Installation

**1. Fork and clone repository.**

**2. Start a virtual environment in repo directory and activate it.**
```
$ virtualenv venv
$ source venv/bin/activate
```

**3. Install dependencies.**
```
$ pip install -r requirements.txt
```

**4. Set environment variable FLASK_APP = macroapp.py**
```
$ export FLASK_APP='macroapp.py'
```

**5. Initialize the user/food database tables.**
```
$ flask db init
$ flask db migrate
$ flask db upgrade
```

**6. Run flask app.**
```
$ flask run
```

# To Do:

### Bug Fixes
- ~~Fix adding recent foods to days other than current.~~

### Additional functionality
- ~~Improve workflow so that I don't have to push to heroku to see every change~~
- ~~Implement quick-add calories functionality~~
- ~~Implement copy-to functionality~~
- Add weight tracking module
- Switch USDA API to openfood database
- Add pagination on search page
- Get more nutrients and display them on Nutrition page
- Add barcode scanning
- Research porting site to Android and iOS apps

### Design

### Other
- Add more documentation within code
