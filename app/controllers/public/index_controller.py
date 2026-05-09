from flask import render_template


class IndexController:
    def __call__(self):
        return render_template("public/index.html")
