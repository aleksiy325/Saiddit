from saiddit import app, mysql, login_manager
from flask import render_template, request, flash, redirect, url_for
from flask_login import UserMixin, login_user, logout_user, user_logged_in, current_user
from werkzeug.routing import BaseConverter
import hashlib

class RegexConverter(BaseConverter):
        def __init__(self, url_map, *items):
                super(RegexConverter, self).__init__(url_map)
                self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

class User(UserMixin):
    def __init__(self, user_id):
        userdata = get_user_data(user_id)
        self.id = user_id
        self.username = userdata[1]
        self.reputation = userdata[2]
        self.friends = get_user_friends(user_id)
        self.subs = get_user_subs(user_id)
        self.posts =  get_user_posts(user_id)
        self.favorites = get_user_favorites(user_id)

    def get_id(self):
        return self.id

    def reload(self):
        userdata = get_user_data(self.id)
        self.username = userdata[1]
        self.reputation = userdata[2]
        self.friends = get_user_friends(self.id)
        self.subs = get_user_subs(self.id)
        self.posts =  get_user_posts(self.id)
        self.favorites = get_user_favorites(self.id)


@app.route('/')
@app.route('/front')
def front():
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
        posts = get_user_front_posts(current_user.id)
    else:
        defaults = getdefaults(-1)
        posts = get_all_defaults()

    return render_template('saiddit/frontpage.html',
                           title='frontpage', defaults=defaults, posts=posts)

@app.route('/frndpost')
def friendposts():
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
        posts = get_user_friend_posts(current_user.id)
    else:
        return redirect(url_for('login'))

    return render_template('saiddit/frontpage.html',
                           title='frontpage', defaults=defaults, posts=posts)

@app.route('/frndfavs')
def friendfavs():
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
        posts = get_user_friend_favs(current_user.id)
    else:
        return redirect(url_for('login'))

    return render_template('saiddit/frontpage.html',
                           title='frontpage', defaults=defaults, posts=posts)

@app.route('/frndsubs')
def friendsubs():
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
        subs = get_friends_subs(current_user.id)
    else:
        return redirect(url_for('login'))

    return render_template('saiddit/subs.html',
                           title='myposts', subs=subs, defaults=defaults )




@app.route('/login', methods = ['GET', 'POST'])
def login():
    invalid_pass = False
    invalid_user = False

    if request.method == 'POST':

        username=request.form['username']
        password=request.form['password']

        
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * from Accounts where username='" + username + "'")
        userdata = cursor.fetchone()
        

        if userdata:
            #username found
            hashed = hashlib.sha256(password + userdata[3]).hexdigest() # hash

            if hashed == userdata[2]:
                #login user
                user = load_user(userdata[0])
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
    posts = []
    if current_user.is_authenticated:
         posts = current_user.posts
         defaults = getdefaults(current_user.id)
    else:
        return redirect(url_for('login'))


    return render_template('saiddit/myposts.html',
                           title='myposts', posts=posts, defaults=defaults )


@app.route("/u/<regex('.*'):name>/")
def userpage(name):
    user_id = get_id(name)
    user = load_user(user_id)
    defaults = []
    favorites = get_user_favorites(user_id)
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
    else:
        defaults = getdefaults(-1)

    return render_template('saiddit/userpage.html',
                           title='myposts', posts=user.posts, defaults=defaults, user=user )

@app.route("/s/<regex('.*'):sub>" , methods = ['GET', 'POST'])
def subpage(sub):
    if request.method == 'POST':
        posts = search_sub_posts(sub, request.form['search'])
    else:
        posts = get_subs_posts(sub)
    defaults = []
    if current_user.is_authenticated:
        defaults = getdefaults(current_user.id)
    else:
        defaults = getdefaults(-1)
    return render_template('saiddit/subsaiddit.html',
                           title='myposts', posts=posts, defaults=defaults, sub=sub)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def getdefaults(user_id):
    defaults = []
    if user_id != -1:
        defaults = get_user_subs(user_id)

    else:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CSC370.Subsaiddits WHERE is_default = 1 LIMIT 20;")
        defaults += cursor.fetchall()

    return defaults


