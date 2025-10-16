from app import create_app, db
from app.models import User, Membership, CreditPurchase, News, Event

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Membership': Membership,
        'CreditPurchase': CreditPurchase,
        'News': News,
        'Event': Event
    }

if __name__ == '__main__':
    app.run(debug=True)
