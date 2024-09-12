# Import necessary modules and packages from Flask and other libraries.
from flask import (
    Flask,
    render_template,
    url_for,
    session,
    flash,
    redirect,
    request,
    jsonify,
)
import os
import hashlib
from flaskext.mysql import MySQL  # Flask extension for MySQL integration.
import random
from dotenv import load_dotenv  # Import dotenv to load environment variables
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app.
app = Flask(__name__)

# Secret key configuration for session management. It's imported from a secure source (credentials).
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Initialize MySQL configuration using Flask extension.
mysql = MySQL()
app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USERNAME")
app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("DB_PASSWORD")
app.config["MYSQL_DATABASE_DB"] = "pythonista"
app.config["MYSQL_DATABASE_HOST"] = "antoniskarnavas.mysql.pythonanywhere-services.com"
mysql.init_app(app)


# This function is executed before each request to make the session permanent, with a custom timeout.
@app.before_request
def make_session_permanent():
    """Sets session to be permanent and configures the lifetime to 10 minutes."""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)


# Error handling for 404 (page not found) errors.
@app.errorhandler(404)
def not_found(e):
    """Renders a custom error page when a 404 error occurs."""
    return render_template("error.html"), 404  # Explicitly return the 404 status code.


# Routes for the home page.
@app.route("/index")
@app.route("/")
@app.route("/home")
def home():
    """Renders the home (index) page."""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login with both GET and POST methods."""

    # Handle GET request - serve the login page or redirect if already logged in.
    if request.method == "GET":
        if "username" in session:
            flash("You are already logged in!", "info")
            return redirect(url_for("home"))
        else:
            return render_template("login.html")

    # Handle POST request - process login form submission.
    else:
        # Retrieve form data
        email = request.form["email"]
        password = request.form["password"]

        # Connect to the database
        try:
            connection = mysql.connect()
            cursor = connection.cursor()

            # Use a parameterized query to prevent SQL injection
            query = "SELECT email, password, salt, username, age, user_id, teacher FROM users_info WHERE email = %s"
            cursor.execute(query, (email,))
            records = cursor.fetchall()

            # Ensure connection is closed properly
        finally:
            connection.close()

        # Check if any user exists with the given email
        if len(records) == 0:
            return jsonify({"error": "An account with that email does not exist!"})

        # Iterate through fetched records (though usually should be just one if emails are unique)
        for row in records:
            # Generate hash from the entered password using the stored salt
            salt = row[2]  # Assuming salt is stored securely
            hex_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, 10000
            ).hex()

            # Check if the hashed password matches the stored hash
            if hex_hash == row[1]:
                # Clear any previous session data to prevent session fixation attacks
                session.clear()

                # Set session data for the logged-in user
                session["username"] = row[3]
                session["age"] = row[4]
                session["id"] = row[5]

                # Check if the user is a teacher and return the appropriate response
                if row[6] == 1:
                    session["teacher"] = True
                    return jsonify(
                        {"success": f"Welcome back {row[3]}!", "teacher": "true"}
                    )
                else:
                    return jsonify({"success": f"Welcome back {row[3]}!"})

        # If password does not match, return an error
        return jsonify({"error": "The given password is incorrect. Please try again!"})


@app.route("/signup", methods=["POST"])
def signup():
    """Handle user sign up with form data validation and secure password storage."""

    # Retrieve form data from the signup form
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    age = request.form["age"]

    # Check if the email or username already exists
    try:
        connection = mysql.connect()
        cursor = connection.cursor()

        # Use parameterized queries to check if the username or email is already taken
        cursor.execute(
            "SELECT username, email FROM users_info WHERE username = %s OR email = %s",
            (username, email),
        )
        records = cursor.fetchall()

        # Check if the username or email is already registered
        for row in records:
            if username == row[0]:
                return jsonify(
                    {"info": "Username already exists, please try logging in!"}
                )
            elif email == row[1]:
                return jsonify({"info": "Email already exists, please try logging in!"})

        # If the username/email are unique, create a new user
        # Generate a random salt and hash the password securely
        salt = os.urandom(32)
        hex_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 10000).hex()

        # Insert new user details into the database with a parameterized query
        cursor.execute(
            "INSERT INTO users_info (username, email, password, salt, age) VALUES (%s, %s, %s, %s, %s)",
            (username, email, hex_hash, salt, age),
        )
        connection.commit()

        # Retrieve the user_id of the newly inserted user
        cursor.execute(
            "SELECT user_id FROM users_info WHERE username = %s", (username,)
        )
        user_id = cursor.fetchone()[0]  # Assuming username is unique, fetch one record

    except Exception as e:
        # Log the error in production for better debugging
        print(f"Error during signup: {e}")
        return (
            jsonify(
                {"error": "An error occurred during sign-up. Please try again later."}
            ),
            500,
        )

    finally:
        # Ensure the connection is closed
        connection.close()

    # Clear any existing session and set the session for the new user
    session.clear()
    session["id"] = user_id
    session["username"] = username
    session["age"] = age

    # Return a success message to the user
    return jsonify({"success": f"Welcome {username}!"})


@app.route("/chapters", methods=["GET", "POST"])
def chapters():
    """
    Handle displaying and updating user progress on chapters.
    GET: Display chapters/tests based on the user's progress.
    POST: Update user's progress when they complete a chapter.
    """

    # Handle GET requests
    if request.method == "GET":
        # Ensure user is logged in and not a teacher
        if "username" in session and "teacher" not in session:
            try:
                # Fetch user-specific data from the database
                connection = mysql.connect()
                cursor = connection.cursor()

                # Check if user has a level assigned
                cursor.execute(
                    "SELECT * FROM levels WHERE user_id=%s", (session["id"],)
                )
                result = cursor.fetchall()

                if len(result) == 0:
                    flash(
                        "Wanna take a test to determine your level and possibly skip a couple of chapters? "
                        "If you score 0% to 39% you will be assigned as a beginner. If you score 40% to 69%, "
                        "you will be assigned as an intermediate. If you score 70% to 100%, you will be assigned as an expert.",
                        "info",
                    )
                    return render_template("chapters.html")

                # Fetch completed chapters and tests for the user
                cursor.execute(
                    "SELECT chapter_name FROM chapters_users_info WHERE user_id=%s",
                    (session["id"],),
                )
                chapters = cursor.fetchall()

                cursor.execute(
                    "SELECT tests.test_name, score FROM tests "
                    "INNER JOIN tests_users_info ON tests.test_name=tests_users_info.test_name "
                    "WHERE user_id=%s AND score > 50 ORDER BY tests.id",
                    (session["id"],),
                )
                tests = cursor.fetchall()

                # Fetch all available chapters and tests
                cursor.execute("SELECT chapter_name FROM chapters ORDER BY id")
                all_chapters = cursor.fetchall()

                cursor.execute("SELECT test_name FROM tests ORDER BY id")
                all_tests = cursor.fetchall()

            finally:
                # Ensure the connection is closed
                connection.close()

            # Format data for display
            completed_chapters = [row[0] for row in chapters]
            completed_tests = [row[0] for row in tests]
            all_chapters_formatted = [row[0] for row in all_chapters]
            all_tests_formatted = [row[0] for row in all_tests]

            # Render the chapters template with user progress
            return render_template(
                "chapters.html",
                chapters=completed_chapters,
                tests=completed_tests,
                all_chapters=all_chapters_formatted,
                all_tests=all_tests_formatted,
            )
        else:
            # Redirect to login if user is not logged in or is a teacher
            flash(
                "You need to log in or create an account to access our learning materials!",
                "info",
            )
            return redirect(url_for("login"))

    # Handle POST requests
    else:
        if "username" in session and "teacher" not in session:
            curr_chapter = request.form["chapter"]

            try:
                connection = mysql.connect()
                cursor = connection.cursor()

                # Fetch the completed chapters for the user
                cursor.execute(
                    "SELECT id FROM chapters_users_info "
                    "INNER JOIN chapters ON chapters_users_info.chapter_name = chapters.chapter_name "
                    "WHERE user_id = %s ORDER BY id",
                    (session["id"],),
                )
                chapters = cursor.fetchall()

                # Fetch the current chapter ID
                cursor.execute(
                    "SELECT id FROM chapters WHERE chapter_name = %s", (curr_chapter,)
                )
                curr_chapter_id = cursor.fetchone()

                if not curr_chapter_id:
                    return jsonify({"error": "Invalid chapter name."})

                curr_chapter_id = curr_chapter_id[0]

                # Check if the user has completed previous chapters in order
                valid = all(chapters[i][0] == i + 1 for i in range(len(chapters)))
                if len(chapters) + 1 != curr_chapter_id:
                    valid = False

                if valid:
                    # Insert the new chapter into the user's completed list
                    cursor.execute(
                        "INSERT INTO chapters_users_info (user_id, chapter_name) VALUES (%s, %s)",
                        (session["id"], curr_chapter),
                    )
                    connection.commit()
                    return jsonify({"success": "completed"})
                else:
                    return jsonify(
                        {
                            "error": "You must complete all previous chapters before accessing this one."
                        }
                    )

            finally:
                # Ensure the connection is closed
                connection.close()
        else:
            return jsonify({"error": "Unauthorized request."})


@app.route("/tests", methods=["GET", "POST"])
def tests():
    """
    Handle test selection and rendering based on user session and progress.
    GET: Display the selected test if available and user has access.
    POST: Render the test template when the user is logged in.
    """

    # Handle POST requests (rendering the test template)
    if request.method == "POST":
        if "username" in session:
            return render_template("test.html")
        else:
            flash("You need to log in to take a test.", "info")
            return redirect(url_for("login"))

    # Handle GET requests (test selection and validation)
    else:
        if "username" in session and "teacher" not in session:
            curr_test = request.args.get("test")

            # Ensure the user selects a test from the chapters
            if curr_test is None:
                flash("Please select a test from the chapters.", "info")
                return redirect(url_for("chapters"))

            # Special case for level test
            elif curr_test == "levels":
                try:
                    with mysql.connect() as connection:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "SELECT question_type, question, multiple1, multiple2, multiple3, multiple4, chapter_name, subchapter, test_id "
                                "FROM level_test"
                            )
                            questions = cursor.fetchall()
                except Exception as e:
                    flash(
                        "An error occurred while fetching the test questions.", "error"
                    )
                    return redirect(url_for("chapters"))

                return render_template("test.html", questions=questions)

            # Handle chapter-specific tests
            else:
                try:
                    with mysql.connect() as connection:
                        with connection.cursor() as cursor:
                            # Fetch the user's completed tests
                            cursor.execute(
                                "SELECT id FROM tests_users_info "
                                "INNER JOIN tests ON tests_users_info.test_name = tests.test_name "
                                "WHERE user_id = %s ORDER BY id",
                                (session["id"],),
                            )
                            user_tests = cursor.fetchall()

                            # Get the current test's ID
                            cursor.execute(
                                "SELECT id FROM tests WHERE test_name = %s",
                                (curr_test,),
                            )
                            curr_test_id = cursor.fetchone()

                            if not curr_test_id:
                                flash("The selected test does not exist.", "error")
                                return redirect(url_for("chapters"))

                            # Check if the user is eligible to take the test
                            valid = all(
                                user_tests[i][0] == i + 1
                                for i in range(len(user_tests))
                            )
                            if len(user_tests) + 1 != curr_test_id[0]:
                                valid = False

                            if valid:
                                # Fetch the questions for the selected test
                                cursor.execute(
                                    "SELECT question_type, question, multiple1, multiple2, multiple3, multiple4, chapter_name, subchapter, test_id "
                                    "FROM tests_questions WHERE test_name = %s",
                                    (curr_test,),
                                )
                                questions = cursor.fetchall()

                                # Randomize the number of questions displayed based on test type
                                if curr_test.startswith(("C", "Q")):
                                    questions = random.sample(questions, 3)
                                else:
                                    questions = random.sample(questions, 6)

                                return render_template("test.html", questions=questions)

                            else:
                                flash(
                                    "You must complete the previous tests before accessing this one.",
                                    "error",
                                )
                                return redirect(url_for("chapters"))

                except Exception as e:
                    flash("An error occurred while processing your request.", "error")
                    return redirect(url_for("chapters"))

        # User is not logged in or is a teacher
        else:
            flash(
                "You need to log in or create an account to access the tests.", "info"
            )
            return redirect(url_for("login"))


@app.route("/profile", methods=["GET"])
def profile():
    """
    Display the user's profile with completed chapters, tests, and scores.
    The profile includes all chapters, completed chapters, completed tests,
    and the user's average test score if tests have been taken.
    """
    if "id" not in session:
        flash("You must be logged in to view your profile.", "info")
        return redirect(url_for("login"))

    try:
        with mysql.connect() as connection:
            with connection.cursor() as cursor:
                # Fetch the chapters the user has completed
                cursor.execute(
                    "SELECT chapters.chapter_name FROM chapters_users_info "
                    "LEFT OUTER JOIN chapters ON chapters_users_info.chapter_name = chapters.chapter_name "
                    "WHERE user_id = %s ORDER BY chapters.id",
                    (session["id"],),
                )
                completed_chapters = cursor.fetchall()

                # Fetch all available chapters and tests
                cursor.execute("SELECT chapter_name FROM chapters ORDER BY id")
                all_chapters = cursor.fetchall()

                cursor.execute("SELECT test_name FROM tests ORDER BY id")
                all_tests = cursor.fetchall()

                # Fetch the user's completed tests and their scores
                cursor.execute(
                    "SELECT tests.test_name, score FROM tests_users_info "
                    "LEFT OUTER JOIN tests ON tests_users_info.test_name = tests.test_name "
                    "WHERE user_id = %s ORDER BY tests.id",
                    (session["id"],),
                )
                completed_tests = cursor.fetchall()

        # Calculate the sum and average score
        total_score = (
            sum(int(test[1]) for test in completed_tests) if completed_tests else 0
        )
        average_score = total_score / len(completed_tests) if completed_tests else "-"

    except Exception as e:
        # Log the error and inform the user
        print(f"Error fetching profile data for user {session['id']}: {e}")
        flash("An error occurred while fetching your profile data.", "error")
        return redirect(url_for("home"))

    # Render the profile template with the user's data
    return render_template(
        "profile.html",
        chapters=completed_chapters,
        tests=completed_tests,
        all_chapters=all_chapters,
        all_tests=all_tests,
        average=average_score,
        sum=total_score,
    )


@app.route("/logout", methods=["GET"])
def logout():
    """
    Logs out the user by clearing the session and redirects to the home page with a goodbye message.
    """
    if "username" in session:
        flash(f"Hope to see you soon, {session['username']}!", "success")
    session.clear()  # Clear all session data
    return redirect(url_for("home"))


@app.route("/python", methods=["GET"])
def python():
    """
    Displays the Python info page. Redirects teachers to the admin page.
    """
    if "teacher" in session:
        return redirect(url_for("admin"))
    return render_template("python.html")


@app.route("/admin", methods=["GET"])
def admin():
    """
    Displays the admin dashboard for teachers. Redirects non-teachers to the login page.
    """
    if "username" in session and "teacher" in session:
        return render_template("admin.html")
    else:
        flash(
            "You must be logged in with a teacher account to access this page.", "error"
        )
        return redirect(url_for("login"))


@app.route("/questions", methods=["GET", "POST"])
def questions():
    """
    Handles both GET and POST requests for managing questions.
    GET: Displays the question form if the user is a teacher.
    POST: Submits a new question to the database and redirects to the question form.
    """
    if request.method == "GET":
        if "username" in session and "teacher" in session:
            try:
                with mysql.connect() as connection:
                    with connection.cursor() as cursor:
                        # Fetch available tests and chapters for the form
                        cursor.execute("SELECT test_name FROM tests ORDER BY id")
                        tests = cursor.fetchall()
                        cursor.execute("SELECT chapter_name FROM chapters ORDER BY id")
                        chapters = cursor.fetchall()
            except Exception as e:
                print(f"Error fetching data for /questions GET request: {e}")
                flash("An error occurred while fetching data.", "error")
                return redirect(url_for("home"))

            return render_template("questions.html", tests=tests, chapters=chapters)
        else:
            flash(
                "You need to log in with a teacher account to access this page!",
                "error",
            )
            return redirect(url_for("login"))

    if request.method == "POST":
        # Ensure all required fields are present
        required_fields = [
            "question",
            "test_name",
            "chapter_name",
            "subchapter",
            "type",
            "multiple1",
            "multiple2",
            "multiple3",
            "multiple4",
            "right_answer",
        ]
        if not all(field in request.form for field in required_fields):
            flash("All form fields are required.", "error")
            return redirect(url_for("questions"))

        # Extract data from the form
        question = request.form["question"]
        test_name = request.form["test_name"]
        chapter_name = request.form["chapter_name"]
        subchapter = request.form["subchapter"]
        question_type = request.form["type"]
        multiple1 = request.form["multiple1"]
        multiple2 = request.form["multiple2"]
        multiple3 = request.form["multiple3"]
        multiple4 = request.form["multiple4"]
        right_answer = request.form["right_answer"]

        try:
            with mysql.connect() as connection:
                with connection.cursor() as cursor:
                    # Insert the question into the database
                    cursor.execute(
                        "INSERT INTO tests_questions (question, test_name, chapter_name, subchapter, question_type, multiple1, multiple2, multiple3, multiple4, right_answer) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            question,
                            test_name,
                            chapter_name,
                            subchapter,
                            question_type,
                            multiple1,
                            multiple2,
                            multiple3,
                            multiple4,
                            right_answer,
                        ),
                    )
                    connection.commit()
        except Exception as e:
            print(f"Error submitting question: {e}")
            flash("An error occurred while submitting the question.", "error")
            return redirect(url_for("questions"))

        flash("Successfully submitted!", "success")
        return redirect(url_for("questions"))


@app.route("/students", methods=["GET"])
def students():
    """
    Displays a list of students with their scores, accessible only by teacher accounts.
    """
    if "username" in session and "teacher" in session:
        try:
            with mysql.connect() as connection:
                with connection.cursor() as cursor:
                    # Query to fetch student information and scores
                    query = """
                        SELECT username, email, GROUP_CONCAT(id) AS ids, GROUP_CONCAT(score) AS scores
                        FROM (
                            SELECT username, email, id, score
                            FROM (
                                SELECT username, email, test_name, score
                                FROM tests_users_info
                                RIGHT JOIN users_info ON users_info.user_id = tests_users_info.user_id
                                WHERE teacher IS NULL
                            ) AS T
                            LEFT JOIN tests ON tests.test_name = T.test_name
                            ORDER BY id
                        ) AS B
                        GROUP BY username
                    """
                    cursor.execute(query)
                    students = cursor.fetchall()

            # Process student scores to calculate averages
            students = [list(student) for student in students]
            for student in students:
                scores = student[3]
                if scores:
                    scores_list = list(map(int, scores.split(",")))
                    average_score = sum(scores_list) / len(scores_list)
                    student.append(average_score)
                else:
                    student.append("-")

            return render_template("students.html", students=students)
        except Exception as e:
            print(f"Error fetching students data: {e}")
            flash("An error occurred while fetching student data.", "error")
            return redirect(url_for("home"))

    else:
        flash("You need to log in with a teacher account to access this page!", "error")
        return redirect(url_for("login"))


@app.route("/rightanswer", methods=["POST"])
def rightanswer():
    """
    Checks the provided answer against the correct answer from the database and provides feedback.
    """
    if "username" in session and request.method == "POST":
        question_id = request.form.get("question")
        answer = request.form.get("answer")
        test_type = request.form.get("test")

        if not question_id or not answer or not test_type:
            return jsonify({"error": "Missing required fields."})

        try:
            with mysql.connect() as connection:
                with connection.cursor() as cursor:
                    if test_type == "levels":
                        query = """
                            SELECT right_answer, chapter_name, subchapter
                            FROM level_test
                            WHERE test_id = %s
                        """
                    else:
                        query = """
                            SELECT right_answer, chapter_name, subchapter
                            FROM tests_questions
                            WHERE test_id = %s
                        """
                    cursor.execute(query, (question_id,))
                    right_answer_data = cursor.fetchone()

            if right_answer_data:
                correct_answer, chapter_name, subchapter = right_answer_data
                normalized_correct_answer = correct_answer.strip().lower()
                normalized_user_answer = answer.strip().lower()

                if normalized_correct_answer == normalized_user_answer:
                    if chapter_name != subchapter:
                        message = f"Right answer, great job! This question was from chapter: {chapter_name} and sub-chapter: {subchapter}."
                    else:
                        message = f"Right answer, great job! This question was from chapter: {chapter_name}."
                    return jsonify({"success": message})
                else:
                    if chapter_name != subchapter:
                        message = f"Wrong answer! Please re-study the chapter: {chapter_name} and especially the sub-chapter: {subchapter}."
                    else:
                        message = f"Wrong answer! Please re-study the chapter: {chapter_name}."
                    return jsonify({"false": message})
            else:
                return jsonify({"error": "No question found with the provided ID."})

        except Exception as e:
            print(f"Error checking answer: {e}")
            return jsonify(
                {"error": "There was a bug with our servers, please try again later!"}
            )

    else:
        return jsonify({"error": "Unauthorized access."})


def format_test_name(test: str) -> str:
    """
    Formats the test name for display purposes.
    """
    return (
        test.replace("_", " ")
        .replace("Chapter", "Chapter ")
        .replace("Test_test", " test")
    )


def get_level_info(score: float):
    """
    Determines the user's level, chapters, and tests based on their score.
    Returns the level description, chapters list, and tests list.
    """
    if score < 40:
        return "beginner", [], []
    elif score < 70:
        return (
            "intermediate",
            ["Quickstart", "Chapter1", "Chapter2", "Chapter3", "BasicsTest"],
            [
                "Quickstart_test",
                "Chapter1_test",
                "Chapter2_test",
                "Chapter3_test",
                "BasicsTest_test",
            ],
        )
    else:
        return (
            "expert",
            [
                "Quickstart",
                "Chapter1",
                "Chapter2",
                "Chapter3",
                "BasicsTest",
                "Chapter4",
                "Chapter5",
                "Chapter6",
                "AdvancedTest",
            ],
            [
                "Quickstart_test",
                "Chapter1_test",
                "Chapter2_test",
                "Chapter3_test",
                "BasicsTest_test",
                "Chapter4_test",
                "Chapter5_test",
                "Chapter6_test",
                "AdvancedTest_test",
            ],
        )


def insert_chapters_tests(cursor, chapters: list, tests: list):
    """
    Inserts chapters and tests for the user in the database.
    """
    for chapter in chapters:
        cursor.execute(
            "INSERT INTO chapters_users_info (user_id, chapter_name) VALUES (%s, %s)",
            (session["id"], chapter),
        )
    for test in tests:
        cursor.execute(
            "INSERT INTO tests_users_info (user_id, test_name, score) VALUES (%s, %s, %s)",
            (session["id"], test, float(100)),
        )
    print("Chapters and tests inserted for user %s", session["id"])


@app.route("/submitanswer", methods=["POST"])
def submitanswer():
    """
    Handles test submissions and updates user levels and test results in the database based on the score.
    """
    if request.method == "POST":
        if "username" in session:

            # Validate and extract form data
            score = request.form.get("score", type=float)
            test = request.form.get("test")

            # Validate score
            if score is None or not isinstance(score, (float, int)):
                print("Invalid score provided")
                return jsonify({"error": "Invalid score"})

            try:
                with mysql.connect() as connection:
                    with connection.cursor() as cursor:
                        if test == "levels":
                            level_info, chapters, tests = get_level_info(score)
                            if level_info:
                                cursor.execute(
                                    "insert into levels (user_id,level_test) values(%s,%s)",
                                    (session["id"], "finished"),
                                )
                                insert_chapters_tests(cursor, chapters, tests)
                                connection.commit()
                                return jsonify(
                                    {
                                        "info": f"You were set to be a {level_info} because you scored {score}%."
                                    }
                                )

                        else:
                            if score >= 60:
                                cursor.execute(
                                    "insert into tests_users_info (user_id,test_name,score) values(%s,%s,%s)",
                                    (session["id"], test, float(score)),
                                )
                                connection.commit()
                                return jsonify(
                                    {
                                        "success": f"You passed the {format_test_name(test)} with a score of {score}%."
                                    }
                                )
                            else:
                                return jsonify(
                                    {
                                        "error": f"You failed the {format_test_name(test)} with a score of {score}%. You must score over 60% to pass. Try again later."
                                    }
                                )
            except Exception as e:
                print("Error processing the test submission: %s", str(e))
                return jsonify(
                    {"error": "An error occurred processing your submission."}
                )
        else:
            # Redirect to login if user is not logged in or is a teacher
            flash(
                "You need to log in or create an account to access our learning materials!",
                "info",
            )
            return redirect(url_for("login"))


@app.route("/leveltest", methods=["POST"])
def level_test():
    """
    Handles the user's response to the level test and updates the database accordingly.
    If the user cancels the test, they are set to the beginner level and relevant progress is returned.
    """
    if request.method == "POST":
        if "username" in session:
            try:
                if request.form.get("answer") == "no":
                    # Establish a connection to the database
                    with mysql.connect() as connection:
                        with connection.cursor() as cursor:
                            # Update user's level to 'cancel'
                            cursor.execute(
                                "INSERT INTO levels (user_id, level_test) VALUES (%s, %s)",
                                (session["id"], "cancel"),
                            )
                            connection.commit()

                            # Fetch user's progress (completed chapters and tests)
                            cursor.execute(
                                "SELECT chapter_name FROM chapters_users_info WHERE user_id=%s",
                                (session["id"],),
                            )
                            chapters = cursor.fetchall()
                            completed_chapters = [chapter[0] for chapter in chapters]

                            cursor.execute(
                                "select tests.test_name,score from tests inner join tests_users_info on tests.test_name=tests_users_info.test_name where user_id=%s and score>50 order by tests.id",
                                (session["id"]),
                            )
                            tests = cursor.fetchall()
                            completed_tests = [test[0] for test in tests]

                            cursor.execute(
                                "select chapter_name from chapters order by id"
                            )
                            chapters = cursor.fetchall()
                            all_chapters = [chapter[0] for chapter in chapters]
                            cursor.execute("select test_name from tests order by id")
                            tests = cursor.fetchall()
                            all_tests = [test[0] for test in tests]

                    # Return the response as a JSON object
                    return jsonify(
                        {
                            "cancel": "You were assigned to be a beginner!",
                            "chapters": completed_chapters,
                            "tests": completed_tests,
                            "all_chapters": all_chapters,
                            "all_tests": all_tests,
                        }
                    )
            except Exception as e:
                print("Error handling level test cancellation: %s", str(e))
                return (
                    jsonify({"error": "An error occurred processing your request."}),
                    500,
                )
        else:
            flash(
                "You need to log in or create an account to access our learning materials!",
                "info",
            )
            return redirect(url_for("login"))
    return jsonify({"error": "Invalid request method."}), 405


if __name__ == "__main__":
    app.run(debug=True)
