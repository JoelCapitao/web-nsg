import os
from flask import render_template, request, flash, redirect, url_for, Response, session, send_file, send_from_directory, g, json
from model import *
from netscriptgen import NetScriptGen, Integer
from werkzeug import secure_filename
from shutil import move
from validationForm import *
from zip_list_of_files_in_memory import zip_file
from fnmatch import fnmatch
from flask.ext.login import LoginManager, login_user, login_required, logout_user, current_user
import pickle, re
SESSION_TYPE = 'redis'
SECRET_KEY = 'develop'

#TODO 404 Not Found
#TODO Methode not allowed

# Initializing Flask-Login configuring it
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# This callback is used to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()

@app.before_request
def before_request():
    g.user = current_user


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'GET':
        return render_template('register.html', form=form)
    if request.method == 'POST' and form.validate():
        user_exists = User.query.filter_by(mail=request.form['email']).first()
        if not user_exists:
            user = User(request.form['firstname'],
                        request.form['lastname'],
                        request.form['email'],
                        request.form['password'],
                        request.form['uid'],
                        request.form['function'],
                        request.form['service'])

            error_while_adding_user = user.add(user)
            if not error_while_adding_user:
                flash('Congrats, registered successfully! You can now log in', 'success')
                return redirect(url_for('login'))
            else:
                flash(error_while_adding_user, 'danger')
        else:
            flash('The user already exists', 'danger')
            return render_template('register.html', form=form)
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'GET':
        return render_template('login.html', form=form)
    if request.method == 'POST' and form.validate():
        user_exists = User.query.filter_by(mail=request.form['email']).first()
        if not user_exists:
            flash('Your email or password does not match', 'danger')
        else:
            if user_exists.check_password(request.form['password']):
                remember_me = False
                if 'remember_me' in request.form:
                    remember_me = True
                # Creating a session on user's browser
                login_user(user_exists, remember=remember_me)
                return redirect(url_for('project_display_all'))
            else:
                flash('Your email or password does not match', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/project/new', methods=['GET','POST'])
@login_required
def project_new():
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():

        _folder = '{0}-{1}'.format(request.form['client'], request.form['project_name'])
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], _folder)
        session['project_folder'] = project_folder
        os.makedirs(project_folder, exist_ok=True)

        excel_file = request.files['excel_file']
        excel_file_path = os.path.join(project_folder, secure_filename(excel_file.filename))
        excel_file.save(excel_file_path)

        template_file = request.files['template_file']
        template_file_path = os.path.join(project_folder, secure_filename(template_file.filename))
        template_file.save(template_file_path)

        project_data = dict()
        for item in ('client', 'project_name', 'subproject_name'):
            project_data[item] = request.form[item]
        session['project_data'] = project_data

        versioning_data = {'to_fill': 0, 'filled': 0}
        for item, path in [('excel_file', excel_file.filename), ('template_file', template_file.filename)]:
            versioning_data[item] = path
        try:
            equipments, wb, hostnames = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error


        data_of_equipments = list()
        for equipment in equipments:
            equipment.save_script_as(project_folder, equipment.hostname)

            versioning_data['to_fill'] += equipment.get_nbr_of_var_to_fill_in()
            versioning_data['filled'] += equipment.get_resolved_var()

            _data_of_equipment = dict()
            for param in ('Hostname', 'Equipment', 'Type'):
                _data_of_equipment[param] = wb['Global'].get_value_of_var_by_index_and_param(equipment.hostname, param)
            _data_of_equipment['filling_ratio'] = equipment.get_filling_ratio()
            _data_of_equipment['filling_ratio_in_percentage'] = equipment.get_filling_ratio_in_percentage()
            _data_of_equipment['tb'] = equipment.tb
            _data_of_equipment['project_folder'] = _folder
            data_of_equipments.append(_data_of_equipment)

        versioning_data['fillingRatio'] = '{:.0%}'.format(versioning_data['filled']/versioning_data['to_fill'])
        session['versioning_data'] = versioning_data

        with open(os.path.join(project_folder, 'data.pickle'), 'wb') as f:
            pickle.dump(data_of_equipments, f, 0)

        return render_template('generation_preview.html', equipments=data_of_equipments, iterator=Integer(1))

    return render_template('project.html', form=form)


