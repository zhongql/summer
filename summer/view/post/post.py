# -*- coding: utf-8 -*-

import os

from flask import Blueprint, g, request, jsonify
from flask.ext.mako import render_template
from flask.ext.misaka import markdown
from slugify import slugify

from summer.model.entry import Entry


bp = Blueprint('post', __name__, url_prefix='/posts')

@bp.route('/<int:id>')
def show_entry(id):
	entry = Entry.get(id)

	return render_template('entry.html', **locals())


@bp.route('/<int:id>/edit')
def edit_entry(id):
	_entry = Entry.get(id)

	post_title = _entry['title']
	post_content = _entry['content']
	slug = _entry['slug']
	status = _entry['status']

	return render_template('edit.html', **locals())


@bp.route('/<int:id>/update', methods=['POST'])
def update_entry(id):
	title = request.form['title']
	content = request.form['content']

	_entry = Entry.update(title, content, id)

	name = _entry['slug']
	create_time = _entry['create_time']
	status = _entry['status']

	if status == 'draft':
		# delete old file
		os.remove(os.path.join('./summer/_draft/', name + '.md'))

		# create new file
		filepath = os.path.join('./summer/_draft/', name + '.md')
	else:
		# delete old file
		os.remove(os.path.join('./summer/post/', name + '.md'))

		# create new file
		filepath = os.path.join('./summer/post/', name + '.md')

	newfile = open(unicode(filepath, 'utf8'), 'w')

	newfile.write('title: \"' + title.encode('utf8') + '\"\n')
	newfile.write('date: ' + create_time + '\n')
	newfile.write('---' + '\n\n')
	newfile.write(content.encode('utf8'))
	newfile.write('\n')
	newfile.close()

	return jsonify(r=True)


@bp.route('/<int:id>/del', methods=['POST'])
def delete_entry(id):
	_entry = Entry.delete(id)

	name = _entry['slug']
	status = _entry['status']

	if status == 'draft':
		os.remove(os.path.join('./summer/_draft/', name + '.md'))
	else:
		os.remove(os.path.join('./summer/post/', name + '.md'))

	return jsonify(r=True)


@bp.route('/<int:id>/save', methods=['POST'])
def save(id):
	if id == '-1':
		title = request.form['title']
		slug = slugify(title)
		content = request.form['content']
		date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		g.db.execute('insert into entries (title, content, create_time, slug, status) values (?, ?, ?, ?, "draft")',
								 [title, content, date, slug], )
		g.db.commit()

		filepath = os.path.join('./summer/_draft/', slug + '.md')
		newfile = open(unicode(filepath, 'utf8'), 'w')

		meta =  yaml.safe_dump({
			'title': title,
			'date': date,
			'tags': [''],
			'categories': ['']
		}, default_flow_style=False).replace('- ', '  - ')

		newfile.write(meta + '\n')
		newfile.write('---' + '\n\n')
		newfile.write(content.encode('utf8'))
		newfile.write('\n')
		newfile.close()

		cur = g.db.execute('select id, status from entries where slug=?', (slug,))

		entry = cur.fetchone()

		id = entry['id']
		status = entry['status']

		return jsonify(r=True, id=id, status=status)
	else:
		title = request.form['title']
		content = request.form['content']

		_entry = Entry.save_entry(title, content, id)

		name = _entry['slug']
		date = _entry['create_time']
		status = _entry['status']

		if status == 'draft':
			filename = os.path.join('./summer/_draft/', name + '.md')
		else:
			filename = os.path.join('./summer/post/', name + '.md')

		open(filename, 'w').close()

		newfile = open(filename, 'w')

		meta =  yaml.safe_dump({
			'title': title.encode('utf8'),
			'date': date,
			'tags': [''],
			'categories': ['']
		}, default_flow_style=False).replace('- ', '  - ')

		newfile.write(meta + '\n')
		newfile.write('---' + '\n\n')
		newfile.write(content.encode('utf8'))
		newfile.write('\n')
		newfile.close()

		return jsonify(r=True, id=id, status=status)


@bp.route('/<int:id>/update_status', methods=['POST'])
def publish_draft(id):
	status = request.form['status']

	entry = Entry.update_status(id)

	slug = entry['slug']

	draft_file = os.path.join('./summer/_draft/', filename + '.md')
	post_file = os.path.join('./summer/post/', filename + '.md')

	if status == 'publish':
		os.rename(draft_file, post_file)
	else if status == 'unpublish':
		os.rename(post_file, draft_file)

	return jsonify(r=True)

