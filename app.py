from flask import Flask,json,Response,request, render_template
from werkzeug.utils import secure_filename
from os import path, getcwd
import time;
from db import Database
from face import Face

app=Flask(__name__)
app.config['file_allowed'] = ['image/jpeg', 'image/png']
app.config['storage'] = path.join(getcwd(), 'storage')
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
            "filename": row[4],
            "created": row[5],
        }
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
    print(users)
    return render_template('index.html', users = users)



@app.route('/api/train', methods=['POST'])
def train():
    if 'file' not in request.files:
        return error_handle("image is required")
    else:
        file=request.files['file']
        if file.mimetype not in app.config['file_allowed']:
            return error_handle('File type not supported')
        else:
            print(request.form['name'])
            filename=secure_filename(file.filename)
            trained=path.join(app.config['storage'], 'trained')
            file.save(path.join(trained,filename))

            #save it to database sqllite
            created= int(time.time())
            user_id = app.db.insert('INSERT  INTO users(name, created) VALUES(?,?)',[request.form['name'],created])
            if user_id:
                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(?,?,?)',[user_id, filename, created])
                print(face_id)
    output = json.dumps({'success': 'true'})
    return success_handle(output)


#route for user profile
@app.route('/api/profile/<int:user_id>')
def user_profile(user_id):
    return success_handle(json.dumps(get_user(user_id)));


#route for user profile delete
@app.route('/api/delete-user/<int:user_id>')
def user_delete(user_id):
    delete_user(user_id)
    return success_handle(json.dumps({'success': {'delete':"true"} }));

#route for recognize unknown image
@app.route('/api/recognize', methods=['POST'])
def recognize():
    if "file" not in request.files:
        return error_handle("Image required")
    else:
        file=request.files['file']
        filename=secure_filename(file.filename)
        unknown_path=path.join(app.config['storage'],'unknown')
        file.save(path.join(unknown_path,filename))
        result = app.face.recognize(filename)
        if result:
            return success_handle(json.dumps({"found": get_user(result)}))
        else:
            return error_handle("We cant able to find any user")


app.run()