@app.route('/project/add', methods=['GET','POST'])
@login_required
def project_add():
    if request.method == 'POST':
        project_data = session.get('project_data')
        versioning_data = session.get('versioning_data')

        project = Project(project_data['client'],
                          project_data['project_name'],
                          project_data['subproject_name'])
        project.user = g.user
        project.add_user(g.user)
        post_add = project.add(project)

        if project_data['subproject_name']:
            zf_name = "scripts-{0}-{1}-{2}-v1.zip".format(project_data['client'], project_data['project_name'], project_data['subproject_name'])
        else:
            zf_name = "scripts-{0}-{1}-v1.zip".format(project_data['client'], project_data['project_name'])

        project = last_project()
        project_versioning = ProjectVersioning(1,
                                               versioning_data['excel_file'],
                                               versioning_data['template_file'],
                                               versioning_data['to_fill'],
                                               versioning_data['filled'],
                                               versioning_data['fillingRatio'],
                                               zf_name,
                                               project,
                                               g.user)
        project_versioning = project_versioning.add(project_versioning)

        if not post_add and not project_versioning:
            new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project.id), 'v1')
            move(session['project_folder'], new_project_folder)

            try:
                zip_file(new_project_folder, os.path.join(new_project_folder, zf_name))
            except:
                pass

            return redirect(url_for('project_display', project_id=last_id_of_the_table_project()))
        else:
            error = post_add
            flash(error)
    return redirect(url_for('project_display_all'))


def nsg_processing(excel_worbook, template_file):
    excel_wb = excel_worbook
    template = open(template_file, 'r', -1, 'UTF-8').read()
    nsg = NetScriptGen(excel_wb, template)
    nsg.extract_data()
    equipments = nsg.get_all_equipments()
    hostnames = nsg.get_all_equipment_names()
    return equipments, nsg.workbook, hostnames


@app.route('/project')
@login_required
def project_display_all():
    projects = Project.query.join(project_users, (project_users.c.project_id == Project.id)).filter(
        (Project.user == g.user) |
        (Project.public.isnot(False)) |
        (g.user.id == project_users.c.user_id)
    ).all()
    for _project in projects:
        _all_version_of_the_project = _project.version.all()
        if _all_version_of_the_project:
            last_version = _all_version_of_the_project[-1]
            for item in ('excelFile', 'templateFile'):
                setattr(_project, item, getattr(last_version, item))
            # Because SQLAlchemy do not let us to set an attribute named 'version'
            setattr(_project, 'lastVersion', str(getattr(last_version, 'version')))

    return render_template('project_display_all.html', project=projects)


@app.route('/project/display/<int:project_id>', methods=['GET','POST'])
@login_required
def project_display(project_id):
    project = Project.query.get(project_id)
    if project:
        all_version_of_the_project = project.version.all()
        last_version_of_the_project = all_version_of_the_project[-1]
        for item in ('excelFile', 'templateFile', 'numberOfVarToFill', 'numberOfVarFilled', 'fillingRatio', 'zipFile'):
            setattr(project, item, getattr(last_version_of_the_project, item))
        # The attribute 'version' is not in the loop because the object does not accept an attr with that name
        # So I replace 'version' by 'current_version'
        setattr(project, 'currentVersion', getattr(last_version_of_the_project, 'version'))

        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id),
                                      'v{0}'.format(last_version_of_the_project.version))
        with open(os.path.join(project_folder, 'data.pickle'), 'rb') as f:
            equipments = pickle.load(f)

        form = ProjectForm(request.form)
        users = User.query.all()
        project_users = project.users.all()
        if g.user == project.user:
            return render_template('project_display.html', project=project, versions=all_version_of_the_project[:-1],
                               form=form, alert='None', message='', equipments=equipments, iterator=Integer(1),
                                   user_can_edit=True, user_can_delete=True, users=users, project_users=project_users)
        elif g.user in project_users:
            return render_template('project_display.html', project=project, versions=all_version_of_the_project[:-1],
                               form=form, alert='None', message='', equipments=equipments, iterator=Integer(1),
                                   user_can_edit=True, user_can_delete=False, users=users, project_users=project_users)
        elif project.public is True:
            return render_template('project_display.html', project=project, versions=all_version_of_the_project[:-1],
                               form=form, alert='None', message='', equipments=equipments, iterator=Integer(1),
                                   user_can_edit=False, user_can_delete=False, users=users, project_users=project_users)
        else:
            flash("You are not authorized to consult this project", 'error')
            return redirect(url_for('project_display_all'))
    else:
        flash("The project does not exist in the database", 'error')
        return redirect(url_for('project_display_all'))


