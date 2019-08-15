from app import app, db
from flask import (Flask,
                   render_template,
                   request,
                   url_for,
                   flash,
                   redirect,
                   session)
from app.forms import (SearchForm,
                       LoginForm,
                       RegistrationForm,
                       AddToDiaryForm,
                       RemoveFood,
                       DiaryDatePicker,
                       SetMacroForm,
                       SetMacroGrams,
                       QuickAddCals,
                       CopyMealForm)
from app.models import User, Food
import requests
from jinja2 import Template
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm.session import make_transient


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
@app.route('/search/<string:date>/<string:meal>', methods=['GET', 'POST'])
@login_required
def search(date=None, meal=None):
    form = SearchForm()
    
    if request.method == 'GET':
        food_list_clean = []
        recent_list = True
        recent_foods = Food.query.filter_by(user_id=current_user.get_id()).order_by(
            desc(Food.id)).group_by(Food.food_name)
        
        for food in recent_foods:
            food_list_clean.append((food.food_name, food.ndbno, food.id))

        return render_template('search.html', form=form, food_list_clean=food_list_clean,
                               recent_list=recent_list, date=date, meal=meal)

    if request.method == 'POST':
        if request.form["action"] == "multiadd":
            food_ids = request.form.getlist("selected")
            
            if meal == None:
                meal = request.form.get('mealselect')
                
            for food_id in food_ids:
                food = Food.query.filter_by(id=food_id).first()
                food = Food(food_name=food.food_name, count=food.count,
                            kcal=food.kcal,
                            protein=food.protein,
                            fat=food.fat,
                            carbs=food.carbs,
                            unit=food.unit, meal=meal,
                            ndbno=food.ndbno, date=date,
                            user_id=current_user.get_id())
                db.session.add(food)
                db.session.commit()
            return redirect(url_for('diary', date_pick = date))

        else:
            recent_list = False

            # get user input from search bar
            food_search = form.search.data
            if food_search == "":
                return redirect(url_for('search', date=date, meal=meal))

            # build API URL to search for food
            search_url = "https://api.nal.usda.gov/ndb/search/?format=json"
            params = dict(
                q=food_search,
                sort="r",
                max="100",
                offset="0",
                ds="Standard Reference",
                api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe"
            )

            # build list of tuples w/ name of food and associated ndbno (unique ID)
            resp = requests.get(url=search_url, params=params)
            if "zero results" in str(resp.json()):
                flash("No results found.")
                return redirect(url_for('search'))
            else:
                food_list = resp.json()['list']['item']
                food_list_clean = []

                for i in food_list:
                    food_list_clean.append((i['name'], i['ndbno']))

                # return list of food to web page
                return render_template('search.html', date=date, meal=meal,
                                       food_list_clean=food_list_clean, form=form, recent_list=recent_list)


@app.route('/food/<string:ndbno>', methods=['GET', 'POST'])
@app.route('/food/<string:date>/<string:meal>/<string:ndbno>',
           methods=['GET', 'POST'])
@login_required
def get_nutrition(ndbno, meal=None, date=datetime.now()):

    form1 = AddToDiaryForm()

    search_url = "https://api.nal.usda.gov/ndb/nutrients/?format=json"
    params = dict(
        api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe",
        nutrients=["205", "204", "208", "203"],
        ndbno=ndbno
    )

    resp = requests.get(url=search_url, params=params)

    if "No food" in str(resp.json()):
        flash("No foods found.")
        return redirect(url_for('search'))
    else:
        food_name = resp.json()['report']['foods'][0]['name']
        food_measure = resp.json()['report']['foods'][0]['measure']
        food_cals = resp.json()['report']['foods'][0]['nutrients'][0]['value']
        food_protein = resp.json(
        )['report']['foods'][0]['nutrients'][1]['value']
        food_fat = resp.json()['report']['foods'][0]['nutrients'][2]['value']
        food_carbs = resp.json()['report']['foods'][0]['nutrients'][3]['value']

    if request.method == 'GET':
        return render_template('nutrition.html',
                                meal=meal,
                                date=date,
                                food_name=food_name,
                                food_measure=food_measure,
                                food_cals=food_cals,
                                food_protein=food_protein,
                                food_fat=food_fat,
                                food_carbs=food_carbs,
                                ndbno=ndbno,
                                form1=form1,
                                )

    if request.method == 'POST':
        if meal is None:
            meal_choice = form1.meal.data
        else:
            meal_choice = meal
            
        try:
            quant_choice = float(form1.quantity.data)
        except:
            flash("Please enter valid values.")
            return redirect(url_for('get_nutrition', ndbno=ndbno,
                                    meal=meal, date=date))
        else:
            if quant_choice > 10000 or meal_choice not in ("Breakfast", "Lunch", "Dinner", "Snacks"):
                flash("Please enter valid values.")
                return redirect(url_for('get_nutrition', ndbno=ndbno,
                                        meal=meal, date=date))
            else:
                food = Food(food_name=food_name, count=quant_choice,
                            kcal=quant_choice * float(food_cals),
                            protein=quant_choice * float(food_protein),
                            fat=quant_choice * float(food_fat),
                            carbs=quant_choice * float(food_carbs),
                            unit=food_measure, meal=meal_choice,
                            date=date, ndbno=ndbno, user_id=current_user.get_id())
                db.session.add(food)
                db.session.commit()
        
                return redirect(url_for('diary', date_pick=date))


