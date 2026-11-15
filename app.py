"""FonDeep: Flask ile yazılmış kitle fonlama platformu."""
import os
from datetime import date
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from database import connect, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("FONDEEP_SECRET_KEY", "gelistirme-anahtari")

CATEGORIES = ["Teknoloji", "Eğitim", "Sanat", "Çevre", "Sosyal Sorumluluk"]

# Kart kapağının rengi kategoriye göre seçilir (style.css içindeki sınıflar).
CATEGORY_COVERS = {
    "Teknoloji": "cover-teknoloji",
    "Eğitim": "cover-egitim",
    "Sanat": "cover-sanat",
    "Çevre": "cover-cevre",
    "Sosyal Sorumluluk": "cover-sosyal",
}

FUNDING_TYPES = {
    "fixed": {
        "label": "Hedef Bazlı Fonlama",
        "desc": "Kampanya süresi sonunda hedef tutara ulaşılırsa fon proje sahibine "
        "aktarılır, ulaşılamazsa bağışlar destekçilere iade edilir.",
    },
    "flexible": {
        "label": "Esnek Fonlama",
        "desc": "Hedef tutara ulaşılıp ulaşılmadığından bağımsız olarak toplanan fon "
        "proje sahibine aktarılır.",
    },
}

PANELS = {
    "destekci": {
        "label": "Destekçi",
        "title": "Destekçi Girişi",
        "desc": "Projeleri keşfedin ve beğendiğiniz projelere destek olun.",
    },
    "girisimci": {
        "label": "Girişimci",
        "title": "Girişimci Girişi",
        "desc": "Projelerinizi yayınlayın ve fonlama sürecini yönetin.",
    },
}

PROJECT_QUERY = """
    SELECT p.*, u.name AS owner_name,
           COALESCE(SUM(d.amount), 0) AS raised,
           COUNT(d.id)                AS backer_count
    FROM projects p
    JOIN users u ON u.id = p.owner_id
    LEFT JOIN donations d ON d.project_id = p.id
"""


# --------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def format_tl(amount):
    """12500 -> '12.500 ₺', 99.5 -> '99,50 ₺'"""
    amount = float(amount)
    if amount.is_integer():
        text = f"{int(amount):,}".replace(",", ".")
    else:
        text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} ₺"


app.jinja_env.filters["tl"] = format_tl


def enrich(row):
    p = dict(row)
    p["percent"] = round(p["raised"] / p["goal_amount"] * 100)
    p["bar_percent"] = min(p["percent"], 100)
    p["days_left"] = (date.fromisoformat(p["deadline"]) - date.today()).days
    p["funding_label"] = FUNDING_TYPES[p["funding_type"]]["label"]
    p["funding_desc"] = FUNDING_TYPES[p["funding_type"]]["desc"]
    p["is_open"] = p["days_left"] >= 0
    reached = p["raised"] >= p["goal_amount"]

    if p["is_open"]:
        p["status"] = "Hedefe Ulaştı" if reached else "Aktif"
    elif reached:
        p["status"] = "Başarıyla Tamamlandı"
    elif p["funding_type"] == "fixed":
        p["status"] = "Hedefe Ulaşılamadı - İade Sürecinde"
    else:
        p["status"] = "Tamamlandı"
    return p


def load_projects(where="", params=()):
    """Projeleri toplanan tutar ve bağış sayısıyla birlikte getirir."""
    rows = get_db().execute(
        PROJECT_QUERY + where + " GROUP BY p.id ORDER BY p.id", params
    ).fetchall()
    projects = [enrich(row) for row in rows]
    for p in projects:
        p["cover"] = CATEGORY_COVERS.get(p["category"], "cover-teknoloji")
    return projects


def get_project(project_id):
    projects = load_projects(" WHERE p.id = ?", (project_id,))
    if not projects:
        abort(404)
    return projects[0]


@app.before_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()


@app.context_processor
def inject_user():
    return {"current_user": g.get("user"), "active_panel": session.get("panel", "destekci")}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Bu sayfayı görmek için giriş yapmalısınız.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


# --------------------------------------------------------------------------
# Ana sayfa ve proje sayfaları
# --------------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    stats = {
        "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
        "raised": db.execute("SELECT COALESCE(SUM(amount), 0) FROM donations").fetchone()[0],
        "donations": db.execute("SELECT COUNT(*) FROM donations").fetchone()[0],
    }
    active = [p for p in load_projects() if p["is_open"]]
    featured = sorted(active, key=lambda p: p["raised"] / p["goal_amount"], reverse=True)[:3]
    return render_template(
        "index.html", stats=stats, featured=featured, funding_types=FUNDING_TYPES
    )