@app.route('/project/<int:id>/new', methods=['POST'])
@login_required
def project_new_version(id):
    project = Project.query.get(id)
    all_version_of_the_project = project.version.all()
    last_version = all_version_of_the_project[-1].version
    new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(id), 'v{0}'.format(last_version + 1))
    os.makedirs(new_project_folder, exist_ok=True)

    form = NewProjectVersionForm(request.form)
    if request.method == 'POST' and form.validate():

        excel_file = request.files['excel_file']
        excel_file_path = os.path.join(new_project_folder, secure_filename(excel_file.filename))
        excel_file.save(excel_file_path)

        template_file = request.files['template_file']
        template_file_path = os.path.join(new_project_folder, secure_filename(template_file.filename))
        template_file.save(template_file_path)

        versioning_data = {'to_fill': 0, 'filled': 0}
        for _file, _path in [('excel_file', excel_file.filename), ('template_file', template_file.filename)]:
            versioning_data[_file] = _path
            print(_path)

        try:
            equipments, wb, hostnames = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error


        data_of_equipments = list()
        for equipment in equipments:
            equipment.save_script_as(new_project_folder, equipment.hostname)

            versioning_data['to_fill'] += equipment.get_nbr_of_var_to_fill_in()
            versioning_data['filled'] += equipment.get_resolved_var()

            _data_of_equipment = dict()
            for _item in ('Hostname', 'Equipment', 'Type'):
                _data_of_equipment[_item] = equipment.get_value_of_var(_item, wb)
            _data_of_equipment['filling_ratio'] = equipment.get_filling_ratio()
            _data_of_equipment['filling_ratio_in_percentage'] = equipment.get_filling_ratio_in_percentage()
            _data_of_equipment['tb'] = equipment.tb
            data_of_equipments.append(_data_of_equipment)

            with open(os.path.join(new_project_folder, 'data.pickle'), 'wb') as f:
                pickle.dump(data_of_equipments, f, 0)

        versioning_data['fillingRatio'] = '{:.0%}'.format(versioning_data['filled']/versioning_data['to_fill'])
        versioning_data['project_folder'] = new_project_folder
        session['versioning_data'] = versioning_data

        return render_template('project_upgrade_preview.html', id=project.id,
                               equipments=data_of_equipments, iterator=Integer(1))

    return render_template('project.html', form=form)


@app.route('/project/<int:project_id>/upgrade', methods=['POST'])
@login_required
def project_upgrade(project_id):
    if request.method == 'POST':
        versioning_data = session.get('versioning_data')
        project = Project.query.get(project_id)
        last_version_of_the_project = last_version_of_the_project_id_equal_to(project_id)

        if project.subProjectName:
            zf_name = "scripts-{0}-{1}-{2}-v{3}.zip".format(project.client,
                                                            project.projectName,
                                                            project.subProjectName,
                                                            last_version_of_the_project.version + 1)
        else:
            zf_name = "scripts-{0}-{1}-v{2}.zip".format(project.client,
                                                        project.projectName,
                                                        last_version_of_the_project.version + 1)

        new_version = ProjectVersioning(last_version_of_the_project.version + 1,
                                        versioning_data['excel_file'],
                                        versioning_data['template_file'],
                                        versioning_data['to_fill'],
                                        versioning_data['filled'],
                                        versioning_data['fillingRatio'],
                                        zf_name,
                                        project,
                                        g.user)
        error_in_creation_of_new_version = new_version.add(new_version)

        if not error_in_creation_of_new_version:
            try:
                zip_file(versioning_data['project_folder'], os.path.join(versioning_data['project_folder'], zf_name))
            except:
                pass

            return redirect(url_for('project_display', project_id=project_id))
        else:
            flash(error_in_creation_of_new_version)
    return redirect(url_for('project_display_all'))