@app.route('/diary', methods=['GET', 'POST'])
@app.route('/diary/<string:date_pick>', methods=['GET', 'POST'])
@login_required
def diary(date_pick=datetime.now().strftime('%B %d, %Y')):

    form = RemoveFood()
    form2 = DiaryDatePicker()

    if request.method == 'GET':

        # make sure user didn't tamper with the date URL to throw an error
        try:
            datetime.strptime(date_pick, '%B %d, %Y')
        except ValueError:
            return redirect(url_for('diary'))

        session.pop('_flashes', None)

        form2.date.data = date_pick

        foods = Food.query.filter_by(user_id=current_user.get_id(), date=date_pick)
        user = User.query.filter_by(id=current_user.get_id()).first()

        meals = {'Breakfast':0, 'Lunch':0, 'Dinner':0, 'Snacks':0, 'total':0}
        total_cals = dict(meals)
        total_carbs = dict(meals)
        total_protein = dict(meals)
        total_fat = dict(meals)

        for food in foods:
            total_cals['total'] = total_cals['total'] + food.kcal
            total_carbs['total'] = total_carbs['total'] + food.carbs
            total_protein['total'] = total_protein['total'] + food.protein
            total_fat['total'] = total_fat['total'] + food.fat

            for meal in meals:
                if str(food.meal) == str(meal):
                    total_cals[meal] = total_cals[meal] + food.kcal
                    total_carbs[meal] = total_carbs[meal] + food.carbs
                    total_protein[meal] = total_protein[meal] + food.protein
                    total_fat[meal] = total_fat[meal] + food.fat

        return render_template('diary.html', foods=foods, user=user, form=form,
                            form2=form2, total_fat=total_fat,
                            total_cals=total_cals, total_carbs=total_carbs,
                            total_protein=total_protein, date_pick=date_pick)

    if request.method == 'POST':

        if request.form["action"] == "remove":
            remove_id = form.entry_id.data
            user_id_for_row = Food.query.filter_by(
                id=remove_id).first().user_id
            if str(user_id_for_row) == current_user.get_id():
                Food.query.filter_by(id=remove_id).delete()
                db.session.commit()
            else:
                flash("Cannot access this entry.")

        elif request.form["action"] == "back":
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') -
                         timedelta(days=1)).strftime('%B %d, %Y')

        elif request.form["action"] == "forward":
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') +
                         timedelta(days=1)).strftime('%B %d, %Y')

        # redirect back to diary; if date is today, exclude ugliness from URL
        todays_date = datetime.now().strftime('%B %d, %Y')
        if date_pick == todays_date:
            return redirect(url_for('diary'))
        else:
            return redirect(url_for('diary', date_pick=date_pick))


@app.route('/diary/quickadd/<string:date>/<string:meal>', methods=['GET', 'POST'])
@login_required
def quickadd(date=datetime.now().strftime('%B %d, %Y'), meal=None):
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = QuickAddCals()

    if request.method == 'GET':
        return render_template('quickadd.html', user=user, form=form)

    if request.method == 'POST':
        try:
            float(form.calories.data)
            float(form.carbs.data)
            float(form.fat.data)
            float(form.protein.data)
        except:
            flash("Please enter valid numbers.")
        else:
            food = Food(food_name='Quick Add', count=1,
                kcal=form.calories.data,
                protein=form.protein.data,
                fat=form.fat.data,
                carbs=form.carbs.data,
                unit='', meal=meal,
                date=date, ndbno=-1, user_id=current_user.get_id())
            db.session.add(food)
            db.session.commit()
        return redirect(url_for('diary', date_pick=date))


