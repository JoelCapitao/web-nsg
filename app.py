import os
from flask import render_template, request, flash, redirect, url_for, Response, session, send_file, send_from_directory
from model import *
from netscriptgen import NetScriptGen, Integer
from werkzeug import secure_filename
from shutil import move
from validationForm import ProjectForm, NewProjectVersionForm, ProjectUpdateForm, RegisterForm, LoginForm
from zip_list_of_files_in_memory import zip_file
from fnmatch import fnmatch
from flask.ext.login import LoginManager, login_user
import pickle
SESSION_TYPE = 'redis'
SECRET_KEY = 'develop'

# Initializing Flask-Login configuring it
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# This callback is used to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


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
                        request.form['uid'])

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
                # Creating a session on user's browser
                login_user(user_exists)
                flash('You have been logged in', 'success')
                return redirect(url_for('project_display_all'))
            else:
                flash('Your email or password does not match', 'danger')

    return render_template('login.html', form=form)


@app.route('/project/new', methods=['GET','POST'])
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
def project_add():
    if request.method == 'POST':
        project_data = session.get('project_data')
        versioning_data = session.get('versioning_data')

        project = Project(project_data['client'],
                          project_data['project_name'],
                          project_data['subproject_name'])
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
                                               project)
        project_versioning = project_versioning.add(project_versioning)

        if not post_add and not project_versioning:
            new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project.id), 'v1')
            move(session['project_folder'], new_project_folder)

            try:
                zip_file(new_project_folder, os.path.join(new_project_folder, zf_name))
            except:
                pass

            return redirect(url_for('project_display', id=last_id_of_the_table_project()))
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
def project_display_all():
    projects = Project.query.all()
    for _project in projects:
        _all_version_of_the_project = _project.version.all()
        if _all_version_of_the_project:
            last_version = _all_version_of_the_project[-1]
            for item in ('excelFile', 'templateFile'):
                setattr(_project, item, getattr(last_version, item))
            # Because SQLAlchemy do not let us to set an attribute named 'version'
            setattr(_project, 'lastVersion', str(getattr(last_version, 'version')))

    return render_template('project_display_all.html', project=projects)

@app.route('/project/display/<id>', methods=['GET','POST'])
def project_display(id):
    project = Project.query.get(id)
    if project:
        all_version_of_the_project = project.version.all()
        last_version_of_the_project = all_version_of_the_project[-1]
        for item in ('excelFile', 'templateFile', 'numberOfVarToFill', 'numberOfVarFilled', 'fillingRatio', 'zipFile'):
            setattr(project, item, getattr(last_version_of_the_project, item))
        # The attribute 'version' is not in the loop because the object does not accept an attr with that name
        # So I replace 'version' by 'current_version'
        setattr(project, 'currentVersion', getattr(last_version_of_the_project, 'version'))

        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(last_version_of_the_project.version))
        with open(os.path.join(project_folder, 'data.pickle'), 'rb') as f:
            equipments = pickle.load(f)

        form = ProjectForm(request.form)
        return render_template('project_display.html', project=project, versions=all_version_of_the_project[:-1],
                               form=form, alert='None', message='', equipments=equipments, iterator=Integer(1))
    else:
        flash("The project does not exist in the database")
        return redirect(url_for('project_display_all'))


@app.route('/project/<id>/new', methods=['GET','POST'])
def project_new_version(id):
    project = Project.query.get(id)
    all_version_of_the_project = project.version.all()
    last_version = all_version_of_the_project[-1].version
    new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(last_version + 1))
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


@app.route('/project/<id>/upgrade', methods=['GET','POST'])
def project_upgrade(id):
    if request.method == 'POST':
        versioning_data = session.get('versioning_data')
        project = Project.query.get(id)
        last_version_of_the_project = last_version_of_the_project_id_equal_to(id)

        new_version = ProjectVersioning(last_version_of_the_project.version + 1,
                                        versioning_data['excel_file'],
                                        versioning_data['template_file'],
                                        versioning_data['to_fill'],
                                        versioning_data['filled'],
                                        versioning_data['fillingRatio'],
                                        project)
        error_in_creation_of_new_version = new_version.add(new_version)

        if not error_in_creation_of_new_version:
            if project.subProjectName:
                zf_name = "scripts-{0}-{1}-{2}-v{3}.zip".format(project.client,
                                                                project.projectName,
                                                                project.subProjectName,
                                                                last_version_of_the_project.version + 1)
            else:
                zf_name = "scripts-{0}-{1}-v{2}.zip".format(project.client,
                                                            project.projectName,
                                                            last_version_of_the_project.version + 1)

            try:
                zip_file(versioning_data['project_folder'], os.path.join(versioning_data['project_folder'], zf_name))
            except:
                pass

            return redirect(url_for('project_display', id=id))
        else:
            flash(error_in_creation_of_new_version)
    return redirect(url_for('project_display_all'))


@app.route('/project/<id>/update', methods=['GET','POST'])
def project_update(id):
    form = ProjectUpdateForm(request.form)
    project = Project.query.get(id)
    if project == None:
        flash("The project does not exist in the database")
        return render_template('project_update.html', form=form)

    if request.method == 'POST' and form.validate():
        project_updated = Project(request.form['client'],
                                  request.form['project_name'],
                                  request.form['subproject_name'])

        column = dict()
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

        return redirect(url_for('project_display', id=id))

    return render_template('project_update.html', form=form, project=project)