def get_all_defaults():
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select   COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id  FROM Posts
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        JOIN Subsaiddits ON Posts.subsaiddit_id = Subsaiddits.id
                        LEFT JOIN
                        (Select   COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    return posts

def get_user_front_posts(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select DISTINCT  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0) , Posts.id  FROM Subscriptions
                            JOIN Subsaiddits ON Subscriptions.subsaiddit_id = Subsaiddits.id
                            JOIN Posts ON Subsaiddits.id = Posts.subsaiddit_id
                            JOIN Accounts on Posts.poster_id = Accounts.id
                            LEFT JOIN
                            (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                    GROUP BY VotesOnPosts.post_id )  VT
                                ON VT.post_id = Posts.id
                            LEFT JOIN
                                (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                    GROUP BY Comments.post_id )  CT
                                ON CT.post_id = Posts.id
                            WHERE (Subscriptions.account_id = """ + str(user_id) + """ OR Subsaiddits.is_default = 1 )
                            ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    
    return posts

def get_user_friend_posts(user_id):
    
    cursor = mysql.get_db().cursor()
    cursor.execute(""" Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id FROM Friends
                        JOIN Posts ON Friends.buddy_id = Posts.poster_id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        JOIN Subsaiddits on Posts.subsaiddit_id = Subsaiddits.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        WHERE Friends.self_id = """ + str(user_id) + """
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    
    return posts


def get_user_friend_favs(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute(""" Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id FROM Friends
						JOIN FavoritePosts ON Friends.buddy_id = FavoritePosts.account_id
                        JOIN Posts ON FavoritePosts.post_id = Posts.id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        JOIN Subsaiddits on Posts.subsaiddit_id = Subsaiddits.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        WHERE Friends.self_id =  """ + str(user_id) + """
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    return posts



def get_user_favorites(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute(""" Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0) , Posts.id  FROM FavoritePosts
                        Join Posts ON FavoritePosts.post_id = Posts.id
                        JOIN Subsaiddits ON Posts.subsaiddit_id = Subsaiddits.id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        WHERE FavoritePosts.account_id = """ + str(user_id) + """
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    
    return posts


def get_user_posts(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute(""" Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id   FROM Posts
                        JOIN Subsaiddits ON Posts.subsaiddit_id = Subsaiddits.id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                          WHERE Posts.poster_id = """ + str(user_id) + """
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    return posts


def get_subs_posts(sub_name):
    cursor = mysql.get_db().cursor()
    cursor.execute("""  Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id   FROM Subsaiddits
                        JOIN Posts ON Subsaiddits.id =  Posts.subsaiddit_id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        WHERE Subsaiddits.title ='""" + sub_name + """'
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()
    return posts

def search_sub_posts(sub_name, term):
    cursor = mysql.get_db().cursor()
    cursor.execute("""  Select  COALESCE(VT.votes,0), Posts.title, Accounts.username, Posts.date_posted, Subsaiddits.title, Posts.url, COALESCE(CT.comments, 0), Posts.id   FROM Subsaiddits
                        JOIN Posts ON Subsaiddits.id =  Posts.subsaiddit_id
                        JOIN Accounts on Posts.poster_id = Accounts.id
                        LEFT JOIN
                        (Select COALESCE(SUM(VotesOnPosts.vote_type), 0) as votes, VotesOnPosts.post_id FROM VotesOnPosts
                                GROUP BY VotesOnPosts.post_id )  VT
                            ON VT.post_id = Posts.id
                        LEFT JOIN
                            (Select COALESCE(Count(Comments.id), 0) as comments, Comments.post_id FROM Comments
                                GROUP BY Comments.post_id )  CT
                            ON CT.post_id = Posts.id
                        WHERE Subsaiddits.title ='""" + sub_name + """' and  Posts.title LIKE '""" + term + """%' or Posts.content_text LIKE '""" + term + """%'
                        ORDER BY   COALESCE(VT.votes,0) DESC;""")
    posts = cursor.fetchall()

    return posts


def get_user_data(user_id):
    
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select Accounts.id, Accounts.username, COALESCE(SUM(VotesOnPosts.vote_type), 0) From Accounts
                        LEFT JOIN Posts ON Accounts.id = Posts.poster_id
                        LEFT JOIN VotesOnPosts ON VotesOnPosts.post_id = Posts.id
                        WHERE Accounts.id = """ + str(user_id) + """ GROUP BY Accounts.id""")
    userdata = cursor.fetchone()

    return userdata



def get_user_subs(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select Subsaiddits.id, Subsaiddits.title From Accounts
                        JOIN Subscriptions ON Subscriptions.account_id = Accounts.id
                        JOIN Subsaiddits ON Subsaiddits.id = Subscriptions.subsaiddit_id
                        WHERE Accounts.id =""" + str(user_id) + """
                        UNION
                        SELECT Subsaiddits.id, Subsaiddits.title  FROM CSC370.Subsaiddits WHERE is_default = 1 LIMIT 20; """)
    subs = cursor.fetchall()
    return subs

def get_friends_subs(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select DISTINCT Subsaiddits.id, Subsaiddits.title From Friends
                        JOIN Subscriptions ON Subscriptions.account_id = Friends.buddy_id
                        JOIN Subsaiddits ON Subsaiddits.id = Subscriptions.subsaiddit_id
                        WHERE Friends.self_id = """ + str(user_id))
    subs = cursor.fetchall()
    return subs

def get_user_friends(user_id):
    cursor = mysql.get_db().cursor()
    cursor.execute("""Select  Accounts.username, COALESCE(SUM(VotesOnPosts.vote_type), 0) From Friends
                        JOIN Accounts ON Friends.buddy_id = Accounts.id
                        LEFT JOIN Posts ON Friends.buddy_id = Posts.poster_id
                        LEFT JOIN VotesOnPosts ON VotesOnPosts.post_id = Posts.id
                        WHERE Friends.self_id =""" + str(user_id) + " GROUP BY Friends.buddy_id")
    friends = cursor.fetchall()
    
    return friends



def remove_post(post_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM CSC370.Posts WHERE Posts.id=" + str(post_id) + ";")
    conn.commit()


def get_id(name):
    
    cursor = mysql.get_db().cursor()
    cursor.execute("SELECT Accounts.id FROM Accounts WHERE Accounts.username = '" + name +"';" )
    id = cursor.fetchone()
    
    return id[0]