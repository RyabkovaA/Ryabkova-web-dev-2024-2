from flask_login import current_user

class UsersPolicy:
    def __init__(self, user=None):
        self.user = user

    def create(self):
        return current_user.is_admin()

    def edit(self):
        return self.user.id == int(current_user.id) or current_user.is_admin()

    def delete(self):
        return current_user.is_admin()      

    def show(self):
        return True 
    
    def assign_roles(self):
        return current_user.is_admin()    

    def check_journal(self): 
        return current_user.is_admin()    



