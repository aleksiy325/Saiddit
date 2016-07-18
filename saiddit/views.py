from saiddit import app, mysql, login_manager
from flask import render_template, request, flash, redirect, url_for
from flask_login import UserMixin, login_user, logout_user, user_logged_in, current_user
import hashlib


class User(UserMixin):
    def __init__(self, id, username, friends, subs, posts):
        self.id = id
        self.username = username
        self.friends = friends
        self.subs = subs
        self.posts = posts
    def get_id(self):
        return self.id

    def reload(self):
        user = load_user(self.id)
        self.friends = user.friends
        self.subs = user.subs
        self.posts = user.posts

@app.route('/')
@app.route('/front')
def front():
    defaults = getdefaults()
    posts = getallposts()
    return render_template('saiddit/frontpage.html',
                           title='frontpage', defaults=defaults, posts=posts)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    invalid_pass = False
    invalid_user = False

    if request.method == 'POST':

        username=request.form['username']
        password=request.form['password']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * from Accounts where username='" + username + "'")
        userdata = cursor.fetchone()
        conn.close()

        if userdata:
            #username found
            hashed = hashlib.sha256(password + userdata[3]).hexdigest() # hash
            print hashed

            if hashed == userdata[2]:
                #login user
                user = User(userdata[0], userdata[1], None, None, None)
                login_user(user)

                return redirect(url_for('front'))

            else:
                invalid_pass = True


        else:
            invalid_user = True

    return render_template('saiddit/login.html',
                           title='login', invalid_pass=invalid_pass,  invalid_user=invalid_user )

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('front'))

@app.route('/myposts' , methods = ['GET', 'POST'])
def myposts():
    if request.method == 'POST':
        i =  int(request.form['btn']) - 1
        postid = current_user.posts[i][7]
        remove_post(postid)
        current_user.reload()


    defaults = getdefaults()
    posts = []
    if current_user.is_authenticated:
          posts = current_user.posts
    else:
        return redirect(url_for('login'))


    return render_template('saiddit/myposts.html',
                           title='myposts', posts=posts, defaults=defaults )

def getdefaults():
    defaults = []
    if current_user.is_authenticated:
        defaults += current_user.subs

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM CSC370.Subsaiddits WHERE is_default = 1 LIMIT 20;")
    defaults += cursor.fetchall()
    conn.close()
    return defaults


def getallposts():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("""SELECT COALESCE(SUM(VotesOnPosts.vote_type), 0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COUNT(Comments.id), Posts.id
                        FROM Posts
                        LEFT JOIN Comments ON Posts.id = Comments.post_id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        JOIN Subsaiddits ON Posts.subsaiddit_id = Subsaiddits.id
                        LEFT JOIN VotesOnPosts ON Posts.id = VotesOnPosts.post_id
                        GROUP BY Posts.id
                        ORDER BY SUM(VotesOnPosts.vote_type) DESC; """)
    posts = cursor.fetchall()
    conn.close()
    return posts


@login_manager.user_loader
def load_user(user_id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Accounts where id='" + str(user_id) + "'")
    userdata = cursor.fetchone()
    cursor.execute("""Select FriendsAccount.username  From Accounts
                            JOIN Friends ON Friends.self_id = Accounts.id
                            JOIN Accounts AS FriendsAccount ON FriendsAccount.id = Friends.buddy_id
                            WHERE Accounts.id =""" + str(user_id) + ";")
    friends = cursor.fetchall()
    cursor.execute("""Select Subsaiddits.id, Subsaiddits.title From Accounts
                        JOIN Subscriptions ON Subscriptions.account_id = Accounts.id
                        JOIN Subsaiddits ON Subsaiddits.id = Subscriptions.subsaiddit_id
                        WHERE Accounts.id =""" + str(user_id) + ";")
    subs = cursor.fetchall()
    cursor.execute(""" SELECT COALESCE(SUM(VotesOnPosts.vote_type), 0), Posts.title, Posts.title, Posts.date_posted, Subsaiddits.title, Posts.url, COUNT(Comments.id), Posts.id
                            FROM Posts
                            LEFT JOIN Comments ON Posts.id = Comments.post_id
                            JOIN Subsaiddits ON Posts.subsaiddit_id = Subsaiddits.id
                            LEFT JOIN VotesOnPosts ON Posts.id = VotesOnPosts.post_id
                            WHERE Posts.poster_id = 4
                            GROUP BY Posts.id
                            ORDER BY Posts.date_posted DESC;""")
    posts = cursor.fetchall()
    conn.close()
    return User(userdata[0], userdata[1], friends, subs, posts)




def remove_post(post_id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM CSC370.Posts WHERE Posts.id=" + str(post_id) + ";")
    conn.commit()
    conn.close()
