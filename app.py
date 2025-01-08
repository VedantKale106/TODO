from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId 
import datetime
from dotenv import load_dotenv
import os
import bcrypt  

load_dotenv()

app = Flask(__name__)
app.secret_key = '122333'  
#AADITESH WAS HERE
# Set up MongoDB connection
client = MongoClient(os.getenv("MONGODB_URI"))
db = client['todo']
tasks_collection = db['tasks']
users_collection = db['users']  



# Merge Sort to sort tasks by priority 
def merge_sort(tasks):
    if len(tasks) > 1:
        mid = len(tasks) // 2
        left = tasks[:mid]
        right = tasks[mid:]

        merge_sort(left)
        merge_sort(right)

        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i]['priority'] < right[j]['priority']:
                tasks[k] = left[i]
                i += 1
            else:
                tasks[k] = right[j]
                j += 1
            k += 1

        while i < len(left):
            tasks[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            tasks[k] = right[j]
            j += 1
            k += 1

# Binary Search to find a task by name 
def binary_search(tasks, task_name):
    low = 0
    high = len(tasks) - 1

    while low <= high:
        mid = (low + high) // 2
        if tasks[mid]['name'] == task_name:
            return mid
        elif tasks[mid]['name'] < task_name:
            low = mid + 1
        else:
            high = mid - 1
    return -1

@app.route('/index')
def index():
    if 'username' in session:  # Check if user is logged in
        tasks = list(tasks_collection.find())
        merge_sort(tasks)  # Sort tasks by priority using merge sort
        print("Tasks:", tasks)  # Print tasks to check if they're retrieved
        return render_template('index.html', tasks=tasks)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')  # Encode password

        # Find user in MongoDB
        user = users_collection.find_one({'username': username})

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):  # Check hashed password
            session['username'] = username  # Set session variable
            return redirect(url_for('index'))  # Redirect to index after login
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')  # Render login page


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))  # Redirect to login page after logout


@app.route('/add', methods=['POST'])
def add_task():
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')  # Capture description
    task_priority = int(request.form.get('task_priority'))
    task_deadline = request.form.get('task_deadline')

    new_task = {
        'name': task_name,
        'description': task_description,  # Store description in the task
        'priority': task_priority,
        'deadline': datetime.datetime.strptime(task_deadline, '%Y-%m-%d'),
        'date_created': datetime.datetime.utcnow()
    }
    
    tasks_collection.insert_one(new_task)
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete_task(task_id):
    tasks_collection.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('index'))

@app.route('/delete_all')
def delete_all_tasks():
    tasks_collection.delete_many({})  
    return redirect(url_for('index'))

@app.route('/edit/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = tasks_collection.find_one({'_id': ObjectId(task_id)})

    if request.method == 'POST':
        updated_name = request.form.get('task_name')
        updated_description = request.form.get('task_description')  
        updated_priority = int(request.form.get('task_priority'))
        updated_deadline = request.form.get('task_deadline')

        tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'name': updated_name,
                'description': updated_description, 
                'priority': updated_priority,
                'deadline': datetime.datetime.strptime(updated_deadline, '%Y-%m-%d')
            }}
        )
        return redirect(url_for('index'))

    return render_template('edit.html', task=task)

@app.route('/search', methods=['POST'])
def search_task():
    task_name = request.form.get('task_name').lower()  # Convert to lowercase for case-insensitive matching
    tasks = list(tasks_collection.find())

    # Filter tasks to find those that contain the search term in their name
    matching_tasks = [task for task in tasks if task_name in task['name'].lower()]

    return render_template('search_result.html', tasks=matching_tasks)  # Pass all matching tasks


if __name__ == '__main__':
    app.run(debug=True)
