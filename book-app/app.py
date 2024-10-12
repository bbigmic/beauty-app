from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Potrzebne do obsługi sesji

# Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja bazy danych
db = SQLAlchemy(app)

# Definicja modelu Rezerwacja
class Rezerwacja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    ekspert = db.Column(db.String(100), nullable=False)
    rodzaj = db.Column(db.String(100), nullable=False)
    termin = db.Column(db.String(100), nullable=False)

# Tworzenie bazy danych
with app.app_context():
    db.create_all()

# Lista ekspertów i rodzajów konsultacji
eksperci = ["Jan Kowalski", "Anna Nowak", "Michał Wiśniewski"]
rodzaje_konsultacji = ["Konsultacja techniczna", "Konsultacja biznesowa", "Konsultacja prawna"]

# Dane administratora (hardkodowane na potrzeby tego przykładu)
admin_username = "admin"
admin_password = "password123"

def czy_termin_dostepny(ekspert, termin_start):
    """
    Funkcja sprawdza, czy dany termin jest dostępny dla wybranego eksperta.
    Konsultacja trwa 30 minut, więc porównujemy nowy termin z istniejącymi rezerwacjami.
    """
    termin_koniec = termin_start + timedelta(minutes=30)
    rezerwacje = Rezerwacja.query.filter_by(ekspert=ekspert).all()

    for rezerwacja in rezerwacje:
        istniejący_start = datetime.strptime(rezerwacja.termin, "%Y-%m-%dT%H:%M")
        istniejący_koniec = istniejący_start + timedelta(minutes=30)
        if (termin_start < istniejący_koniec) and (termin_koniec > istniejący_start):
            return False
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        imie = request.form['imie']
        email = request.form['email']
        ekspert = request.form['ekspert']
        rodzaj = request.form['rodzaj']
        termin_str = request.form['termin']

        try:
            termin_start = datetime.strptime(termin_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Nieprawidłowy format terminu. Użyj formatu RRRR-MM-DD GG:MM.")
            return redirect(url_for('index'))

        if czy_termin_dostepny(ekspert, termin_start):
            nowa_rezerwacja = Rezerwacja(
                imie=imie,
                email=email,
                ekspert=ekspert,
                rodzaj=rodzaj,
                termin=termin_start.strftime("%Y-%m-%dT%H:%M")
            )
            db.session.add(nowa_rezerwacja)
            db.session.commit()

            return redirect(url_for('potwierdzenie', imie=imie))
        else:
            flash(f'Termin {termin_str} jest już zajęty dla eksperta {ekspert}. Wybierz inny termin.')
            return redirect(url_for('index'))

    return render_template('index.html', eksperci=eksperci, rodzaje_konsultacji=rodzaje_konsultacji)

@app.route('/potwierdzenie')
def potwierdzenie():
    imie = request.args.get('imie')
    return f'Dziękujemy za rezerwację, {imie}!'

@app.route('/rezerwacje')
def pokaz_rezerwacje():
    rezerwacje = Rezerwacja.query.all()
    return render_template('rezerwacje.html', rezerwacje=rezerwacje)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            flash('Zalogowano pomyślnie.')
            return redirect(url_for('admin_panel'))
        else:
            flash('Niepoprawny login lub hasło.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Wylogowano pomyślnie.')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'):
        flash('Musisz być zalogowany, aby uzyskać dostęp do panelu administracyjnego.')
        return redirect(url_for('login'))

    wybrany_ekspert = None
    posortowane_rezerwacje = []

    if request.method == 'POST':
        wybrany_ekspert = request.form['ekspert']
        posortowane_rezerwacje = Rezerwacja.query.filter_by(ekspert=wybrany_ekspert).order_by(Rezerwacja.termin).all()

    return render_template('admin.html', eksperci=eksperci, rezerwacje=posortowane_rezerwacje, wybrany_ekspert=wybrany_ekspert)

if __name__ == '__main__':
    app.run(debug=True)