@app.route('/diary/copyto/<string:date>/<string:meal>', methods=['GET', 'POST'])
@login_required
def copyto(date, meal):
    form = CopyMealForm()
    
    if request.method == 'GET':
        return render_template('copyto.html', form=form)

    if request.method == 'POST':
        copy_to_date = form.dt.data.strftime('%B %d, %Y')
        copy_to_meal = form.meal_select.data
        copy_meal_items = Food.query.filter_by(user_id=current_user.get_id(),
                                            date=date,
                                            meal=meal)
        
        for row in copy_meal_items:
            db.session.expunge(row)
            make_transient(row)
            row.id = None
            row.meal = copy_to_meal
            row.date = copy_to_date
            db.session.add(row)
        
        db.session.commit()
        return redirect(url_for('diary', date_pick = copy_to_date))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password.')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('diary')
            return redirect(next_page)
        return render_template('login.html', form=form)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/profile/macrosgrams', methods=['GET', 'POST'])
@login_required
def macros_grams():
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = SetMacroGrams(calories=user.calories_goal)

    if request.method == 'GET':
        return render_template('macros_grams.html', user=user, form=form)

    if request.method == 'POST':
        try:
            float(form.carbs.data)
            float(form.fat.data)
            float(form.protein.data)
        except:
            flash("Please enter valid numbers.")
        else:
            user.carbs_grams = form.carbs.data
            user.fat_grams = form.fat.data
            user.protein_grams = form.protein.data
            user.calories_goal = (form.carbs.data * 4) + \
                (form.fat.data * 9) + (form.protein.data * 4)
            db.session.commit()
            flash("Macros updated.")
        return redirect(url_for('macros_grams'))


@app.route('/profile/macrospercent', methods=['GET', 'POST'])
@login_required
def macros_percent():
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = SetMacroForm(calories=user.calories_goal,
                        fat=float(user.fat_goal),
                        carbs=float(user.carb_goal),
                        protein=float(user.protein_goal))

    if request.method == 'GET':
        return render_template('macros_percent.html', user=user, form=form)

    if request.method == 'POST':
        valid_percents = [.05, .1, .15, .2, .25,
                    .3, .35, .4, .45, .5, .55, .6,
                    .65, .7, .75, .8, .85, .9]
        try:
            # server-side input validation
            # check form values convert to float successfully
            # check macros add up to 100% of calories
            # check macro percentages chosen are among available
            sum_macro_percents = (float(form.protein.data) +
                                    float(form.fat.data) +
                                    float(form.carbs.data))
            if not (float(form.protein.data) in valid_percents
                    and float(form.fat.data) in valid_percents
                    and float(form.carbs.data) in valid_percents):
                flash("Error: Please enter valid values.")
                return redirect(url_for('macros_percent'))
            if sum_macro_percents != 1.00:
                flash("Values did not add up to 100%: try again!")
                return redirect(url_for('macros_percent'))
        except:
            flash("Error: Please enter valid values.")
            return redirect(url_for('macros_percent'))
        else:
            # update db values
            try:
                user.calories_goal = int(form.calories.data)
            except:
                flash('Please enter valid calorie value.')
                return redirect(url_for('macros_percent'))
            user.protein_goal = form.protein.data
            user.fat_goal = form.fat.data
            user.carb_goal = form.carbs.data
            user.protein_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.protein_goal)) / 4))
            user.fat_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.fat_goal)) / 9))
            user.carbs_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.carb_goal)) / 4))
            db.session.commit()

            flash("Macro targets updated.")
            return redirect(url_for('macros_percent'))


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     else:
#         form = RegistrationForm()
#         if form.validate_on_submit():
#             user = User(username=form.username.data, email=form.email.data)
#             user.set_password(form.password.data)
#             db.session.add(user)
#             db.session.commit()
#             flash('Congratulations, you are now a registered user!')
#             return redirect(url_for('login'))
#         return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    # logout_user is a flask_login function
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')