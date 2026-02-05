from app import create_app, db
from app.models import Modality

app = create_app()
with app.app_context():
    columns = [c.name for c in Modality.__table__.columns]
    print(f"COLUMNS: {columns}")
    
    # Update existing modalities if column exists
    if 'default_duration' in columns:
        musc = Modality.query.filter(Modality.name.ilike('%musculação%')).first()
        if musc: musc.default_duration = 60
        
        ems = Modality.query.filter(Modality.name.ilike('%eletroestimulação%')).first()
        if ems: ems.default_duration = 60
        
        lipo = Modality.query.filter(Modality.name.ilike('%eletrolipólise%')).first()
        if lipo: lipo.default_duration = 90
        
        db.session.commit()
        print("Updated modalities durations.")
