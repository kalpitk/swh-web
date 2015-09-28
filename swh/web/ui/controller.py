# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import logging

from flask import redirect, render_template, url_for, flash, request


from swh.web.ui.main import app
from swh.web.ui import service


@app.route('/')
def main():
    """Main application view.
    At the moment, redirect to the content search view.
    """
    return redirect(url_for('info'))


@app.route('/info')
def info():
    """A simple api to define what the server is all about.

    """
    logging.info('Dev SWH UI')
    return 'Dev SWH UI'


@app.route('/search')
def search():
    """Search for hashes in swh-storage.

    """
    q = request.args.get('q', '')

    if q:
        flash("Search hash '%s' posted!" % q)
        message = service.lookup_hash(q)
    else:
        message = ''

    return render_template('search.html',
                           q=q,
                           message=message)


@app.route('/browse/revision/<sha1_git>')
def revision(sha1_git):
    """Show commit information.

    Args:
        sha1_git: the revision's sha1

    Returns:
        Revision information
    """
    return render_template('revision.html',
                           sha1_git=sha1_git)


@app.route('/browse/directory/<sha1_git>')
def directory(sha1_git):
    """Show directory information.

    Args:
        sha1_git: the directory's sha1

    Returns:
        Directory information
    """
    return render_template('directory.html',
                           sha1_git=sha1_git)


@app.route('/browse/directory/<sha1_git>/<path:p>')
def directory_at_path(sha1_git, p):
    """Show directory information for the sha1_git at path.

    Args:
        sha1_git: the directory's sha1
        path: file or directory pointed to

    Returns:
        Directory information at sha1_git + path
    """
    return render_template('directory.html',
                           sha1_git=sha1_git,
                           path=p)


@app.route('/browse/content/<hash>:<sha>')
def content(hash, sha):
    """Show content information.

    Args:
        hash: hash according to HASH_ALGO, where HASH_ALGO is
    one of: sha1, sha1_git, sha256. This means that several different URLs (at
    least one per HASH_ALGO) will point to the same content
        sha: the sha with 'hash' format

    Returns:
        The content's information at sha1_git

    """
    return render_template('content.html',
                           hash=hash,
                           sha=sha)


@app.route('/browse/release/<sha1_git>')
def release(sha1_git):
    """Show release's information.

    Args:
        sha1_git: sha1_git for this particular release

    Returns:
        Release's information

    """
    return 'Release information at %s' % sha1_git


@app.route('/browse/person/<int:id>')
def person(id):
    """Show Person's information at id.

    Args:
        id: person's unique identifier

    Returns:
        Person's information

    """
    return 'Person information at %s' % id


@app.route('/browse/origin/<int:id>')
def origin(id):
    """Show origin's information at id.

    Args:
        id: origin's unique identifier

    Returns:
        Origin's information

    """
    return 'Origin information at %s' % id


@app.route('/browse/project/<int:id>')
def project(id):
    """Show project's information at id.

    Args:
        id: project's unique identifier

    Returns:
        Project's information

    """
    return 'Project information at %s' % id


@app.route('/browse/organization/<int:id>')
def organization(id):
    """Show organization's information at id.

    Args:
        id: organization's unique identifier

    Returns:
        Organization's information

    """
    return 'Organization information at %s' % id


@app.route('/browse/directory/<string:timestamp>/<string:origin_type>+<path:origin_url>|/<path:branch>|/<path:path>')
def directory_at_origin(timestamp, origin_type, origin_url, branch, path):
    """Show directory information at timestamp, origin-type, origin-url, branch
    and path.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or some iso8601 date
    format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)
        branch: branch name which can contain `/`
        path: path to directory or file

    Returns:
        Directory information at the given parameters.

    """
    return 'Directory at (%s, %s, %s, %s, %s)' % (timestamp,
                                                  origin_type,
                                                  origin_url,
                                                  branch,
                                                  path)


@app.route('/browse/revision/<string:timestamp>/<string:origin_type>+<path:origin_url>|/<path:branch>')
def revision_at_origin_and_branch(timestamp, origin_type, origin_url, branch):
    """Show revision information at timestamp, origin, and branch.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or some iso8601 date
        format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)
        branch: branch name which can contain /

    Returns:
        Revision information at the given parameters.

    """
    return 'Revision at (ts=%s, type=%s, url=%s, branch=%s)' % (timestamp,
                                                                origin_type,
                                                                origin_url,
                                                                branch)


@app.route('/browse/revision/<string:timestamp>/<string:origin_type>+<path:origin_url>|')
def revision_at_origin(timestamp, origin_type, origin_url):
    """Show revision information at timestamp, origin, and branch.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or some iso8601 date
        format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)

    Returns:
        Revision information at the given parameters.

    """
    return 'Revision at (timestamp=%s, type=%s, url=%s)' % (timestamp,
                                                            origin_type,
                                                            origin_url)


def run(conf):
    """Run the api's server.

    Args:
        conf is a dictionary of keywords:
        - 'db_url' the db url's access (through psycopg2 format)
        - 'content_storage_dir' revisions/directories/contents storage on disk
        - 'host'   to override the default 127.0.0.1 to open or not the server
        to the world
        - 'port'   to override the default of 5000 (from the underlying layer:
        flask)
        - 'debug'  activate the verbose logs

    Returns:
        Never

    Raises:
        ?

    """
    print("""SWH Web UI run
host: %s
port: %s
debug: %s""" % (conf['host'], conf.get('port', None), conf['debug']))

    app.config.update({'conf': conf})

    app.run(host=conf['host'],
            port=conf.get('port', None),
            debug=conf['debug'])
