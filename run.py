import os
from app import create_app, db
from app.models import User, Modality, Package, ClassSchedule, Booking, Subscription

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Modality': Modality, 
        'Package': Package,
        'ClassSchedule': ClassSchedule,
        'Booking': Booking,
        'Subscription': Subscription
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
