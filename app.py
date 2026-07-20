from flask import Flask, render_template, request
import os

from parser import process_pdf

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():

    result = None

    if request.method == "POST":

        if "pdf" not in request.files:
            return render_template(
                "index.html",
                result=None,
                error="No se seleccionó ningún archivo."
            )

        file = request.files["pdf"]

        if file.filename == "":
            return render_template(
                "index.html",
                result=None,
                error="Seleccione un PDF."
            )

        if not file.filename.lower().endswith(".pdf"):
            return render_template(
                "index.html",
                result=None,
                error="Solo se permiten archivos PDF."
            )

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        pdf_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(pdf_path)

        try:

            result = process_pdf(pdf_path)

        except Exception as e:

            return render_template(
                "index.html",
                result=None,
                error=str(e)
            )

    return render_template(
        "index.html",
        result=result
    )


if __name__ == "__main__":
    app.run(debug=True)