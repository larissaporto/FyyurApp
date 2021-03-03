#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request,
  Response,
  flash,
  redirect,
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import app, db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
  city_and_state = ''
  data = []
  for venue in venues:
    upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time>current_time).all()
    if city_and_state == venue.city + venue.state:
      data[len(data) - 1]["venues"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      })
    else:
      city_and_state = venue.city + venue.state
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(upcoming_shows)
        }]
      })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  
  response={
    "count": len(results),
    "data": []
  }
  for result in results:
    response["data"].append({
        'id': result.id,
        'name': result.name
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  upcoming_shows = []
  past_shows = []
  venue = Venue.query.get(venue_id)
  upcoming_shows_details = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time >= current_time).all()
  past_shows_details = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time < current_time).all()
  data_shows = []
  
  for show in upcoming_shows_details:
    data_shows = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    upcoming_shows.append(data_shows)
  
  for show in past_shows_details:
    data_shows = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    past_shows.append(data_shows)

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)

  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    data = {}
    if 'seeking_talent' in request.form:
      seeking_talent = True
    else:
        seeking_talent = False
    new_venue = Venue(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_talent=seeking_talent,
      seeking_description=request.form['seeking_description'],
      website=request.form['website'],
      genres=request.form.getlist('genres')
    )
    db.session.add(new_venue)
    db.session.commit()
    data['id'] = new_venue.id
    data['name'] = new_venue.name
  # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except():
    db.session.rollback()
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    for show in venue.shows:
      db.session.delete(show)
    
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue_name + ' was deleted')
  except():
    db.session.rollback()
    flash('an error occured and Venue ' + venue_name + ' was not deleted')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []

  artists = Artist.query.all()

  for artist in artists:
    data.append({
        "id": artist.id,
        "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  
  response={
    "count": len(results),
    "data": []
  }
  for result in results:
    response["data"].append({
        'id': result.id,
        'name': result.name
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  upcoming_shows = []
  past_shows = []
  artist = Artist.query.get(artist_id)
  upcoming_shows_details = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time >= current_time).all()
  past_shows_details = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time < current_time).all()
  data_shows = []
  
  for show in upcoming_shows_details:
    data_shows = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    upcoming_shows.append(data_shows)
  
  for show in past_shows_details:
    data_shows = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    past_shows.append(data_shows)
  
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)

  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):  
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    data = {}
    artist = Artist.query.get(artist_id)
    if 'seeking_venue' in request.form:
      seeking_venue = True
    else:
      seeking_venue = False
    
    artist.name=request.form['name']
    artist.city=request.form['city']
    artist.state=request.form['state']
    artist.phone=request.form['phone']
    artist.image_link=request.form['image_link']
    artist.facebook_link=request.form['facebook_link']
    artist.seeking_venue=seeking_venue
    artist.seeking_description=request.form['seeking_description']
    artist.website=request.form['website']
    artist.genres=request.form.getlist('genres')
    
    db.session.add(artist)
    db.session.commit()
    data['id'] = artist.id
    data['name'] = artist.name
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except():
    db.session.rollback()
    flash('An error occurred. Artist ' + data.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    data = {}
    venue = Venue.query.get(venue_id)
    if 'seeking_talent' in request.form:
      seeking_talent = True
    else:
      seeking_talent = False
    
    venue.name=request.form['name']
    venue.city=request.form['city']
    venue.state=request.form['state']
    venue.address=request.form['address']
    venue.phone=request.form['phone']
    venue.image_link=request.form['image_link']
    venue.facebook_link=request.form['facebook_link']
    venue.seeking_talent=seeking_talent
    venue.seeking_description=request.form['seeking_description']
    venue.website=request.form['website']
    venue.genres=request.form.getlist('genres')
    
    db.session.add(venue)
    db.session.commit()
    data['id'] = venue.id
    data['name'] = venue.name
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except():
    db.session.rollback()
    flash('An error occurred. Venue ' + data.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    data = {}
    if 'seeking_venue' in request.form:
      seeking_venue = True
    else:
      seeking_venue = False
    new_artist = Artist(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_venue=seeking_venue,
      seeking_description=request.form['seeking_description'],
      website=request.form['website'],
      genres=request.form.getlist('genres')
    )
    db.session.add(new_artist)
    db.session.commit()
    data['id'] = new_artist.id
    data['name'] = new_artist.name
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except():
    db.session.rollback()
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows_listed = db.session.query(Show).order_by(db.desc(Show.start_time))

  for show in shows_listed:
    data.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time),
      "venue_id": show.venue_id,
      "venue_name": show.venue.name
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    new_show = Show(
      artist_id=request.form['artist_id'],
      venue_id=request.form['venue_id'],
      start_time=request.form['start_time'],
    )
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except():
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