@app.route("/projeler")
def projects():
    q = request.args.get("q", "").strip()
    category = request.args.get("kategori", "").strip()

    conditions, params = [], []
    if q:
        conditions.append("(p.title LIKE ? OR p.short_desc LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if category in CATEGORIES:
        conditions.append("p.category = ?")
        params.append(category)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    return render_template(
        "projects.html",
        projects=load_projects(where, params),
        categories=CATEGORIES,
        q=q,
        selected=category,
    )


@app.route("/projeler/<int:project_id>")
def project_detail(project_id):
    project = get_project(project_id)
    donations = get_db().execute(
        "SELECT donor_name, amount, message, created_at FROM donations"
        " WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    ).fetchall()
    return render_template("project_detail.html", project=project, donations=donations)


@app.route("/projeler/<int:project_id>/bagis", methods=["POST"])
def donate(project_id):
    project = get_project(project_id)
    if not project["is_open"]:
        flash("Bu projenin kampanya süresi sona ermiştir.", "error")
        return redirect(url_for("project_detail", project_id=project_id))

    try:
        amount = float(request.form.get("amount", "0").replace(",", "."))
    except ValueError:
        amount = 0
    if amount <= 0:
        flash("Lütfen geçerli bir bağış tutarı girin.", "error")
        return redirect(url_for("project_detail", project_id=project_id))

    name = request.form.get("donor_name", "").strip() or "Anonim"
    message = request.form.get("message", "").strip() or None
    db = get_db()
    db.execute(
        "INSERT INTO donations (project_id, user_id, donor_name, amount, message) VALUES (?, ?, ?, ?, ?)",
        (project_id, session.get("user_id"), name, amount, message),
    )
    db.commit()
    flash(f"{format_tl(amount)} tutarındaki bağışınız için teşekkür ederiz.", "success")
    return redirect(url_for("project_detail", project_id=project_id))


# --------------------------------------------------------------------------
# Giriş, kayıt ve paneller
# --------------------------------------------------------------------------
@app.route("/giris", methods=["GET", "POST"])
def login():
    panel = request.values.get("panel", "destekci")
    if panel not in PANELS:
        panel = "destekci"
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("E-posta adresi veya şifre hatalı.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["panel"] = panel
            return redirect(url_for("dashboard"))
    return render_template("login.html", panels=PANELS, active=panel, email=email)


@app.route("/kayit", methods=["GET", "POST"])
def register():
    form = {"name": "", "email": ""}
    errors = {}
    if request.method == "POST":
        form["name"] = request.form.get("name", "").strip()
        form["email"] = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not form["name"]:
            errors["name"] = "Ad soyad alanı boş bırakılamaz."
        if not form["email"]:
            errors["email"] = "E-posta alanı boş bırakılamaz."
        if not password:
            errors["password"] = "Şifre alanı boş bırakılamaz."

        if not errors:
            # Ara rapor aşamasında yeni kullanıcı kaydı bilerek kapalıdır:
            # form ve alan doğrulaması çalışır, veritabanına kayıt yapılmaz.
            flash("Kayıt işlemi henüz aktif değildir. Örnek hesaplardan biriyle giriş yapabilirsiniz.", "info")
    return render_template("register.html", form=form, errors=errors)


@app.route("/panel")
@login_required
def dashboard():
    panel = session.get("panel", "destekci")
    db = get_db()
    if panel == "girisimci":
        projects = load_projects(" WHERE p.owner_id = ?", (g.user["id"],))
        return render_template("dashboard_creator.html", projects=projects)

    donations = db.execute(
        "SELECT d.amount, d.message, d.created_at, p.id AS project_id, p.title"
        " FROM donations d JOIN projects p ON p.id = d.project_id"
        " WHERE d.user_id = ? ORDER BY d.id DESC",
        (g.user["id"],),
    ).fetchall()
    total = sum(d["amount"] for d in donations)
    return render_template("dashboard_backer.html", donations=donations, total=total)


@app.route("/panel/<panel>")
@login_required
def switch_panel(panel):
    if panel not in PANELS:
        abort(404)
    session["panel"] = panel
    return redirect(url_for("dashboard"))


@app.route("/proje-olustur", methods=["GET", "POST"])
@login_required
def create_project():
    form = {
        "title": "",
        "short_desc": "",
        "description": "",
        "category": CATEGORIES[0],
        "goal_amount": "",
        "deadline": "",
        "funding_type": "fixed",
    }
    if request.method == "POST":
        for key in form:
            form[key] = request.form.get(key, "").strip()

        errors = []
        if not all(form.values()):
            errors.append("Lütfen bütün alanları doldurun.")
        try:
            goal = float(form["goal_amount"].replace(",", "."))
        except ValueError:
            goal = 0
        if form["goal_amount"] and goal <= 0:
            errors.append("Hedef tutar sıfırdan büyük olmalıdır.")
        if form["deadline"]:
            try:
                if date.fromisoformat(form["deadline"]) <= date.today():
                    errors.append("Bitiş tarihi ileri bir tarih olmalıdır.")
            except ValueError:
                errors.append("Bitiş tarihi geçerli değil.")
        if form["category"] not in CATEGORIES:
            errors.append("Geçerli bir kategori seçin.")
        if form["funding_type"] not in FUNDING_TYPES:
            errors.append("Geçerli bir fonlama modeli seçin.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            db = get_db()
            cur = db.execute(
                "INSERT INTO projects (owner_id, title, short_desc, description, category,"
                " goal_amount, funding_type, deadline) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    g.user["id"],
                    form["title"],
                    form["short_desc"],
                    form["description"],
                    form["category"],
                    goal,
                    form["funding_type"],
                    form["deadline"],
                ),
            )
            db.commit()
            session["panel"] = "girisimci"
            flash("Projeniz yayınlandı.", "success")
            return redirect(url_for("project_detail", project_id=cur.lastrowid))

    return render_template(
        "create_project.html", form=form, categories=CATEGORIES, funding_types=FUNDING_TYPES
    )


@app.route("/cikis")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# Uygulama ilk kez çalıştığında tablolar oluşturulur ve örnek veriler yüklenir.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
