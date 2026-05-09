from flask import render_template


class AboutController:
    def __call__(self):
        return render_template("public/about.html")
