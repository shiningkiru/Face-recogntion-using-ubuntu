from flask import Flask,json,Response,request, render_template, redirect
from werkzeug.utils import secure_filename
from os import path, getcwd
import time;
from db import Database
from face import Face

app=Flask(__name__)
app.config['file_allowed'] = ['image/jpeg', 'image/png']
static = path.join(getcwd(), 'static')
app.config['storage'] = path.join(static, 'storage')
app.db = Database()
app.face = Face(app)

def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)

def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({'error': {'message': error_message}}), status=status, mimetype=mimetype)

def get_user(user_id):
    user={}
    result = app.db.query('SELECT * FROM users LEFT JOIN faces ON faces.user_id = users.id where users.id = ?',[user_id])
    index=0
    for row in result:
        face = {
            "id": row[3],
            "filename": row[5],
            "created": row[6],
        }
        print(row)
        if index == 0:
            user={
                "id": row[0],
                "name": row[1],
                "created": row[2],
                "faces":[]
            }
        if row[3]:
            user['faces'].append(face)
        index+=1
    return user

def delete_user(user_id: int):
    app.db.just_execute('DELETE FROM users WHERE users.id = ?',[user_id])
    app.db.just_execute('DELETE FROM faces WHERE faces.user_id = ?',[user_id])
    print("deleted")


@app.route('/', methods=['GET'])
def homepage():
    users = app.db.query('SELECT * FROM users')
    return render_template('index.html', users = users)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = get_user(user_id)
    file_path = path.join(app.config['storage'], 'trained')
    return render_template('profile.html', user = user, file_path = file_path)


@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@app.route('/reg-submit', methods=['POST'])
def reagister_submit():
    user_name = request.form['username']

    #save it to database sqllite
    created= int(time.time())
    user_id = app.db.insert('INSERT  INTO users(name, created) VALUES(?,?)',[user_name,created])
    if user_id:
        #print('/profile/'+ str(user_id))
        return redirect('/profile/'+ str(user_id))
    return redirect('/')


@app.route('/recognize', methods=['GET'])
def recognize():
    return render_template('recognize.html')


@app.route('/train-process', methods=['GET'])
def train_images_process():
    app.face.loadAll();
    return redirect('/recognize')


@app.route('/delete/<int:user_id>')
def delete(user_id):
    delete_user(user_id)
    return redirect("/")



@app.route('/api/register', methods=['POST'])
def reagister_api():
    user_name = request.form['name']

    #save it to database sqllite
    created= int(time.time())
    user_id = app.db.insert('INSERT  INTO users(name, created) VALUES(?,?)',[request.form['name'],created])
    if user_id:
        output = json.dumps({'success': 'true', 'user_id': user_id})
        return success_handle(output)
    return error_handle("Cant able to register")



@app.route('/api/train', methods=['POST'])
def train():
    if 'file' not in request.files:
        return error_handle("image is required")
    else:
        file=request.files['file']
        if file.mimetype not in app.config['file_allowed']:
            return error_handle('File type not supported')
        else:
            filename=secure_filename(file.filename)
            trained=path.join(app.config['storage'], 'trained')
            file.save(path.join(trained,filename))
            user_id = request.form['user_id']
            #save it to database sqllite
            if user_id:
                created= int(time.time())
                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(?,?,?)',[user_id, filename, created])
                output = json.dumps({'success': 'true', 'face': face_id})
                return success_handle(output)
            else:
                return error_handle("User ID required")

#route for user profile
@app.route('/api/profile/<int:user_id>')
def user_profile(user_id):
    return success_handle(json.dumps(get_user(user_id)));


#route for user profile delete
@app.route('/api/delete-user/<int:user_id>')
def user_delete(user_id):
    delete_user(user_id)
    return success_handle(json.dumps({'success': {'delete':"true"} }));


#route for user profile delete
@app.route('/api/delete-face/<int:face_id>')
def user_delete_face(face_id):
    app.db.just_execute('DELETE FROM faces WHERE faces.id = ?',[face_id])
    return success_handle(json.dumps({'success': {'delete':"true"} }));

#route for recognize unknown image
@app.route('/api/recognize', methods=['POST'])
def recognize_api():
    if "file" not in request.files:
        return error_handle("Image required")
    else:
        file=request.files['file']
        filename=secure_filename(file.filename)
        unknown_path=path.join(app.config['storage'],'unknown')
        file.save(path.join(unknown_path,filename))
        result = app.face.recognize(filename)
        if result:
            user = get_user(result)
            if user == {}:
                return error_handle("Cant able to find")
            return success_handle(json.dumps({"found": user}))
        else:
            return error_handle("We cant able to find any user")


app.run()