@app.route('/project/update/<int:id>', methods=['GET','POST'])
@login_required
def project_update(id):
    form = ProjectUpdateForm(request.form)
    project = Project.query.get(id)

    if project is None:
        flash('The project does not exist in the database', 'error')
        return redirect(url_for('project_display_all'))

    if request.method == 'GET' and g.user not in project.all_users():
        flash('You are not allowed to edit this project', 'error')
        return redirect(url_for('project_display_all'))

    if request.method == 'POST' and form.validate() and g.user in project.all_users():
        column = dict()
        project_updated = Project(request.form['client'],
                                  request.form['project_name'],
                                  request.form['subproject_name'])

        for column_name, form_value in [('client', 'client'),
                                        ('projectName', 'project_name'),
                                        ('subProjectName', 'subproject_name')]:
            column[column_name] = request.form[form_value]
        error_occurred_while_updating = project_updated.update(project, column)
        if not error_occurred_while_updating:
            flash("Update was successful")
        else:
            flash(error_occurred_while_updating)
            render_template('project_update.html', form=form, project=project)

        return redirect(url_for('project_display', project_id=id))

    return render_template('project_update.html', form=form, project=project)

@app.route('/project/<int:id>/addUser', methods=['POST'])
@login_required
def project_add_user(id):
    data_json = request.get_json()
    if data_json:
        if data_json['uid']:
            user = User.query.filter_by(uid=data_json['uid']).first()
            project = Project.query.filter_by(id=id).first()
            no_error_while_adding_user = project.add_user(user)
            if no_error_while_adding_user:
                user_data = dict()
                for item in ('firstname', 'lastname', 'mail', 'id', 'function', 'service'):
                    user_data[item] = getattr(user, item)
                return json.dumps(user_data)


@app.route('/project/<int:project_id>/removeUser/<int:user_id>', methods=['POST'])
@login_required
def project_remove_user(project_id, user_id):
    project = Project.query.filter_by(id=project_id).first()
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({'is_removed': False})
    if project is None:
        return json.dumps({'is_removed': False})
    is_user_removed = project.delete_user(user)
    if is_user_removed is False:
        return json.dumps({'is_removed': False})
    return json.dumps({'is_removed': True})

@app.route('/project/<int:project_id>/users', methods=['GET'])
@login_required
def project_get_users(project_id):
    users = User.query.join(project_users, (project_users.c.user_id == User.id)).filter(project_users.c.project_id == project_id)
    _users = list()
    for user in users:
        _users.append(user.id)
    users = User.query.filter(~User.id.in_(_users))
    list_of_users = list()
    for user in users:
        list_of_users.append('{} {} ({})'.format(user.firstname, user.lastname, user.uid))
    return json.dumps(list_of_users)



@app.route('/project/privacy', methods=['POST'])
@login_required
def project_privacy():
    data_json = request.get_json()
    if data_json:
        if data_json['id']:
            project = Project.query.get(data_json['id'])
            if project.public is True:
                project.public = False
                session_commit()
                return json.dumps({'status': 'OK', 'public': 'False'})
            else:
                project.public = True
                session_commit()
                return json.dumps({'status': 'OK', 'public': 'True'})

@app.route('/project/delete/version/<int:id>')
@login_required
def project_delete_version(id):
    project_versioning = ProjectVersioning.query.get(id)
    if project_versioning == None:
        flash('This entry does not exist in the database', 'error')
        return redirect(url_for('project_display_all'))

    if g.user not in project_versioning.project.all_users():
        flash('You are not allowed to do this operation', 'error')
        return redirect(url_for('project_display_all'))

    error_when_deleting_project_version = project_versioning.delete()
    if not error_when_deleting_project_version:
        flash('The version {} of the project was deleted successfully'.format(project_versioning.version), 'success')
    else:
        flash(error_when_deleting_project_version, 'error')

    return redirect(url_for('project_display', project_id=project_versioning.projectId))


@app.route('/project/delete/<int:id>')
@login_required
def project_delete(id):
    project = Project.query.get(id)
    if project == None:
        flash('The project does not exist in the database', 'error')
        return redirect(url_for('project_display_all'))

    if g.user != project.user:
        flash('You are not allowed to do this operation', 'error')
        return redirect(url_for('project_display_all'))

    error_while_deleting_project = project.delete()
    if not error_while_deleting_project:
        flash('The project was successfully deleted', 'success')
    else:
        flash(error_while_deleting_project, 'error')

    return redirect(url_for('project_display_all'))


