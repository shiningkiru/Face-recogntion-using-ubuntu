import face_recognition
from os import  path
class Face:
    def __init__(self, app):
        self.storage = app.config['storage']
        self.db = app.db
        self.faces =[]
        self.known_encoding_faces = []
        self.face_user_keys = {}
        self.loadAll()

    def load_train_file_by_name(self, name):
        trained_storage = path.join(self.storage, 'trained')
        return path.join(trained_storage,name)


    def load_unknown_file_by_name(self, filename):
        unknown_storage = path.join(self.storage, 'unknown')
        return path.join(unknown_storage,filename)

    def load_user_by_index_key(self, index_key = 0):
        key_str = str(index_key)

        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]

        return None


    def loadAll(self):
        results = self.db.query('SELECT faces.id, faces.filename, faces.user_id FROM faces')

        for row in results:
            user_id=row[2]
            filename = row[1]
            face = {
                "id" : row[0],
                "filename" : filename,
                'user_id' : user_id
            }
            self.faces.append(face)

            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] =user_id

    def recognize(self,filename):
        unknown_image = face_recognition.load_image_file(self.load_unknown_file_by_name(filename))
        unknown_encoding_image = face_recognition.face_encodings(unknown_image)[0]
        result = face_recognition.compare_faces(self.known_encoding_faces, unknown_encoding_image)
        print(result)
        index_key = 0
        for matched in result:
            if matched:
                user_id = self.load_user_by_index_key(index_key)
                return user_id
            index_key = index_key + 1
        return None