@app.route('/project/delete/version/<id>')
def project_delete_version(id):
    project_versioning = ProjectVersioning.query.get(id)

    if project_versioning == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('user_display_all'))

    error_when_deleting_project_version = project_versioning.delete(project_versioning)
    if not error_when_deleting_project_version:
        flash("Project version was deleted successfully")
    else:
        flash(error_when_deleting_project_version)

    return redirect(url_for('project_display', id=project_versioning.projectId))


@app.route('/project/delete/<id>')
def project_delete(id):
    project = Project.query.get(id)
    all_versions_of_the_project = project.version.all()
    if project == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('user_display_all'))

    project_not_deleted = project.delete(project)
    if not project_not_deleted:
        flash("Project was deleted successfully")
    else:
        error = project_not_deleted
        flash(error)

    for _version in all_versions_of_the_project:
        version_not_deleted = _version.delete(_version)
        if not version_not_deleted:
            flash("Project version was deleted successfully")
        else:
            error = project_not_deleted
            flash(error)

    return redirect(url_for('project_display_all'))


@app.route('/user')
def user_display_all():
    user = User.query.all()
    return render_template('user_display_all.html', user=user)


@app.route('/user/display/<id>', methods=['GET','POST'])
def user_display(id):
    user = User.query.get(id)
    if user is None:
        flash("The user does not exist in the database")
        return redirect(url_for('user_display_all'))
    return render_template('user_display.html', user=user, alert='None', message='')


@app.route('/user/update/<id>', methods=['GET','POST'])
def user_update(id):
    user = User.query.get(id)
    if user == None:
        flash("The user does not exist in the database")
        return redirect(url_for('user_display_all'))
    if request.method == 'POST':
        user = User(request.form['firstname'],
                    request.form['lastname'],
                    request.form['email'],
                    request.form['password'],
                    request.form['quadri'],
                  )
        user_update = user.update(user)
        if not user_update:
            flash("Update was successful")
            return redirect(url_for('user_display', id=id))
        else:
            error=user_update
            flash(error)
    return render_template('user_update.html', user=user, alert='None', message='')



@app.route('/user/delete/<id>')
def user_delete(id):
    user = User.query.get(id)
    if user == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('user_display_all'))
    post_delete = user.delete(user)
    if not post_delete:
        flash("User was deleted successfully")
    else:
        error = post_delete
        flash(error)
    return redirect(url_for('user_display_all'))


@app.route('/user/add', methods=['GET','POST'])
def user_add():
    if request.method == 'POST':
        user = User(request.form['firstname'],
                    request.form['lastname'],
                    request.form['email'],
                    request.form['password'],
                    request.form['quadri'],
                  )
        post_add = user.add(user)
        if not post_add:
            flash("Add was successful")
            return redirect(url_for('user_display_all'))
        else:
            error = post_add
            flash(error)
    return render_template('new_user.html')


@app.route('/customer')
def customer_display_all():
    customer = Customer.query.all()
    return render_template('customer_display_all.html', customer=customer)

@app.route('/customer/add', methods=['GET','POST'])
def customer_add():
    if request.method == 'POST':
        customer = Customer(request.form['firstname'],
                            request.form['lastname'],
                            request.form['mail'],
                            request.form['company'],
                            request.form['landline'],
                            request.form['function']
                            )
        post_add = customer.add(customer)
        if not post_add:
            flash("Add was successful")
            return redirect(url_for('customer_display_all'))
        else:
            error = post_add
            flash(error)
    return render_template('customer_user.html')


@app.route('/customer/update/<id>', methods=['GET','POST'])
def customer_update(id):
    customer = Customer.query.get(id)
    if customer == None:
        flash("The user does not exist in the database")
        return redirect(url_for('customer_display_all'))
    if request.method == 'POST':
        customer = Customer(request.form['firstname'],
                            request.form['lastname'],
                            request.form['mail'],
                            request.form['company'],
                            request.form['landline'],
                            request.form['function']
                            )
        customer_update = customer.update(customer)
        if not customer_update:
            flash("Update was successful")
            return redirect(url_for('customer_display', id=id))
        else:
            error = user_update
            flash(error)
    return render_template('customer_update.html', customer=customer, alert='None', message='')

@app.route('/customer/delete/<id>')
def customer_delete(id):
    customer = Customer.query.get(id)
    if customer == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('customer_display_all'))
    post_delete = customer.delete(customer)
    if not post_delete:
        flash("Customer was deleted successfully")
    else:
        error = post_delete
        flash(error)
    return redirect(url_for('customer_display_all'))

@app.route('/customer/display/<id>', methods=['GET','POST'])
def customer_display(id):
    customer = Customer.query.get(id)
    if customer is None:
        flash("The user does not exist in the database")
        return redirect(url_for('customer_display_all'))
    return render_template('customer_display.html', customer=customer, alert='None', message='')

@app.route('/file/<filename>')
def return_file(filename):
    folder = session['project_folder']
    file = get_file(folder, filename + '.txt')
    return Response(file, mimetype="text/plain")

@app.route('/file/<id>/<version>/<filename>')
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
def send_file_by_id_and_filename(id, version, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(version))
    return send_from_directory(folder, filename, as_attachment=True)


@app.route('/download/<id>/<version>/zipFile')
def send_zip_file_by_id_equal_to(id, version):
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id, 'v{0}'.format(version))
    for _file in os.listdir(project_folder):
        if fnmatch(_file, '*.zip'):
            return send_from_directory(project_folder, _file, as_attachment=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
