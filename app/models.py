from app import db

class Project(db.Model):
    """
    Project model for storing project workspace details.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Active")

    def __repr__(self):
        return f"<Project {self.name}>"