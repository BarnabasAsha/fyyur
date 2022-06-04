#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120),)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String, nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    seeking_description = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    shows = db.relationship('Show', backref='venues',
                            lazy=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Venue id={self.id} name={self.name} city={self.city} state={self.state}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    seeking_description = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    shows = db.relationship('Show', backref='artists',
                            lazy=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Artist id={self.id} name={self.name} city={self.city} state={self.state}>'


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __repr__(self):
        return f'<Show id={self.id} artist_id={self.artist_id} venue_id={self.venue_id} start_time={self.start_time}'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# Utils
#----------------------------------------------------------------------------#

def orm_obj_list_to_dict(obj_list):
    for u in obj_list:
        print("\n", u.__dict__, "\n")

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    venues = Venue.query.order_by(db.desc(Venue.created_at)).limit(10).all()
    artists = Artist.query.order_by(db.desc(Artist.created_at)).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    results = Venue.query.distinct(Venue.city, Venue.state).all()
    for result in results:
        city_state_data = {
            "city": result.city,
            "state": result.state
        }
        venues = Venue.query.filter_by(
            city=result.city, state=result.state).all()

        # format each venue
        formatted_venues = []
        for venue in venues:
            formatted_venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
            })

        city_state_data["venues"] = formatted_venues
        data.append(city_state_data)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    # convert genre string back to array
    setattr(venue, "genres", venue.genres.split(","))

    # get past shows
    past_shows = list(filter(lambda show: show.start_time <
                      datetime.now(), venue.shows))
    temp_shows = []
    for show in past_shows:
        temp = {}
        temp["artist_name"] = show.artists.name
        temp["artist_id"] = show.artists.id
        temp["artist_image_link"] = show.artists.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        temp_shows.append(temp)

    setattr(venue, "past_shows", temp_shows)
    setattr(venue, "past_shows_count", len(past_shows))

    # get future shows
    upcoming_shows = list(
        filter(lambda show: show.start_time > datetime.now(), venue.shows))
    temp_shows = []
    for show in upcoming_shows:
        temp = {}
        temp["artist_name"] = show.artists.name
        temp["artist_id"] = show.artists.id
        temp["artist_image_link"] = show.artists.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        temp_shows.append(temp)

    setattr(venue, "upcoming_shows", temp_shows)
    setattr(venue, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submit():
    form = VenueForm(request.form)

    if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                # convert array to string separated by commas
                genres=",".join(form.genres.data),
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                website=form.website.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue' + ' could not be listed.')

        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash('An error occurred. Venue' + ' could not be listed.')

    return redirect(url_for("index"))


#  Update Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # convert genre string back to array
    form.genres.data = venue.genres.split(",")

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submit(venue_id):
    form = VenueForm(request.form)

    if form.validate():
        try:
            venue = Venue.query.get(venue_id)

            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            # convert array to string separated by commas
            venue.genres = ",".join(form.genres.data)
            venue.facebook_link = form.facebook_link.data
            venue.image_link = form.image_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.website = form.website.data

            db.session.add(venue)
            db.session.commit()

            flash("Venue " + form.name.data + " edited successfully")

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash("Venue was not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Venue was not edited successfully.")

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Delete Venue
#  ----------------------------------------------------------------

@app.route("/venues/<venue_id>/delete", methods={"GET"})
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + venue.name + " was deleted successfully!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue was not deleted successfully.")
    finally:
        db.session.close()

    return redirect(url_for("index"))


#  Search Venue
#  ----------------------------------------------------------------

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_query = request.form.get("search_query", "")

    response = {}
    venues = list(Venue.query.filter(
        Venue.name.ilike(f"%{search_query}%") |
        Venue.state.ilike(f"%{search_query}%") |
        Venue.city.ilike(f"%{search_query}%")
    ).all())
    response["count"] = len(venues)
    response["data"] = []

    for venue in venues:
        venue_unit = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
        }
        response["data"].append(venue_unit)

    return render_template('pages/search_venues.html', results=response, search_query=search_query)


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)
    # convert genre string back to array
    setattr(artist, "genres", artist.genres.split(","))

    # get past shows
    past_shows = list(filter(lambda show: show.start_time <
                      datetime.now(), artist.shows))
    temp_shows = []
    for show in past_shows:
        temp = {}
        temp["venue_name"] = show.venues.name
        temp["venue_id"] = show.venues.id
        temp["venue_image_link"] = show.venues.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "past_shows", temp_shows)
    setattr(artist, "past_shows_count", len(past_shows))

    # get upcoming shows
    upcoming_shows = list(
        filter(lambda show: show.start_time > datetime.now(), artist.shows))
    temp_shows = []
    for show in upcoming_shows:
        temp = {}
        temp["venue_name"] = show.venues.name
        temp["venue_id"] = show.venues.id
        temp["venue_image_link"] = show.venues.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "upcoming_shows", temp_shows)
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_artist.html', artist=artist)


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submit():
    form = ArtistForm(request.form)

    if form.validate():
        try:
            new_artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                # convert array to string separated by commas
                genres=",".join(form.genres.data),
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash("Artist " + request.form["name"] +
                  " was successfully listed!")
        except Exception:
            db.session.rollback()
            flash("Artist was not successfully listed.")
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash("Artist was not successfully listed.")

    return redirect(url_for("index"))


#  Update Artist
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # convert genre string back to array
    form.genres.data = artist.genres.split(",")

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get(artist_id)

            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            # convert array to string separated by commas
            artist.genres = ",".join(form.genres.data)
            artist.facebook_link = form.facebook_link.data
            artist.image_link = form.image_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.website = form.website.data

            db.session.add(artist)
            db.session.commit()
            flash("Artist " + artist.name + " was successfully edited!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Artist was not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Artist was not edited successfully.")

    return redirect(url_for('show_artist', artist_id=artist_id))


#  Delete Artist
#  ----------------------------------------------------------------

@app.route("/artists/<artist_id>/delete", methods=["GET"])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash("Artist " + artist.name + " was deleted successfully!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Artist was not deleted successfully.")
    finally:
        db.session.close()

    return redirect(url_for("index"))


#  Search Artist
#  ----------------------------------------------------------------

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_query = request.form.get('search_query', '')
    artists = Artist.query.filter(
        Artist.name.ilike(f"%{search_query}%") |
        Artist.city.ilike(f"%{search_query}%") |
        Artist.state.ilike(f"%{search_query}%")
    ).all()
    response = {
        "count": len(artists),
        "data": []
    }

    for artist in artists:
        temp = {}
        temp["name"] = artist.name
        temp["id"] = artist.id

        upcoming_shows = 0
        for show in artist.shows:
            if show.start_time > datetime.now():
                upcoming_shows = upcoming_shows + 1
        temp["upcoming_shows"] = upcoming_shows

        response["data"].append(temp)

    return render_template('pages/search_artists.html', results=response, search_query=search_query)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []

    shows = Show.query.all()
    for show in shows:
        temp = {}
        temp["venue_id"] = show.venues.id
        temp["venue_name"] = show.venues.name
        temp["artist_id"] = show.artists.id
        temp["artist_name"] = show.artists.name
        temp["artist_image_link"] = show.artists.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        data.append(temp)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submit():
    form = ShowForm(request.form)

    if form.validate():
        try:
            new_show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('Show was not successfully listed.')
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash('Show was not successfully listed.')

    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
