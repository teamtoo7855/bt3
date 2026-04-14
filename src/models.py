from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Index
from sqlalchemy.exc import OperationalError
import os, pandas
from tools.fetch_gtfs_static import fetch_gtfs_static

db = SQLAlchemy()
Models = {}

def check_db_exists(app):
    # get GTFS static data if not already existing
    db_path = os.path.join(app.instance_path, "static.db")
    if not os.path.isfile(db_path):
        print("Static data not found, fetching")
        fetch_gtfs_static(app.instance_path)
        with app.app_context():
            db.create_all()     # create database if not yet existing
            for f in os.listdir(app.instance_path):
                if f.endswith('.txt'):
                    name = f.split('.')[0]
                    path = os.path.join(app.instance_path, f)
                    df = pandas.read_csv(path)
                    df.to_sql(name, db.engine, if_exists="replace", index=False)
                    os.remove(path)
                    print(f'{f} imported into db')
    else:
        print("Static data found")

def reflect_tables(app):
    with app.app_context():
        db.reflect()
        for table_name, table in db.metadata.tables.items():
            pk_col = Column("rowid", Integer, primary_key=True)
            table.append_column(pk_col)

            model = type(
                table_name.capitalize(),
                (db.Model,),
                {"__table__": table}
            )
            Models[table_name] = model
            print(f"Model reflected: {table_name}")
        create_gtfs_indexes(db.engine)

def create_gtfs_indexes(engine):
    indexes = [
        # index for route lookup from stop code
        Index("idx_stops_stop_code",    Models["stops"].__table__.c.stop_code),
        Index("idx_stop_times_stop_id", Models["stop_times"].__table__.c.stop_id),
        Index("idx_stop_times_trip_id", Models["stop_times"].__table__.c.trip_id),

        # index for shape lookup from trip id
        Index("idx_trips_shape_id",  Models["trips"].__table__.c.shape_id),
        Index("idx_shapes_shape_id", Models["shapes"].__table__.c.shape_id),
    ]

    for idx in indexes:
        try:
            idx.create(engine)
            print(f"Indexed: {idx.name}")
        except OperationalError:
            print(f"Skipped: {idx.name} (exists)")