@app.route('/user', methods=['GET'])
@login_required
def user_display_all():
    user = User.query.all()
    return render_template('user_display_all.html', user=user)


@app.route('/user/display/<int:user_id>', methods=['GET'])
@login_required
def user_display(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('The user does not exist in the database', 'error')
        return redirect(url_for('user_display_all'))
    return render_template('user_display.html', user=user)


@app.route('/user/update/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_update(user_id):
    modify_user_form = ModifyUserForm(request.form, prefix="modify_user_form")
    user = User.query.get(user_id)
    if user is None:
        flash('The user does not exist in the database', 'error')
        return redirect(url_for('user_display_all'))

    if g.user.is_admin() is False:
        if g.user != user:
            flash('You are not allowed to do this operation', 'error')
            return redirect(url_for('user_display_all'))

    if request.method == 'POST' and modify_user_form.validate():
        data = {'firstname': request.form['modify_user_form-firstname'],
                'lastname': request.form['modify_user_form-lastname'],
                'mail': request.form['modify_user_form-email'],
                'uid': request.form['modify_user_form-uid'],
                'function': request.form['modify_user_form-function'],
                'service': request.form['modify_user_form-service'],
                'admin': request.form['admin']}
        error_while_updating_user = user.update(data)
        if not error_while_updating_user:
            flash('Update was successful', 'success')
            return redirect(url_for('user_display', user_id=user_id))
        else:
            flash(error_while_updating_user, 'error')
    return render_template('user_update.html', user=user, modify_user_form=modify_user_form, modify_password_form=ModifyPasswordForm(), alert='None', message='')


@app.route('/user/update/password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_update_password(user_id):
    modify_password_form = ModifyPasswordForm(request.form)
    user = User.query.get(user_id)
    if user is None:
        flash('The user does not exist in the database', 'error')
        return redirect(url_for('user_display_all'))

    if g.user.is_admin() is False:
        if g.user != user:
            flash('You are not allowed to do this operation', 'error')
            return redirect(url_for('user_display_all'))

    if request.method == 'POST' and modify_password_form.validate():
        error_while_setting_new_password = user.update_password(request.form['password'])
        if not error_while_setting_new_password:
            flash('Update was successful', 'success')
            return redirect(url_for('user_display', user_id=user_id))
        else:
            flash(error_while_setting_new_password, 'error')
    return render_template('user_update.html', user=user, modify_user_form=ModifyUserForm(), modify_password_form=modify_password_form, alert='None', message='')


@app.route('/user/delete/<int:user_id>')
@login_required
def user_delete(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('The user does not exist in the database', 'error')
        return redirect(url_for('user_display_all'))

    if g.user.is_admin() is False:
        if g.user != user:
            flash('You are not allowed to do this operation', 'error')
            return redirect(url_for('user_display_all'))

    error_while_deleting_user = user.delete()
    if not error_while_deleting_user:
        flash('The user was successfully deleted', 'success')
        return redirect(url_for('user_display_all'))
    else:
        flash('An error occured while deleting the user', 'error')
        return redirect(url_for('user_display', user_id=user_id))




@app.route('/file/<filename>')
@login_required
def return_file(filename):
    folder = session['project_folder']
    file = get_file(folder, filename + '.txt')
    return Response(file, mimetype="text/plain")


@app.route('/file/<id>/<version>/<filename>')
@login_required
def return_file_by_id_and_version(id, version, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(version))
    file = get_file(folder, filename + '.txt')
    return Response(file, mimetype="text/plain")

def get_file(folder, filename):
    try:
        file = os.path.join(folder, filename)
        return open(file).read()
    except IOError as exc:
        return str(exc)


@app.route('/download/<id>/<version>/<filename>')
@login_required
def send_file_by_id_and_filename(id, version, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(version))
    return send_from_directory(folder, filename, as_attachment=True)


@app.route('/download/<id>/<version>/zipFile')
@login_required
def send_zip_file_by_id_equal_to(id, version):
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(version))
    for _file in os.listdir(project_folder):
        if fnmatch(_file, '*.zip'):
            return send_from_directory(project_folder, _file, as_attachment=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
